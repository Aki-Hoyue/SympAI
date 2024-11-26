from typing import Dict, Any, Optional, List
from pathlib import Path
import chromadb
from chromadb.config import Settings
import time
import gc
from dotenv import load_dotenv
import os

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

class VectorStore:
    def __init__(self, 
                 collection_name: str = "medical_knowledge",
                 persist_directory: Optional[str] = None):
        """
        Initialize vector database Chroma
        
        Args:
            collection_name: Collection name
            persist_directory: Persistent directory path, if not provided, use in-memory storage
        """
        try:
            self.collection_name = collection_name
            self.persist_directory = persist_directory
            
            # Configure Chroma settings
            settings = Settings(
                persist_directory=persist_directory,
                is_persistent=persist_directory is not None,
                anonymized_telemetry=False,  # Disable telemetry
                allow_reset=True,  # Allow reset
            )
            
            # Initialize client
            self.client = chromadb.Client(settings)
            
            # If the collection exists, delete it
            try:
                if self.client.get_collection(collection_name):
                    self.client.delete_collection(collection_name)
            except:
                pass
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Medical knowledge base"}
            )
            
            if DEBUG:   
                print(f"[VectorStore] Successfully initialized vector store: {collection_name}")
            
        except Exception as e:
            print(f"[VectorStore] Initialization failed: {str(e)}")
            raise
    
    def insert(self, data: Dict[str, Any]):
        """
        Insert data by batch

        Args:
            data: Data in Chroma format
        """
        try:
            documents = [meta["content"] for meta in data["metadata"]]
            metadatas = data["metadata"]
            ids = data["ids"]
            embeddings = data["vectors"]
            
            batch_size = 32
            total_docs = len(documents)
            
            if DEBUG:
                print(f"\n[VectorStore] Starting to insert {total_docs} documents in batches")
            
            for i in range(0, total_docs, batch_size):
                end_idx = min(i + batch_size, total_docs)
                batch_data = {
                    "ids": ids[i:end_idx],
                    "embeddings": embeddings[i:end_idx],
                    "documents": documents[i:end_idx],
                    "metadatas": metadatas[i:end_idx]
                }
                
                if DEBUG:
                    print(f"[VectorStore] Preparing to insert {i+1}-{end_idx} documents")
                
                try:
                    self.collection.add(
                        ids=batch_data["ids"],
                        embeddings=batch_data["embeddings"],
                        documents=batch_data["documents"],
                        metadatas=batch_data["metadatas"]
                    )
                    if DEBUG:
                        print(f"[VectorStore] Successfully inserted {i+1}-{end_idx} documents")
                    
                except Exception as batch_error:
                    print(f"[VectorStore] Batch Insert error ({i+1}-{end_idx}): {str(batch_error)}")
                    retry_count = 3
                    for attempt in range(retry_count):
                        try:
                            self.collection.add(
                                ids=batch_data["ids"],
                                embeddings=batch_data["embeddings"],
                                documents=batch_data["documents"],
                                metadatas=batch_data["metadatas"]
                            )
                            if DEBUG:
                                print(f"[VectorStore] Successfully inserted {i+1}-{end_idx} documents (Retry {attempt + 1})")
                            break
                        except Exception as e:
                            print(f"[VectorStore] Retry {attempt + 1} failed: {e}")
                            time.sleep(2)
                    else:
                        print(f"[VectorStore] Failed to insert {i+1}-{end_idx} documents, skipping this batch")
                        continue
                
                gc.collect()
                time.sleep(1)

            if DEBUG:
                print("[VectorStore] Data insertion completed")
            
        except Exception as e:
            print(f"[VectorStore] Insert data failed: {str(e)}")
            raise ValueError(f"Failed to insert data: {str(e)}")
    
    def search(self, query_vector: List[float], limit: int = 10) -> List[Dict]:
        """
        Search for the most similar vector

        Args:
            query_vector: Query vector
            limit: Search limit
            
        Returns:
            List[Dict]: Search results
        """
        if DEBUG:
            print(f"\n[VectorStore] Performing vector search, limit={limit}")
        
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=limit
            )
            
            formatted_results = []
            if results["ids"]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i] if "distances" in results else None
                    })
            
            if DEBUG:
                print(f"[VectorStore] Found {len(formatted_results)} related documents")
                if formatted_results:
                    print(f"[VectorStore] Most related document: {formatted_results[0]['content'][:100]}...")
            
            return formatted_results
        
        except Exception as e:
            print(f"[VectorStore] Search failed: {e}")
            raise ValueError(f"Search failed: {e}")
    
    def drop_collection(self):
        """
        Drop collection
        """
        try:
            self.client.delete_collection(self.collection_name)
        except Exception as e:
            print(f"[VectorStore] Drop collection failed: {e}")
    
    def get_collection(self):
        """
        Get collection instance
        """
        return self.collection
