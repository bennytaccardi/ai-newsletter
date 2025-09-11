from typing import List

from pydantic import BaseModel
from pypdf import PdfReader
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
PAPER_DIR = root_dir.joinpath('src/papers')

class PdfLoader(BaseModel):
    paper_name: str
    extracted_text: str

def load_paper(paper) -> str:
    pdf_reader = PdfReader(PAPER_DIR.joinpath(paper))
    text = ""
    for page in pdf_reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text
    return text

def load_papers() -> List[PdfLoader]:
    papers = os.listdir(PAPER_DIR)
    pdfs: List[PdfLoader] = []
    for paper in papers:
        pdf = PdfLoader(paper_name=paper, extracted_text=load_paper(paper))
        pdfs.append(pdf)
    return pdfs

def split_text(txt: str, chunk_size=500, overlap=50) -> List[str]:
    chunks: List[str] = []
    start: int = 0
    end: int = 0

    while end < len(txt):
        end = start + chunk_size
        if end > len(txt):
            end = len(txt)
        chunks.append(txt[start:end])
        start = end - overlap

    return chunks