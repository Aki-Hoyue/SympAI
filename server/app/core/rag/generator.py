from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv
from server.app.utils.prompt import QUERY_PROMPT

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

@dataclass
class PromptTemplate:
    context: str
    human: str
    
    def format(self, **kwargs) -> str:
        return f"{self.context}\n\n{self.human}".format(**kwargs)

class PromptStrategy(Enum):
    """
    Prompt strategys include:
    - QA: Question and Answer
    - CHAT: Chat
    - ANALYSIS: Analysis
    """
    QA = "qa"
    CHAT = "chat"
    ANALYSIS = "analysis"

class PromptGenerator:
    def __init__(self, strategy: PromptStrategy = PromptStrategy.QA):
        self.strategy = strategy
        self.templates = {
            PromptStrategy.QA: PromptTemplate(
                context=QUERY_PROMPT,
                human="User query: {query}\nPlease answer:"
            ),
            PromptStrategy.CHAT: PromptTemplate(
                context=QUERY_PROMPT,
                human="User query: {query}\nPlease answer:"
            ),
            PromptStrategy.ANALYSIS: PromptTemplate(
                context=QUERY_PROMPT,
                human="User query: {query}\nPlease answer:"
            )
        }
    
    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format context
        
        Args:
            documents: List of retrieved relevant documents
            
        Returns:
            str: Formatted context string
        """
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            content = doc.get("content", "").strip()
            title = doc.get("metadata", {}).get("source", "unknown")
            formatted_docs.append(f"[{i}] {content}\nSource: {title}")
        
        return "\n\n".join(formatted_docs)
    
    def generate(self, 
                query: str, 
                documents: List[Dict[str, Any]], 
                strategy: Optional[PromptStrategy] = None,
                max_relevance_score: float = 0.0) -> str:
        """
        Generate prompt
        
        Args:
            query: User query
            documents: List of retrieved relevant documents
            strategy: Optional prompt strategy
            max_relevance_score: Highest relevance score
        """
        strategy = strategy or self.strategy
        if DEBUG:
            print(f"\n[PromptGenerator] Using strategy: {strategy.value}")
            print(f"[PromptGenerator] User query: {query}")
            print(f"[PromptGenerator] Using {len(documents)} relevant documents to generate prompt")
            print(f"[PromptGenerator] Highest relevance score: {max_relevance_score:.3f}")
        
        if strategy not in self.templates:
            raise ValueError(f"Unsupported prompt strategy: {strategy}")
        
        relevance_note = ""
        if max_relevance_score < 0.5:
            relevance_note = (
                "Note: The retrieved reference material is not highly relevant to the question (only {:.1f}%). "
            ).format(max_relevance_score * 100)
        else:
            relevance_note = "The highest relevance score between the retrieved reference material and the question is {:.1f}%.".format(max_relevance_score * 100)
        
        template = self.templates[strategy]
        context = self._format_context(documents)
        
        prompt = template.format(
            query=query,
            context=context,
            relevance_note=relevance_note
        )
        
        if DEBUG:
            print(f"[PromptGenerator] Prompt generated, length: {len(prompt)} characters")
            print(prompt)
        return prompt 
