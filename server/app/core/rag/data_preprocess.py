from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from pathlib import Path
import json
from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class TextSplitter:
    def __init__(self, 
                 chunk_size: int = 200, 
                 chunk_overlap: int = 50, 
                 separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.special_separators = separators if separators else None
        default_separators = [
            "\n\n", "\r\n\r\n",
            "。", "！", "？", "；", "......",
            ". ", "! ", "? ", "; ",
            "，", "：", """, """,
            ", ", ": ",
            "\n", " ", ""
        ]
        
        self.set_chunk(chunk_size, chunk_overlap, default_separators)
    
    def set_chunk(self, chunk_size: int = 200, chunk_overlap: int = 50, separators: List[str] = None):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            keep_separator=False,
            is_separator_regex=False
        )
        
    def split(self, text: str, metadata: Dict[str, Any] = {}) -> List[Document]:
        chunks = [text]
        if self.special_separators:
            for separator in self.special_separators:
                new_chunks = []
                for chunk in chunks:
                    new_chunks.extend(chunk.split(separator))
                chunks = new_chunks

        documents = []
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            if len(chunk) > self.chunk_size:
                sub_chunks = self.splitter.split_text(chunk)
                documents.extend([Document(page_content=sub_chunk, metadata=metadata) 
                               for sub_chunk in sub_chunks])
            else:
                documents.append(Document(page_content=chunk.strip(), metadata=metadata))
                
        return documents

    def print_split_result(self, documents: List[Document]):
        print("Split result:")
        print("-" * 100)
        for i, doc in enumerate(documents, 1):
            print(f"Chunk {i}:")
            print(f"Length: {len(doc.page_content)}")
            print("\nContent:")
            print(doc.page_content)
            if i < len(documents):
                next_content = documents[i].page_content
                current_content = doc.page_content
                overlap = self._find_overlap(current_content, next_content)
                if overlap:
                    print("\nOverlap with next chunk:")
                    print(f"Length: {len(overlap)}")
                    print(overlap)
            print("\nMetadata:")
            print(doc.metadata)
            print("-" * 100)

    def _find_overlap(self, text1: str, text2: str) -> str:
        min_length = min(len(text1), len(text2))
        for i in range(min_length, 0, -1):
            if text1[-i:] == text2[:i]:
                return text1[-i:]
        return ""

class BaseDocumentLoader(ABC):
    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 50, separators: List[str] = None):
        self.splitter = TextSplitter(chunk_size, chunk_overlap, separators)
    
    @abstractmethod
    def load(self, source: Union[str, Path], title: str = None) -> List[Document]:
        pass

class TextFileLoader(BaseDocumentLoader):
    '''
    Handle text file
    '''
    
    def load(self, source: Union[str, Path], title: str = None) -> List[Document]:
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")
            
        with source_path.open('r', encoding='utf-8') as f:
            text = f.read()
        metadata = {
            "source": str(source_path),
            "type": "text",
            "title": title or source_path.name,
            "chunk_size": self.splitter.chunk_size,
            "chunk_overlap": self.splitter.chunk_overlap,
            "separators": self.splitter.special_separators
        }
        return self.splitter.split(text, metadata)

class JsonlLoader(BaseDocumentLoader):
    '''
    Handle JSON and JSONL file
    '''
    
    def load(self, source: Union[str, Path], title: str = None) -> List[Document]:
        source_path = Path(source)
        
        with source_path.open('r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSONL file: {source_path}")
                raise e
            
            text = ""
            for i, line in enumerate(data, 1):
                text += "<Question>: " + line["Q"] + "\n<Answer>: " + line["A"] + "\n<Q&A Break>"
                metadata = {
                    "source": str(source_path),
                    "type": "jsonl",
                    "title": title or source_path.name,
                    "chunk_size": self.splitter.chunk_size,
                    "chunk_overlap": self.splitter.chunk_overlap,
                    "separators": self.splitter.special_separators
                }
                
            return self.splitter.split(text, metadata)
    

class HuggingFaceLoader(BaseDocumentLoader):
    '''
    Handle Huggingface dataset
    '''
    def load(self, source: str, title: str = None) -> List[Document]:
        try:
            dataset = load_dataset(source)
            documents = []
            
            for split in dataset.keys():
                for idx, item in enumerate(dataset[split]):
                    try:
                        text = item.pop("text", "")
                        metadata = {
                            "source": f"huggingface/{source}",
                            "type": "huggingface",
                            "split": split,
                            "index": idx,
                            "title": title or source,
                            "chunk_size": self.splitter.chunk_size,
                            "chunk_overlap": self.splitter.chunk_overlap,
                            "separators": self.splitter.special_separators,
                            **item
                        }
                        documents.extend(self.splitter.split(text, metadata))
                    except Exception as e:
                        print(f"Error processing item {idx} in split {split}: {e}")
            
            return documents
        except Exception as e:
            raise ValueError(f"Failed to load dataset {source}: {e}")

class DocumentLoader:
    @staticmethod
    def create_loader(source_type: str, chunk_size: int = 200, chunk_overlap: int = 50, separators: List[str] = None) -> BaseDocumentLoader:
        loaders = {
            "text": TextFileLoader,
            "jsonl": JsonlLoader,
            "huggingface": HuggingFaceLoader
        }
        
        if source_type not in loaders:
            raise ValueError(f"Unsupported source type: {source_type}")
            
        return loaders[source_type](chunk_size, chunk_overlap, separators)

class DataPreprocessor:
    def __init__(self):
        self.splitter = TextSplitter()
        self.loader = DocumentLoader()
    
    def process(self, config_path: Union[str, Path]) -> List[Document]:
        """
        Process data source configuration file.

        Args:
            config_path: Data source configuration file path
        Sample configuration file:
        ```json
        [
            {
                "type": "text",
                "title": "sample",
                "path": "server/data/sample.txt"
            },
            {
                "type": "jsonl",
                "title": "sample",
                "path": "server/data/sample.jsonl"
            },
            {
                "type": "huggingface",
                "title": "sample",
                "path": "FreedomIntelligence/huatuo_encyclopedia_qa"
            }
        ]
        ```
            
        Returns:
            List[Document]: Processed document list
        """
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not isinstance(config, list):
            raise ValueError("Data source configuration file loads error")
        
        documents = []
        for source in config:
            project_path = Path(__file__).resolve().parent.parent.parent.parent
            path = project_path / "data" / "raw" / source["filename"]
            documents.extend(self.process_single_source(source, path))
        # TODO: 处理完一个文件后，立刻将其嵌入到向量数据库中。重写项目目录获取方法
        return documents

    def process_single_source(self, source: Dict[str, Any], path: Union[str, Path]) -> List[Document]:
        loader = self.loader.create_loader(source["type"], source["chunk_size"], source["chunk_overlap"], source["separators"])
        return loader.load(path, source["title"])
    
