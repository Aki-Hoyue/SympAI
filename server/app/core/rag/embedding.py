from typing import List, Dict, Any, Union
from pathlib import Path
import json
import time
import requests
import numpy as np
from langchain.schema import Document
from dotenv import load_dotenv
import os
from server.utils.config import PROJECT_ROOT

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

class EmbeddingService:
    def __init__(self, 
                 base_url: str = os.getenv("EMBEDDING_BASE_URL"),
                 api_key: str = os.getenv("EMBEDDING_API_KEY"),
                 model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-zh-v1.5"),
                 max_retries: int = 3,
                 retry_delay: int = 1):
        """
        Initialize the Embedding service
        
        Args:
            base_url: API base URL
            api_key: API key
            model_name: Model name
            max_retries: Maximum retries
            retry_delay: Retry delay (seconds)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if not all([self.base_url, self.api_key, self.model]):
            raise ValueError("Missing required configuration. Please check your .env file.")

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get the embedding vector of a single text using API
        """
        payload = {
            "model": self.model,
            "input": text,
            "encoding_format": "float"
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()["data"][0]["embedding"]
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    raise ValueError(f"Failed to get embedding after {self.max_retries} retries: {e}")
                time.sleep(self.retry_delay)

    def embed_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Process the document list, return the document list with embedding vectors
        
        Args:
            documents: Document object list
            
        Returns:
            List[Dict]: Document list with content, metadata and embedding vectors
        """
        embedded_docs = []
        total = len(documents)
        
        for i, doc in enumerate(documents, 1):
            try:
                vector = self._get_embedding(doc.page_content)
                embedded_docs.append({
                    "id": f"doc_{i}",
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "embedding": vector
                })
                print(f"Processed document {i}/{total}")
            except Exception as e:
                print(f"Error processing document {i}: {e}")
                continue
                
        return embedded_docs

    def embed_query(self, query: str) -> List[float]:
        return self._get_embedding(query)

    def save_embeddings(self, 
                       vector_data: Dict[str, Any], 
                       output_dir: Union[str, Path] = PROJECT_ROOT / "server" / "data" / "vectors") -> Dict[str, Path]:
        """
        Save the embedding vectors and document information
        
        Args:
            vector_data: Vector data in Chroma format
            output_dir: Output directory
            
        Returns:
            Dict[str, Path]: Saved file path dictionary
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        json_filename = f"{timestamp}_vectors.json"
        npy_filename = f"{timestamp}_vectors.npy"
        
        # Save as JSON format
        json_file = output_dir / json_filename
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(vector_data, f, ensure_ascii=False, indent=2)
        
        # Save as numpy format - extract vectors from the Chroma format data
        np_file = output_dir / npy_filename
        np.save(np_file, np.array(vector_data["vectors"]))  # 直接使用vectors字段
        
        if DEBUG:
            print(f"[EmbeddingService] Embeddings saved to {json_file} and {np_file}")
        
        return {
            "json_data": json_file,
            "numpy_data": np_file
        }

    def get_chroma_data(self, embedded_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get the data format suitable for Chroma
        
        Args:
            embedded_docs: Document list with embedding vectors
            
        Returns:
            Dict: Chroma format data
            {
                "ids": List[str],
                "vectors": List[List[float]],
                "metadata": List[Dict]
            }
        """
        if DEBUG:
            print(f"\n[EmbeddingService] Convert {len(embedded_docs)} documents to Chroma format")
        
        chroma_data = {
            "ids": [doc["id"] for doc in embedded_docs],
            "vectors": [doc["embedding"] for doc in embedded_docs],
            "metadata": []
        }
        
        for doc in embedded_docs:
            metadata = {
                "content": doc["content"],
                "source": doc["metadata"].get("title", "unknown")
            }
            chroma_data["metadata"].append(metadata)
        
        if DEBUG:
            print("[EmbeddingService] Data conversion completed")
        return chroma_data
