from typing import List, Dict, Any
from server.app.core.rag.store import VectorStore
from server.app.core.rag.embedding import EmbeddingService
from langchain.schema import Document
from dotenv import load_dotenv
import os

load_dotenv()

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

class VectorIndexer:
    def __init__(self, 
                 embedding_service: EmbeddingService,
                 vector_store: VectorStore):
        """
        Initialize the index manager
        
        Args:
            embedding_service: Embedding service instance
            vector_store: Vector store instance
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
    def index_documents(self, documents: List[Document]) -> bool:
        """
        Build index for documents
        
        Args:
            documents: Document list
            
        Returns:
            bool: True if index building is successful, False otherwise
        """
        try:
            if DEBUG:
                print(f"\n[VectorIndexer] Processing {len(documents)} documents")
            
            # Get embeddings
            embedded_docs = self.embedding_service.embed_documents(documents)
            if DEBUG:
                print(f"[VectorIndexer] Successfully generated embeddings for {len(embedded_docs)} documents")
            
            # Convert to Chroma format
            vector_data = self.embedding_service.get_chroma_data(embedded_docs)
            if DEBUG:
                print(f"[VectorIndexer] Data conversion completed, preparing to insert into vector store")
                print(f"[VectorIndexer] Vector data format: {list(vector_data.keys())}")
            
            # Save the vector data
            try:
                output_paths = self.embedding_service.save_embeddings(vector_data)
                if DEBUG:
                    print(f"[VectorIndexer] Vector data saved to: {output_paths}")
            except Exception as save_error:
                print(f"[VectorIndexer] Warning: Failed to save vectors: {save_error}")
                # Continue even if saving fails
            
            # Insert into vector store
            self.vector_store.insert(vector_data)
            if DEBUG:
                print(f"[VectorIndexer] Index building completed")
            
            return True
        
        except Exception as e:
            if DEBUG:
                print(f"[VectorIndexer] Index building failed: {e}")
                import traceback
                print(traceback.format_exc())
            return False
    
    def rebuild_index(self):
        """
        Rebuild index
        """
        try:
            self.vector_store.rebuild_index()
            return True
        except Exception as e:
            print(f"Failed to rebuild index: {e}")
            return False 
