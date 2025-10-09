from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
from clients import chroma_client
from chromadb.api import CreateCollectionConfiguration
from chromadb.api.collection_configuration import CreateHNSWConfiguration
from typing import Any, Optional
# collection.add(
#     documents=["Artificial intelligence is transforming industries across the globe.",
#                "Vector databases enable efficient semantic search capabilities."],
#     ids=["doc1", "doc2"]
# )

class Paper:
    text: str
    id: str
    metadata: Optional[dict[str, str]]
    
    def __init__(self, text: str, id: str, metadata: Optional[dict[str, str]] = None):
        self.text = text
        self.id = id
        self.metadata = metadata

class PaperCollection:
    
    COLLECTION_NAME = "papers"
    
    def __init__(self):
        ollama_ef = OllamaEmbeddingFunction(
            url="http://localhost:11434",
            model_name="nomic-embed-text",
        )
        self.collection = chroma_client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=ollama_ef,
            configuration= CreateCollectionConfiguration(hnsw=CreateHNSWConfiguration(space="cosine"))
        )

    def add(self, documents: list[Any]) -> None:
        self.collection.add(
            documents=[document.text for document in documents],
            ids=[document.id for document in documents],
            metadatas=[document.metadata for document in documents]
        )
    
    def query(self, query_texts: list[str], n_results: int) -> Any:
        return self.collection.query(query_texts=query_texts, n_results=n_results)
    
    def delete_document(self, ids: list[str]) -> Any:
        return self.collection.delete(ids=ids)
    
    @staticmethod
    def delete_collection() -> Any:
        return chroma_client.delete_collection("papers")
