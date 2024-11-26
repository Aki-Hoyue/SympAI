server/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI Entry
│   ├── api/                         # API Server
│   │   ├── __init__.py
│   │   └── routes/                  # API Routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── data_preprocess.py   # Data Preprocessing
│   │   │   ├── embeddings.py        # Embedding
│   │   │   ├── generator.py         # Generator Prompt
│   │   │   ├── indexing.py          # Construct Index
│   │   │   ├── retriever.py         # Retriever
│   │   │   ├── reranking.py         # Reranking
│   │   │   └── store.py             # Vector Store
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── base.py              # Model Base Class
│   │       ├── local.py             # Local Model Implementation
│   │       └── online.py            # Online Model Implementation
│   │   
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # Configuration of RAG Pipeline
│       └── prompt.py                # Prompt Definitions
│   
├── tests/                           # Test Files
│   ├── test_api.py                  # API Test
│   ├── test_models.py               # Model Test
│   └── test_openai.py               # OpenAI Model Test
│   └── test_rag_pipeline.py         # RAG Pipeline Test
└── data/                            # Medical Knowledge Base Data
    ├── raw/                         # Raw Data
    └── vectors/                     # Vector Data
