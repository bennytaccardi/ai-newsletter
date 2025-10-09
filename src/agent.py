from idlelib.rpc import response_queue

from pydantic import BaseModel, Field

from clients import openai_client, gemini_client
from pdf_loader import load_paper, PdfLoader, PAPER_DIR
from src.clients import perplexity_client
import requests
import os
import json
import httpx
from google.genai import types
import smtplib

class SearchedPaper(BaseModel):
    url: str = Field(description="The URL of the paper. It must be the link to the pdf, not to the abstract")
    title: str = Field(description="The title of the paper")
    publication_date: str = Field(description="The publication date of the paper")

class PapersList(BaseModel):
    papers: list[SearchedPaper]

def download_papers() -> list[SearchedPaper]:
    completion = perplexity_client.chat.completions.create(
        model="sonar",
        messages=[
            {"role": "system", "content": "You are a super performant web scraper"},
            {"role": "user",
             "content": "Link of PDF file top AI papers which talk about LLM technology of September 2025"}
        ],
        search_domain_filter=[
            "arxiv.org",
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "papers_list",
                "schema": PapersList.model_json_schema(),
                "strict": True
            }
        }
    )

    raw_response = completion.choices[0].message.content
    response_dict: list[SearchedPaper] = json.loads(raw_response)
    papers: list[SearchedPaper] = [
        SearchedPaper.model_validate(paper)
        for paper in response_dict['papers']
    ]
    return papers


def summarize_papers(papers: list) -> list[dict]:
    summaries = []

    for paper in papers:
        try:
            doc_data = httpx.get(paper.url, timeout=30).content
            prompt = """Analyze this scientific paper and provide a comprehensive summary with the following sections:
                        1. **Title and Authors**: Extract the paper title and author information
                        2. **Research Objective**: What problem does this paper address?
                        3. **Methodology**: 
                           - Research approach and design
                           - Dataset/materials used
                           - Key parameters and settings
                        4. **Key Findings**: 
                           - Main results and discoveries
                           - Quantitative results (percentages, metrics, etc.)
                           - Comparative analysis if applicable
                        5. **Visual Content Summary**:
                           - Describe all figures, tables, and charts
                           - Explain what each visualization shows
                           - Note any important trends or patterns visible in images
                        6. **Limitations**: What are the stated or apparent limitations?
                        7. **Implications and Applications**: 
                           - Practical applications
                           - Future research directions
                           - Impact on the field
                        8. **Significance**: Rate the contribution (High/Medium/Low) and justify briefly
                        
                        Format your response as structured JSON with these keys: title, authors, objective, methodology, findings, visual_content, limitations, implications, significance."""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=doc_data,
                        mime_type='application/pdf',
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                )
            )

            summary_text = response.text

            try:
                summary_data = json.loads(summary_text)
            except json.JSONDecodeError:
                summary_data = {
                    "title": paper.title if hasattr(paper, 'title') else "Unknown",
                    "raw_summary": summary_text,
                    "status": "text_format"
                }

            summary_data["paper_url"] = paper.url
            summary_data["status"] = "success"

            summaries.append(summary_data)
            print(f"✓ Summarized: {summary_data.get('title', 'Unknown')}")

        except httpx.HTTPError as e:
            print(f"✗ Failed to fetch {paper.url}: {e}")
            summaries.append({
                "paper_url": paper.url,
                "status": "fetch_error",
                "error": str(e)
            })
        except Exception as e:
            print(f"✗ Failed to summarize {paper.url}: {e}")
            summaries.append({
                "paper_url": paper.url,
                "status": "error",
                "error": str(e)
            })

    return summaries


def format_summary_markdown(summary: dict) -> str:

    if summary.get("status") != "success":
        return f"Failed to summarize: {summary.get('error', 'Unknown error')}"

    md = f"# {summary.get('title', 'Unknown Title')}\n\n"

    if authors := summary.get('authors'):
        md += f"**Authors:** {authors}\n\n"

    sections = ['objective', 'methodology', 'findings', 'visual_content',
                'limitations', 'implications', 'significance']

    for section in sections:
        if content := summary.get(section):
            title = section.replace('_', ' ').title()
            md += f"## {title}\n{content}\n\n"

    return md

if '__main__' == __name__:
    papers = download_papers()
    summaries = summarize_papers(papers[:1])