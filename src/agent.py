from src.collections.papers import PaperCollection, Paper
from pdf_loader import load_papers, split_text


if '__main__' == __name__:

    paper_collection = PaperCollection()

    pdfs = load_papers()
    for pdf in pdfs:
        paper_collection.add([
        Paper(
            text=pdf.extracted_text,
            id=pdf.paper_name
            ),
        ])
        
    results = paper_collection.query(
        query_texts=["WHat is the auto-prompt technique"],
        n_results=10
    )
    
    print(results.get("ids", None))