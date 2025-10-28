import asyncio
import re

import httpx
import json
import time
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from google.genai import types

from utils import summarize_prompt_template, summarize_newsletter_prompt_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    paper_url: str
    title: str
    html_summary: str
    status: str
    processing_time: float
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class PaperSummarizer:
    def __init__(self, gemini_client, output_dir: str = "./summaries", max_workers: int = 3):
        self.client = gemini_client
        self.max_workers = max_workers
        self.output_dir = Path(output_dir)
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.output_dir.mkdir(exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be filesystem-safe"""
        # Remove invalid characters and replace spaces with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Limit length to avoid filesystem issues
        if len(sanitized) > 150:
            sanitized = sanitized[:150]
        return sanitized

    def _generate_output_filename(self, paper_title: str, language: str, level: str) -> str:
        """Generate a safe filename for the HTML summary"""
        safe_title = self._sanitize_filename(paper_title)
        safe_language = self._sanitize_filename(language)
        safe_level = self._sanitize_filename(level)

        filename = f"{safe_title}-{safe_language}-{safe_level}.html"
        return filename

    def _save_html_summary(self, html_content: str, paper_title: str, language: str, level: str) -> str:
        """Save HTML summary to file and return the file path"""
        try:
            filename = self._generate_output_filename(paper_title, language, level)
            file_path = self.output_dir / filename

            # Write HTML content with proper encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"✓ Saved HTML summary: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save HTML summary for {paper_title}: {e}")
            return ""

    def _build_enhanced_prompt(self, level: str, language: str) -> str:
        """Build the enhanced summarization prompt"""
        return summarize_prompt_template.format(level=level, language=language)

    def _build_enhanced_prompt_newsletter(self, summary: str) -> str:
        """Build the enhanced summarization prompt"""
        return summarize_newsletter_prompt_template.format(summary=summary)

    def _validate_html_response(self, text: str) -> Dict:
        """Validate and parse the model response"""
        # Clean the response
        cleaned_text = text.strip()

        # Basic HTML validation
        if not cleaned_text.startswith('<'):
            # Wrap in basic HTML structure if missing
            cleaned_text = f"<div class=\"paper-summary\">{cleaned_text}</div>"

        try:
            # Try to parse as JSON first (in case model misformats)
            json_data = json.loads(cleaned_text)
            return {
                "html_summary": json_data.get('summary', cleaned_text),
                "metadata": json_data
            }
        except json.JSONDecodeError:
            # It's HTML as expected
            return {
                "html_summary": cleaned_text,
                "metadata": {"format": "html"}
            }

    def _summarize_single_paper(self, paper, level: str, language: str) -> SummaryResult:
        """Summarize a single paper with comprehensive error handling"""
        start_time = time.time()
        paper_title = getattr(paper, 'title', 'Unknown_Title')

        try:
            # Fetch PDF content
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(paper.url)
                response.raise_for_status()
                doc_data = response.content

            # Generate summary
            prompt = self._build_enhanced_prompt(level, language)

            api_response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=doc_data,
                        mime_type='application/pdf',
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Lower temp for more consistent results
                    top_p=0.8,
                )
            )

            # Validate and process response
            validation_result = self._validate_html_response(api_response.text)

            html_summary = validation_result["html_summary"]

            # Save HTML summary to file
            saved_path = self._save_html_summary(html_summary, paper_title, language, level)

            return SummaryResult(
                paper_url=paper.url,
                title=getattr(paper, 'title', 'Unknown'),
                html_summary=validation_result["html_summary"],
                status="success",
                processing_time=time.time() - start_time,
                metadata=validation_result["metadata"]
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {paper.url}: {e}")
            return SummaryResult(
                paper_url=paper.url,
                title=getattr(paper, 'title', 'Unknown'),
                html_summary="",
                status="fetch_error",
                processing_time=time.time() - start_time,
                error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Summarization failed for {paper.url}: {e}")
            return SummaryResult(
                paper_url=paper.url,
                title=getattr(paper, 'title', 'Unknown'),
                html_summary="",
                status="error",
                processing_time=time.time() - start_time,
                error=f"Processing error: {str(e)}"
            )

    def summarize_papers(
            self,
            papers: List,
            level: str,
            language: str = 'en',
            parallel: bool = True
    ) -> List[Dict]:
        """
        Enhanced paper summarization with parallel processing and caching

        Args:
            papers: List of paper objects with URL attribute
            level: Audience level (e.g., 'undergraduate', 'general', 'expert')
            language: Output language
            parallel: Whether to process papers in parallel
        """
        logger.info(f"Starting summarization of {len(papers)} papers for {level} audience")

        if parallel and len(papers) > 1:
            # Parallel processing for multiple papers
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._summarize_single_paper, paper, level, language)
                    for paper in papers
                ]
                results = [future.result() for future in futures]
        else:
            # Sequential processing
            results = []
            for paper in papers:
                result = self._summarize_single_paper(paper, level, language)
                results.append(result)
                # Small delay to avoid rate limiting
                time.sleep(0.5)

        # Convert to dictionary format for compatibility
        summary_dicts = []
        success_count = 0

        for result in results:
            summary_dict = {
                "paper_url": result.paper_url,
                "title": result.title,
                "html_summary": result.html_summary,
                "status": result.status,
                "processing_time": round(result.processing_time, 2),
                "language": language,
                "audience_level": level
            }

            if result.error:
                summary_dict["error"] = result.error

            if result.metadata:
                summary_dict["metadata"] = result.metadata

            summary_dicts.append(summary_dict)

            if "success" in result.status:
                success_count += 1
                logger.info(f"✓ Summarized: {result.title} ({result.processing_time:.1f}s)")
            else:
                logger.warning(f"✗ Failed: {result.title} - {result.error}")

        logger.info(f"Summarization complete: {success_count}/{len(papers)} successful")
        return summary_dicts