from src.collections.papers import PaperCollection, Paper
from pdf_loader import load_papers, split_text


if '__main__' == __name__:

    paper_collection = PaperCollection()
    paper_collection.add([
        Paper(
            text="Artificial intelligence is transforming industries across the globe.",
            id="title-1"
            ),
        Paper(
            text="Vector databases enable efficient semantic search capabilities.",
            id="title-2"
            ),
        ])
    # results = paper_collection.query(
    #     query_texts=["How is AI changing businesses?"],
    #     n_results=1
    # )

    pdfs = load_papers()
    for pdf in pdfs:
        paper_collection.add([
        Paper(
            text=pdf.extracted_text,
            id=pdf.paper_name
            ),
        ])
        
    results = paper_collection.query(
        query_texts=["In a self-attention layer all of the keys"],
        n_results=10
    )
    
    print(results)