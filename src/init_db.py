from src.chroma_collections.papers import PaperCollection, Paper
from pdf_loader import load_papers

def load_db(delete_collection = False):
    if delete_collection:
        PaperCollection.delete_collection()
    paper_collection = PaperCollection()

    pdfs = load_papers()

    for pdf in pdfs:
        paper_collection.add([
            Paper(
                text=pdf.extracted_text,
                id=pdf.paper_name
            ),
        ])
if '__main__' == __name__:

    load_db()
    
