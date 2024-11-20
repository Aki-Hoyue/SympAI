from typing import List, Dict, Any, Optional
from app.core.rag.store import VectorStore
from app.core.rag.embedding import EmbeddingService
from app.core.rag.reranking import Reranker, RerankResult

class VectorRetriever:
    def __init__(self,
                 embedding_service: EmbeddingService,
                 vector_store: VectorStore,
                 reranker: Reranker):
        """
        Initialize retriever
        
        Args:
            embedding_service: Embedding service instance
            vector_store: Vector store instance
            reranker: Reranker instance
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranker = reranker
        
        if not self.reranker:
            raise ValueError("Reranker is required for VectorRetriever")
    
    def search(self, 
               query: str, 
               limit: int = 10,
               top_k: Optional[int] = 5,
               output_fields: Optional[List[str]] = None) -> List[RerankResult]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            limit: Initial vector search quantity
            top_k: Number of results after reranking
            output_fields: List of fields to return
            
        Returns:
            List[RerankResult]: Search results list
        """
        try:
            # 1. Vector search
            collection = self.vector_store.get_collection()
            collection.load()
            
            query_vector = self.embedding_service.embed_query(query)
            output_fields = output_fields or ["id", "content", "source", "type"]
            
            results = collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "L2", "params": {"nprobe": 16}},
                limit=limit,
                output_fields=output_fields
            )
            
            # 2. Format search results
            search_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        "score": hit.score,
                        "id": hit.entity.get("id"),
                        "content": hit.entity.get("content"),
                        "source": hit.entity.get("source"),
                        "type": hit.entity.get("type")
                    }
                    search_results.append(result)
            
            # 3. Reranking
            reranked_results = self.reranker.rerank(
                query=query,
                search_results=search_results,
                top_k=top_k
            )
            
            return reranked_results
            
        except Exception as e:
            raise ValueError(f"Search failed: {e}")
        finally:
            collection.release() 
