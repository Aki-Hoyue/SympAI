from typing import List, Dict, Any, Optional, Tuple
import os
import requests
import time
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

@dataclass
class RerankResult:
    """
    Reranking result data class
    """
    content: str
    score: float                  # Original retrieval score
    relevance_score: float        # Reranking score
    index: int                    # Index after reranking
    metadata: Dict[str, Any]      # Metadata

class Reranker:
    def __init__(self,
                 base_url: str = os.getenv("RERANKING_BASE_URL"),
                 api_key: str = os.getenv("RERANKING_API_KEY"),
                 model_name: str = os.getenv("RERANKING_MODEL_NAME"),
                 max_retries: int = 3,
                 retry_delay: int = 1):
        """
        Initialize reranker
        
        Args:
            base_url: API Base URL
            api_key: API Key
            model_name: Model name. Default: BAAI/bge-reranker-v2-m3
            max_retries: Maximum retries
            retry_delay: Retry delay (seconds)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if not all([self.base_url, self.api_key]):
            raise ValueError("Missing required configuration for reranking. Check your .env file.")
        
    def _get_rerank(self, 
                        query: str, 
                        documents: List[str],
                        top_n: Optional[int] = 5) -> Dict[str, Any]:
        """
        Call reranking API
        
        Args:
            query: Query text
            documents: List of texts to be reranked
            top_n: Number of results to return
            
        Returns:
            Dict: Full response from the reranking API
        """
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "return_documents": True,
            "max_chunks_per_doc": 1024,
            "overlap_tokens": 80
        }
        
        if top_n is not None:
            payload["top_n"] = top_n
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    raise ValueError(f"Reranking API call failed after {self.max_retries} retries: {e}")
                time.sleep(self.retry_delay)
    
    def rerank(self, query: str, search_results: List[Dict], top_k: Optional[int] = 5) -> Tuple[List[RerankResult], float]:
        """
        Rerank search results
        
        Args:
            query: Query text
            search_results: List of search results
            top_k: Number of results to return
            
        Returns:
            Tuple[List[RerankResult], float]: Reranking results list and highest relevance score
        """
        if DEBUG:
            print(f"\n[Reranker] Reranking {len(search_results)} search results")
        
        try:
            documents = [result["content"] for result in search_results]
            
            # Call reranking API
            api_response = self._get_rerank(
                query=query,
                documents=documents,
                top_n=top_k
            )
            
            reranked = []
            max_relevance_score = 0.0
            
            for result in api_response["results"]:
                relevance_score = float(result["relevance_score"])
                max_relevance_score = max(max_relevance_score, relevance_score)
                original_result = search_results[result["index"]]
                
                reranked.append(RerankResult(
                    content=result["document"]["text"],
                    score=original_result.get("score", 0.0),
                    relevance_score=relevance_score,
                    index=result["index"],
                    metadata=original_result["metadata"]
                ))
            
            if DEBUG:
                print(f"[Reranker] Reranking completed")
                print(f"[Reranker] Highest relevance score: {max_relevance_score:.3f}")
                if reranked:
                    print(f"[Reranker] Most relevant document (score={reranked[0].relevance_score:.3f}): {reranked[0].content[:100]}...")
            
            return reranked, max_relevance_score
            
        except Exception as e:
            print(f"[Reranker] Reranking failed, using original order: {e}")
            # If API call fails, revert to using original retrieval scores
            reranked = []
            max_relevance_score = 0.0
            
            for idx, result in enumerate(search_results):
                relevance_score = 1.0 - (result.get("score", 0.0) or 0.0)
                max_relevance_score = max(max_relevance_score, relevance_score)
                
                reranked.append(RerankResult(
                    content=result["content"],
                    score=result.get("score", 0.0),
                    relevance_score=relevance_score,
                    index=idx,
                    metadata=result["metadata"]
                ))
            
            # Sort by relevance score
            reranked.sort(key=lambda x: x.relevance_score, reverse=True)
            
            if DEBUG:
                print(f"[Reranker] Using original retrieval scores")
                print(f"[Reranker] Highest relevance score: {max_relevance_score:.3f}")
            
            return reranked, max_relevance_score
