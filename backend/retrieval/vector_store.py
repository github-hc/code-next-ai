import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

from backend.models.chunk import CodeChunk

class ChromaVectorStore:
    """
    Manages storing and retrieving CodeChunks in a local ChromaDB instance.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "coding_agent"):
        """
        Initializes the ChromaDB persistent client.
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: List[CodeChunk]):
        """
        Adds a batch of CodeChunks to the ChromaDB collection.
        Assumes that the chunks already have their embeddings populated.
        """
        if not chunks:
            return

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for chunk in chunks:
            if not chunk.embedding:
                print(f"Warning: Chunk {chunk.chunk_id} has no embedding. Skipping.")
                continue
                
            ids.append(chunk.chunk_id)
            embeddings.append(chunk.embedding)
            
            # Store metadata
            metadata = chunk.to_metadata()
            metadatas.append(metadata)
            
            # The document is the actual code
            documents.append(chunk.code)

        # Upsert prevents crashing on duplicates and updates existing chunks
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def similarity_search_by_vector(self, query_embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """
        Performs a semantic search using an embedding vector.
        
        Returns:
            ChromaDB query results dictionary containing ids, distances, metadatas, and documents.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results
