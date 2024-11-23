from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

@dataclass
class PromptTemplate:
    system: str
    human: str
    context: str
    
    def format(self, **kwargs) -> str:
        return f"{self.system}\n\n{self.context}\n\n{self.human}".format(**kwargs)

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
                system="你是一个专业的医疗助手。请基于提供的医学知识，准确、简洁地回答用户的问题。如果无法从给定信息中找到答案，请基于你的专业知识谨慎作答，并明确说明这是基于你的知识而非提供的参考资料。",
                context="相关医学知识：\n{context}\n\n相关度提示：{relevance_note}",
                human="用户问题：{query}\n请回答："
            ),
            PromptStrategy.CHAT: PromptTemplate(
                system="你是一个友好的医疗咨询助手。请用平易近人的语气，基于提供的医学知识与用户进行对话。注意理解用户的情感需求，给出专业且温暖的回应。如果参考资料相关度不高，请基于你的专业知识谨慎作答。",
                context="参考知识：\n{context}\n\n相关度提示：{relevance_note}",
                human="用户：{query}\n助手："
            ),
            PromptStrategy.ANALYSIS: PromptTemplate(
                system="你是一个专业的医学分析师。请基于提供的医学知识，对用户的问题进行深入分析。分析应包含多个角度，并给出合理的建议。如果参考资料相关度不高，请基于你的专业知识进行分析。",
                context="分析依据：\n{context}\n\n相关度提示：{relevance_note}",
                human="分析问题：{query}\n分析结果："
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
            formatted_docs.append(f"[{i}] {content}\n来源: {title}")
        
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
                "注意：检索到的参考资料与问题的相关度较低（{:.1f}%）。"
                "你可以基于自己的专业知识来回答，但请明确说明这部分回答来自你的知识储备。"
            ).format(max_relevance_score * 100)
        else:
            relevance_note = "其中，参考资料与问题的相关度最高为 {:.1f}%。".format(max_relevance_score * 100)
        
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

# TODO: Optimize more powerful prompts