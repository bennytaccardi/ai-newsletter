from time import sleep

from clients import gemini_client
from search_papers import EnhancedPaperSearch
from src.clients import perplexity_client

from summarize_papers import PaperSummarizer


if '__main__' == __name__:
    search_engine = EnhancedPaperSearch(perplexity_client)
    papers = search_engine.search_papers(topic='Large Language Models', pub_from="2025-10-21", pub_to="2025-10-28", max_results=1)
    sleep(3)
    level = "newbie"
    language = "it"
    summarizer = PaperSummarizer(gemini_client)
    summaries = summarizer.summarize_papers(papers=papers, level=level, language=language, parallel=True)