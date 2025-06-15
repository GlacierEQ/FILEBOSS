"""LawGlance main implementation file."""
from typing import List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, BaseMessage, AIMessage

class Lawglance:
    """Main class for the LawGlance application."""
    
    def __init__(self, llm, embeddings, vector_store, max_history: int = 10):
        """
        Initialize LawGlance with language model, embeddings, and vector store.
        
        Args:
            llm: Language model for generating responses
            embeddings: Embeddings for vector search
            vector_store: Vector database for document retrieval
            max_history: Maximum number of messages to keep in chat history
        """
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.chat_history: List[BaseMessage] = []
        self.max_history = max_history
        
        # Create retriever
        self.retriever = vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
        
        # Create conversational prompt template
        self.LEGAL_TEMPLATE = """
        You are a helpful legal assistant named LawGlance. 
        Use the following pieces of retrieved legal context to answer the question.
        If you don't know the answer, just say that you don't know. 
        Don't try to make up an answer.
        Try to include citations to relevant legal sources when possible.
        
        Context: {context}
        
        Chat History: {chat_history}
        
        Question: {question}
        """
        
        self.prompt = ChatPromptTemplate.from_template(self.LEGAL_TEMPLATE)
    
    def _manage_history(self) -> None:
        """Ensure chat history doesn't exceed max_history."""
        if len(self.chat_history) > self.max_history * 2:  # *2 because each exchange has 2 messages
            # Keep only the most recent exchanges
            self.chat_history = self.chat_history[-self.max_history*2:]
        
    def conversational(self, query: str) -> str:
        """
        Process a conversational query.
        
        Args:
            query: User's question
            
        Returns:
            Response from the language model
        """
        # Get relevant documents from the retriever
        retrieved_docs = self.retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Format chat history
        formatted_chat_history = "\n".join(
            [f"{msg.type}: {msg.content}" for msg in self.chat_history]
        )
        
        # Create the response
        response = self.llm.invoke(
            self.prompt.format(
                context=context, 
                chat_history=formatted_chat_history,
                question=query
            )
        )
        
        # Add to chat history
        self.chat_history.append(HumanMessage(content=query))
        self.chat_history.append(response)
        
        # Manage history size
        self._manage_history()
        
        return response.content
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.chat_history = []
