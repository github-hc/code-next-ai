import weaviate
import weaviate.classes.config as wvc
import weaviate.classes.query as wvq
from typing import List, Dict, Any

from backend.models.chunk import CodeChunk

class WeaviateVectorStore:
    """
    Manages storing and retrieving CodeChunks in a local Weaviate instance.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8080, grpc_port: int = 50051, collection_name: str = "CodingAgent"):
        """
        Initializes the Weaviate client.
        """
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.collection_name = collection_name
        self.client = weaviate.connect_to_local(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
        )
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collections.exists(self.collection_name):
            self.client.collections.create(
                name=self.collection_name,
                vectorizer_config=None,  # We manage embeddings ourselves
                properties=[
                    wvc.Property(name="chunk_id", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="file_path", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="symbol_name", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="chunk_type", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="start_line", data_type=wvc.DataType.INT),
                    wvc.Property(name="end_line", data_type=wvc.DataType.INT),
                    wvc.Property(name="code", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="docstring", data_type=wvc.DataType.TEXT),
                ]
            )

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def clear(self):
        """
        Deletes the entire collection from Weaviate and recreates an empty one.
        """
        try:
            if self.client.collections.exists(self.collection_name):
                self.client.collections.delete(self.collection_name)
        except Exception as e:
            print(f"Error deleting collection: {e}")
        self._ensure_collection()

    def add_chunks(self, chunks: List[CodeChunk]):
        """
        Adds a batch of CodeChunks to the Weaviate collection.
        Assumes that the chunks already have their embeddings populated.
        """
        if not chunks:
            return

        collection = self.client.collections.get(self.collection_name)
        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                if not chunk.embedding:
                    print(f"Warning: Chunk {chunk.chunk_id} has no embedding. Skipping.")
                    continue
                    
                properties = {
                    "chunk_id": chunk.chunk_id,
                    "file_path": chunk.file_path,
                    "symbol_name": chunk.symbol_name,
                    "chunk_type": chunk.chunk_type,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "code": chunk.code,
                    "docstring": chunk.docstring or "",
                }
                
                batch.add_object(
                    properties=properties,
                    vector=chunk.embedding
                )
                
        failed = collection.batch.failed_objects
        if failed:
            print(f"Warning: {len(failed)} errors occurred during batch import.")
            for failed_obj in failed:
                print(f"  Failed object: {failed_obj}")

    def hybrid_search(self, query: str, query_embedding: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs Weaviate's native hybrid search.
        
        Returns:
            A list of ranked result dictionaries in the structure expected by the orchestrator.
        """
        collection = self.client.collections.get(self.collection_name)
        response = collection.query.hybrid(
            query=query,
            vector=query_embedding,
            limit=n_results,
            return_metadata=wvq.MetadataQuery(score=True)
        )
        
        formatted_results = []
        for obj in response.objects:
            formatted_results.append({
                "chunk_id": obj.properties.get("chunk_id"),
                "file_path": obj.properties.get("file_path"),
                "symbol_name": obj.properties.get("symbol_name"),
                "start_line": int(obj.properties.get("start_line", 0)),
                "end_line": int(obj.properties.get("end_line", 0)),
                "score": obj.metadata.score if obj.metadata.score is not None else 0.0,
                "code": obj.properties.get("code", "")
            })
        return formatted_results
