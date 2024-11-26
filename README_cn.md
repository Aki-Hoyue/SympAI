# SympAI
[English](https://github.com/Aki-Hoyue/SympAI/blob/main/README.md) | 中文

## 简介

SympAI 是一个将 AI 与专业医学知识相结合的智能医疗辅助系统。通过自然语言交互的方式，为用户提供准确的症状分析和个性化的健康指导。

系统核心采用先进的 AI 驱动引擎，能够处理用户描述的症状和健康问题。通过调用完善的医学知识库，系统可以生成专业的医疗见解、风险评估和个性化建议。此外，系统还集成了交互式问答功能和个性化健康管理工具，为用户打造了一个全面的健康管理平台。

简而言之，SympAI 是一个基于 **AI 智能体和 RAG 系统**的智能平台，让用户能够在健康管理过程中充分利用 AI 的优势，从而做出更明智的健康决策。

## 功能特点

### 🏥 医疗建议与风险评估
- 专业的身体状况风险评估与分析
- 及早发现疾病严重程度和潜在风险
- 及时提供就医建议和预防措施

### 🔍 智能症状分析
- 先进的用户症状分析
- 识别可能的病因和相关因素
- 常见症状的持续时间和影响分析
- 帮助减轻不必要的健康焦虑

### 📚 医学知识库
- 全面的健康信息和医疗指导
- 通俗易懂的医学术语解释
- 面向医疗从业者的专业知识
- 可靠的医学教育参考资料

### 👤 个人健康管理
- 创建和管理个人健康档案
- 记录和追踪症状分析历史
- 存储重要的 AI 对话记录
- 定制化的健康监测和规划

### 🔄 持续优化系统
- 用户反馈机制
- 基于用户交互的自适应学习
- 定期更新医学知识库
- 医疗建议质量保证

## 系统架构

![Architecture_SympAI](https://s2.loli.net/2024/11/27/pErexhNMF4VHX1Y.png)

### 数据集
我们使用大规模医疗文档数据集构建数据库。该数据集包含广泛的医学知识，涵盖症状、疾病、治疗方案和预防措施等内容。

您需要在 `server/data/raw` 目录下添加自己的数据，并在 `server/data/config.json` 中设置元数据信息。

### 向量嵌入
向量嵌入是将文本转换为可用于语义相似度比较的向量表示的过程。

我们使用远程嵌入模型（如 BAAI/bge-large-en-v1.5）来生成文本的向量表示。这使我们能够通过语义相似度来比较和排序文档。

该模型可以在 `.env` 文件中配置。

### 向量存储
我们使用 ChromaDB 来存储嵌入向量和文档。这使我们能够方便地搜索相似文档。

### 重排序
重排序是根据用户查询和检索到的文档对搜索结果进行重新排序的过程。其目标是提供更相关和准确的文档排序，使用户能够更快速、更便捷地找到最相关的信息。

我们使用远程重排序模型（如 BAAI/bge-reranker-v2-m3）来执行重排序。该模型可以在 `.env` 文件中配置。

### 授权认证
我们使用简单的授权模型来控制系统访问。系统会检查请求头中是否包含有效的 API 密钥。默认的 API 密钥是 `sk-hoyue-sympai`。

### 大语言模型
我们结合在线和本地大语言模型以获得更好的效果。我们为在线大语言模型设置了智能体，但未为本地大语言模型设置。您可以通过编辑 `server/app/core/models/local.py` 来使用您的本地大语言模型。

## 环境要求

### 前端依赖
- Node.js >= 16.0.0
- TypeScript 4.x
- React 18.x
- Vite 4.x
- Tailwind CSS 3.x

### 后端依赖
- Python >= 3.8
- FastAPI
- LangChain
- ChromaDB
- PyTorch

### 开发工具
- yarn（包管理器）
- Git（版本控制）
- Docker（容器化）

### 可选配置
- Electron（桌面应用程序）
- CUDA 支持的 GPU（提升性能）

## 使用说明

### 克隆项目

```bash
git clone https://github.com/Aki-Hoyue/SympAI.git
cd SympAI
```

### 前端配置

1. 安装依赖
```bash
yarn install
```

2. 启动开发服务器
```bash
yarn dev
```

3. 生产环境构建
```bash
yarn build
```

4. 构建桌面应用（可选）
```bash
# 开发环境
yarn electron

# 生产环境
yarn make
```

### 后端配置

1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置必要参数
# 需要配置：API密钥、数据库设置等
```

3. 启动后端服务器
```bash
python run.py
```

### Docker 部署（可选）

1. 使用 Docker Compose 构建并运行
```bash
docker-compose up --build
```

2. 或分别构建并运行容器
```bash
# 构建前端
docker build -t sympai-frontend .

# 运行前端容器
docker run -p 3000:3000 sympai-frontend

# 构建并运行后端
docker-compose up backend
```

### 访问应用

- 开发环境：访问 `http://localhost:5173`
- 生产环境：访问 `http://localhost:3000`
- API 文档：访问 `http://localhost:8000/docs`

## 参考项目
我们的前端基于 [ztjhz](https://github.com/ztjhz/BetterChatGPT) 的 Better ChatGPT 项目进行改进。

- [Better ChatGPT](https://github.com/ztjhz/BetterChatGPT)
- [Node.js](https://nodejs.org/)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [ChromaDB](https://chromadb.readthedocs.io/en/latest/)
- [PyTorch](https://pytorch.org/)

## 项目成员
- 项目负责人：[Hoyue](https://github.com/Aki-Hoyue)
- 前端开发：[Fan Jiacheng](https://github.com/fanjiach)
- 后端开发：[Hoyue](https://github.com/Aki-Hoyue)

<a href="https://github.com/Aki-Hoyue"><img src="https://avatars3.githubusercontent.com/u/73027485?s=400" alt="Hoyue" width="30">Hoyue</a>
<a href="https://github.com/fanjiach"><img src="https://avatars3.githubusercontent.com/u/36438236?s=400" alt="Fan Jiacheng" width="30">Fan Jiacheng</a>
