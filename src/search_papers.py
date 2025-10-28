import json
import re
import time
import logging
from time import sleep
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from utils import search_prompt_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchedPaper(BaseModel):
    url: str = Field(description="The URL of the paper. It must be the link to the pdf, not to the abstract")
    title: str = Field(description="The title of the paper")
    publication_date: str = Field(description="The publication date of the paper")
    citation_number: int = Field(description="The citation number of the paper")

class PapersList(BaseModel):
    papers: list[SearchedPaper]

class EnhancedPaperSearch:
    def __init__(self, perplexity_client):
        self.client = perplexity_client

    def _build_search_prompt(self, topic: str, pub_from: str, pub_to: str, seen_urls: list[str]) -> str:
        """Build the search prompt with dynamic parameters"""
        period_range = f"{pub_from} to {pub_to}"

        return search_prompt_template.format(
            topic=topic,
            pub_from=pub_from,
            pub_to=pub_to,
            url_list=",".join(seen_urls),
        )

    def _calculate_composite_score(self, paper: dict) -> float:
        """Calculate a composite score based on multiple factors"""
        score = 0.0

        # Citation impact (40%)
        citations = paper.get('citations', 0) or 0
        citation_score = min(citations / 100, 1.0)  # Normalize to 0-1
        score += citation_score * 0.4

        # Social proof (30%)
        social_mentions = paper.get('social_mentions', 0) or 0
        github_stars = paper.get('github_stars', 0) or 0
        social_score = min((social_mentions + github_stars / 100) / 50, 1.0)
        score += social_score * 0.3

        # Authority (20%)
        author_hindex = paper.get('author_hindex', 0) or 0
        authority_score = min(author_hindex / 50, 1.0)
        score += authority_score * 0.2

        # Recency (10%)
        pub_date = paper.get('publication_date', '')
        if pub_date:
            try:
                pub_year = int(pub_date[:4])
                current_year = datetime.now().year
                recency_score = max(0, 1 - (current_year - pub_year) / 10)
                score += recency_score * 0.1
            except:
                score += 0.05  # Default recency score

        return round(score, 3)

    def _enhance_paper_data(self, paper: SearchedPaper) -> SearchedPaper:
        """Enhance paper data with additional metrics"""
        # Add composite score
        paper_dict = paper.model_dump()
        paper_dict['composite_score'] = self._calculate_composite_score(paper_dict)

        # Ensure PDF URL
        if hasattr(paper, 'url') and 'abs' in paper.url:
            paper.url = paper.url.replace('abs', 'pdf')

        return SearchedPaper.model_validate(paper_dict)

    def _validate_and_convert_arxiv_url(self, url: str) -> str:
        """
        Validate URL is arXiv and convert to proper PDF format
        Handles arXiv's URL redirection patterns
        """
        if not url:
            raise ValueError("Empty URL provided")

        # Check if it's an arXiv URL
        if 'arxiv.org' not in url:
            raise ValueError(f"Non-arXiv domain: {url}")

        # Extract arXiv ID with more flexible patterns
        arxiv_patterns = [
            r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+(?:v\d+)?)',
            r'arxiv\.org/(?:abs|pdf)/([a-z-]+/\d+\.\d+(?:v\d+)?)',
            r'/(\d+\.\d+(?:v\d+)?)(?:\.pdf)?$',
            r'/([a-z-]+/\d+\.\d+(?:v\d+)?)(?:\.pdf)?$'
        ]

        arxiv_id = None
        for pattern in arxiv_patterns:
            match = re.search(pattern, url)
            if match:
                arxiv_id = match.group(1)
                break

        if not arxiv_id:
            raise ValueError(f"Could not extract arXiv ID from: {url}")

        # Construct PROPER arXiv PDF URL (without .pdf extension)
        # arXiv prefers: https://arxiv.org/pdf/2507.13334v2
        # Not: https://arxiv.org/pdf/2507.13334v2.pdf
        proper_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        return proper_pdf_url

    def search_papers(
            self,
            topic: str,
            pub_from: str,
            pub_to: str,
            max_results: int = 15,
            domains: Optional[List[str]] = None
    ) -> List[SearchedPaper]:
        """
        Enhanced paper search with sophisticated ranking and error handling

        Args:
            topic: Research topic to search for
            pub_from: Start date (YYYY-MM-DD)
            pub_to: End date (YYYY-MM-DD)
            max_results: Maximum number of papers to return
            domains: List of domains to search (default: arxiv.org)
        """
        final_papers: List[SearchedPaper] = []
        exhausted_cycles = 5
        seen_urls = set()
        while len(final_papers) < max_results and exhausted_cycles>0:
            if domains is None:
                domains = ["arxiv.org", "scholar.google.com", "semanticscholar.org"]

            try:
                search_prompt = self._build_search_prompt(topic, pub_from, pub_to, list(seen_urls))

                logger.info(f"Searching for papers on '{topic}' from {pub_from} to {pub_to}")

                completion = self.client.chat.completions.create(
                    model="sonar",
                    messages=[
                        {
                            "role": "system",
                            "content": search_prompt
                        },
                        {
                            "role": "user",
                            "content": f"Topic: **{topic}**. Publication Period: **{pub_from} to {pub_to}**. Return maximum {max_results} papers ranked by impact. You MUST search ONLY pdf papers, not abstract not html pages. Only pdf papers"
                        }
                    ],
                    search_domain_filter=domains,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "papers_list",
                            "schema": PapersList.model_json_schema(),
                            "strict": True
                        }
                    },
                    temperature=0.3  # Lower temperature for more consistent results
                )

                if not completion.choices:
                    raise ValueError("No response from search API")

                raw_response = completion.choices[0].message.content

                if not raw_response:
                    raise ValueError("Empty response content")

                # Parse and validate response
                response_dict = json.loads(raw_response)

                if 'papers' not in response_dict:
                    raise ValueError("Invalid response format: missing 'papers' key")

                # Validate and enhance each paper
                validated_papers = []
                for paper_data in response_dict['papers']:
                    try:
                        # Validate and convert URL to arXiv PDF
                        original_url = paper_data.get('url', '')
                        paper_data['url'] = self._validate_and_convert_arxiv_url(original_url)

                        paper = SearchedPaper.model_validate(paper_data)
                        validated_papers.append(paper)
                        sleep(0.5)

                    except ValueError as e:
                        logger.warning(f"Excluding invalid paper URL: {e}")
                        continue

                # Sort by composite score (descending)
                validated_papers.sort(key=lambda x: x.composite_score if hasattr(x, 'composite_score') else 0, reverse=True)

                # Limit results

                for paper in validated_papers:
                    if paper.url not in seen_urls:
                        seen_urls.add(paper.url)
                        final_papers.append(paper)

                logger.info(f"Successfully retrieved {len(final_papers)} papers")
                exhausted_cycles -= 1
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                raise ValueError(f"Failed to parse search response: {e}")
            except Exception as e:
                logger.error(f"Search failed: {e}")
                raise
        return final_papers

