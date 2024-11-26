import sys
import os
from pathlib import Path
from typing import Optional
import threading

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from server.app.core.rag.data_preprocess import DataPreprocessor
from server.app.core.rag.embedding import EmbeddingService
from server.app.core.rag.store import VectorStore
from server.app.core.rag.indexing import VectorIndexer
from server.app.core.rag.reranking import Reranker
from server.app.core.rag.generator import PromptGenerator

class RAGPipeline:
    """RAG pipeline for enhancing prompts with relevant context"""
    _instance: Optional['RAGPipeline'] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                print("Initializing new RAG Pipeline instance...")
                self._initialize_components()
                self._setup_database()
                RAGPipeline._initialized = True
                print("RAG Pipeline initialization completed.")

    @classmethod
    def get_instance(cls) -> 'RAGPipeline':
        """Get or create RAGPipeline instance"""
        instance = cls()
        return instance

    def _initialize_components(self):
        """Initialize all RAG components"""
        try:
            os.environ["CHROMA_BATCH_SIZE"] = "32"
            self.vector_db_path = PROJECT_ROOT / "server" / "data"
            self.config_path = self.vector_db_path / "config.json"
            self.db_dir = self.vector_db_path / "vectors"
            self.db_dir.mkdir(parents=True, exist_ok=True)

            self.preprocessor = DataPreprocessor()
            self.embedding_service = EmbeddingService()
            self.vector_store = VectorStore(
                collection_name="test_medical",
                persist_directory=str(self.db_dir)
            )
            self.indexer = VectorIndexer(
                embedding_service=self.embedding_service,
                vector_store=self.vector_store
            )
            self.reranker = Reranker()
            self.generator = PromptGenerator()
            print("RAG Pipeline components initialized successfully")
        except Exception as e:
            print(f"Failed to initialize RAG components: {e}")
            raise

    def _setup_database(self):
        """Setup and index the vector database"""
        try:
            self.documents = self.preprocessor.process(self.config_path)
            print(f"\nProcessed {len(self.documents)} document chunks")
            self.preprocessor.splitter.print_split_result(self.documents)
            self.indexer.index_documents(self.documents)
        except Exception as e:
            print(f"Failed to setup vector database: {e}")
            raise

    def get_enhanced_prompt(self, query: str) -> str:
        """
        Get RAG-enhanced prompt for a given query
        
        Args:
            query: User's input query
            
        Returns:
            Enhanced prompt with relevant context
        """
        try:
            # Get query embedding
            query_vector = self.embedding_service.embed_query(query)
            
            # Search relevant documents
            search_results = self.vector_store.search(
                query_vector=query_vector,
                limit=10
            )
            
            # Rerank results
            reranked_results, max_relevance_score = self.reranker.rerank(
                query=query,
                search_results=search_results,
                top_k=5
            )
            
            # Prepare documents for prompt
            documents_for_prompt = [{
                "content": result.content,
                "metadata": result.metadata
            } for result in reranked_results]
            
            # Generate enhanced prompt
            enhanced_prompt = self.generator.generate(
                query=query,
                documents=documents_for_prompt,
                max_relevance_score=max_relevance_score
            )
            
            return enhanced_prompt
        except Exception as e:
            print(f"Error generating enhanced prompt: {e}")
            # Fallback to original query if RAG fails
            return query
