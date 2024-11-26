import pytest
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.rag.data_preprocess import DataPreprocessor
from server.app.core.rag.embedding import EmbeddingService
from server.app.core.rag.store import VectorStore
from server.app.core.rag.indexing import VectorIndexer
from server.app.core.rag.reranking import Reranker
from server.app.core.rag.generator import PromptGenerator

TEST_DATA_DIR = PROJECT_ROOT / "server" / "data"
CONFIG_PATH = TEST_DATA_DIR / "config.json"

class TestRAGPipeline:
    """
    RAG system integration test
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test environment"""
        # Set a smaller batch size
        os.environ["CHROMA_BATCH_SIZE"] = "32"
        
        # Ensure the test database directory exists
        test_db_dir = TEST_DATA_DIR / "vectors"
        test_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the components
        self.preprocessor = DataPreprocessor()
        self.embedding_service = EmbeddingService()
        
        # Create a vector store instance, using the test-specific persistence directory
        self.vector_store = VectorStore(
            collection_name="test_medical_1",
            persist_directory=str(test_db_dir)
        )
        
        self.indexer = VectorIndexer(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store
        )
        self.reranker = Reranker()
        self.generator = PromptGenerator()
        
        # Load and process the test data
        self.documents = self.preprocessor.process(CONFIG_PATH)[60:]
        print(f"\nTotally {len(self.documents)} document chunks")
        self.preprocessor.splitter.print_split_result(self.documents)
        
        # Ensure at least one document was processed
        assert len(self.documents) > 0, "No documents were processed"
        
        # Build the index
        success = self.indexer.index_documents(self.documents)
        assert success, "Failed to index documents"
        
        yield
        
        # Clean up the test data
        self.vector_store.drop_collection()
        
        # Delete the test database directory, except for json and numpy files
        try:
            for file in os.listdir(test_db_dir):
                if file.endswith(".json") or file.endswith(".npy"):
                    continue
                os.remove(os.path.join(test_db_dir, file))
        except Exception as e:
            print(f"Failed to delete test database directory: {e}")
        
    def test_basic_rag_flow(self):
        """Test the basic RAG flow"""
        # 1. Prepare the test query
        query = "I had a headache and a sore throat."
        
        # 2. Get the query vector
        query_vector = self.embedding_service.embed_query(query)
        
        # 3. Search for relevant documents
        search_results = self.vector_store.search(
            query_vector=query_vector,
            limit=10
        )
        
        assert len(search_results) > 0, "No search results returned"
        
        # 4. Rerank the results
        reranked_results, max_relevance_score = self.reranker.rerank(
            query=query,
            search_results=search_results,
            top_k=5
        )
        
        assert len(reranked_results) > 0, "No results after reranking"
        
        # 5. Generate the prompt
        documents_for_prompt = [{
            "content": result.content,
            "metadata": result.metadata
        } for result in reranked_results]
        
        prompt = self.generator.generate(
            query=query,
            documents=documents_for_prompt,
            max_relevance_score=max_relevance_score
        )
        
        # Verify
        assert query in prompt
    
if __name__ == "__main__":
    pytest.main(["-v", "--disable-warnings", __file__]) 
