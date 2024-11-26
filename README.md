# SympAI
English | [中文](https://github.com/Aki-Hoyue/SympAI/blob/main/README_cn.md)

## Introduction
SympAI is an intelligent healthcare system that combines artificial intelligence with comprehensive medical knowledge. The system aims to provide users with accurate symptom analysis and personalized health guidance through natural language interaction.

At its core, SympAI features an advanced AI-powered analysis engine that processes user-described symptoms and health concerns. By leveraging a robust medical knowledge base, it generates professional medical insights, risk assessments, and tailored health recommendations. The system also includes interactive Q&A capabilities and personalized health management tools, making it a comprehensive platform for users to better understand and manage their health conditions.

Simply speaking, SympAI is an **AI Agent with RAG System** that empowers users to harness the power of AI in their healthcare journey, enabling them to make informed decisions about their well-being and health care.

## Architecture

![Architecture_SympAI](https://s2.loli.net/2024/11/27/pErexhNMF4VHX1Y.png)

### Dataset
We use a large-scale dataset of medical documents for constructing our database. This dataset includes a wide range of medical knowledge, such as symptoms, diseases, treatments, and precautions.

You need to add your own data in `server/data/raw` and set metadata in `server/data/config.json`

### Embedding
Embedding is the process of converting text into a vector representation that can be used for semantic similarity. 

We use remote embedding models like BAAI/bge-large-en-v1.5 to generate embeddings from text. This allows us to use semantic similarity to compare and rank documents.

This model can be set in the `.env` file.

### Vector Store
We use ChromaDB to store embeddings and documents. This allows us to easily search for similar documents.

### Reranking
Reranking is the process of re-ranking the search results based on the user's query and the retrieved documents. The goal is to provide a more relevant and accurate ranking of the documents, allowing users to find the most relevant information more quickly and easily.

We use a remote reranking model like BAAI/bge-reranker-v2-m3 to perform reranking. This model can be set in the `.env` file.

### Authorization
We use a simple authorization model to control access to the system. It checks the headers for a valid API key. Default API key is `sk-hoyue-sympai`.

### LLM
We combine online LLM and Local LLM to get better results. We set the agent of online LLM, but not set the agent of local LLM. You can use your local LLM by editting `server/app/core/models/local.py`

## Features

### 🏥 Medical Advice and Risk Assessment
- Professional risk assessment and analysis of physical conditions
- Early detection of illness severity and potential health risks
- Timely recommendations for medical attention and preventive measures

### 🔍 Intelligent Symptom Analysis
- Advanced analysis of user-reported symptoms
- Identification of possible causes and related factors
- Duration and impact analysis for common conditions
- Reduction of unnecessary health-related anxiety

### 📚 Medical Knowledge Base
- Comprehensive health information and medical guidance
- Easy-to-understand explanations of medical terms and conditions
- Professional medical knowledge for healthcare practitioners
- Reliable reference material for medical education

### 👤 Personal Health Management
- Creation and management of personal health profiles
- Recording and tracking of symptom analysis history
- Storage of important AI conversation records
- Customized health monitoring and planning

### 🔄 Continuous Improvement System
- User feedback mechanism for system enhancement
- Adaptive learning from user interactions
- Regular updates to medical knowledge base
- Quality assurance of medical advice

## Environment

### Frontend Requirements
- Node.js >= 16.0.0
- TypeScript 4.x
- React 18.x
- Vite 4.x
- Tailwind CSS 3.x

### Backend Requirements
- Python >= 3.8
- FastAPI
- LangChain
- ChromaDB
- PyTorch

### Development Tools
- yarn (package manager)
- Git (version control)
- Docker (containerization)

### Optional
- Electron (for desktop application)
- CUDA-capable GPU (for better performance)

## Usage

### Clone the Repository

```bash
git clone https://github.com/Aki-Hoyue/SympAI.git
cd SympAI
```

### Frontend Setup

1. Install dependencies
```bash
yarn install
```

2. Start development server
```bash
yarn dev
```

3. Build for production
```bash
yarn build
```

4. Build desktop application (Optional)
```bash
# For development
yarn electron

# For production
yarn make
```

### Backend Setup

1. Install Python dependencies
```bash
pip install -r requirements.txt
```

2. Configure environment variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configurations
# Required: API keys, database settings, etc.
```

3. Start the backend server
```bash
python run.py
```

### Using Docker (Optional)

1. Build and run using Docker Compose
```bash
docker-compose up --build
```

2. Or build and run containers separately
```bash
# Build frontend
docker build -t sympai-frontend .

# Run frontend container
docker run -p 3000:3000 sympai-frontend

# Build and run backend
docker-compose up backend
```

### Access the Application

- Frontend Development: Visit `http://localhost:5173`
- Production Build: Visit `http://localhost:3000`
- API Documentation: Visit `http://localhost:8000/docs`

## Reference
Our frontend is edited from Better ChatGPT by [ztjhz](https://github.com/ztjhz/BetterChatGPT).

- [Better ChatGPT](https://github.com/ztjhz/BetterChatGPT)
- [Node.js](https://nodejs.org/)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [ChromaDB](https://chromadb.readthedocs.io/en/latest/)
- [PyTorch](https://pytorch.org/)

## Contributors
- Project Owner: [Hoyue](https://github.com/Aki-Hoyue)
- Frontend: [Fan Jiacheng](https://github.com/fanjiach)
- Backend: [Hoyue](https://github.com/Aki-Hoyue)

<a href="https://github.com/Aki-Hoyue"><img src="https://avatars3.githubusercontent.com/u/73027485?s=400" alt="Hoyue" width="30">Hoyue</a>
<a href="https://github.com/fanjiach"><img src="https://avatars3.githubusercontent.com/u/36438236?s=400" alt="Fan Jiacheng" width="30">Fan Jiacheng</a>
