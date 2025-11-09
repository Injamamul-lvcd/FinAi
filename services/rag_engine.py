"""
RAG Query Engine for generating context-aware responses.

This module provides the RAGQueryEngine class that orchestrates retrieval
of relevant document chunks, prompt construction with conversation history,
and response generation using Google Gemini LLM.
"""

import logging
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from services.vector_store import VectorStoreManager
from services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class RAGQueryEngine:
    """
    Orchestrates the RAG pipeline for query processing.
    
    Retrieves relevant context from vector store, constructs prompts with
    conversation history, and generates responses using Google Gemini LLM.
    """
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        session_manager: SessionManager,
        google_api_key: str,
        embedding_model_name: str = "models/text-embedding-004",
        chat_model_name: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_k: int = 5
    ):
        """
        Initialize the RAG Query Engine.
        
        Args:
            vector_store: VectorStoreManager instance for similarity search
            session_manager: SessionManager instance for conversation history
            google_api_key: Google API key for Gemini models
            embedding_model_name: Name of the embedding model
            chat_model_name: Name of the chat model
            temperature: Temperature for LLM generation (0.0-2.0)
            max_tokens: Maximum tokens for LLM response
            top_k: Number of chunks to retrieve for context
        """
        self.vector_store = vector_store
        self.session_manager = session_manager
        self.top_k = top_k
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configure Google Gemini API
        genai.configure(api_key=google_api_key)
        
        # Initialize embedding model
        self.embedding_model_name = embedding_model_name
        
        # Initialize chat model
        self.chat_model = genai.GenerativeModel(chat_model_name)
        
        logger.info(
            f"RAGQueryEngine initialized with chat_model={chat_model_name}, "
            f"embedding_model={embedding_model_name}, top_k={top_k}"
        )
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text query.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model_name,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def retrieve_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve top K relevant chunks from vector store based on query.
        
        Args:
            query: User query text
            
        Returns:
            List of dictionaries containing:
                - id: Chunk identifier
                - document: Text content
                - metadata: Associated metadata (document_id, filename, etc.)
                - distance: Similarity distance
                
        Raises:
            Exception: If retrieval fails
        """
        try:
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            # Perform similarity search
            results = self.vector_store.similarity_search(
                query_embedding=query_embedding,
                top_k=self.top_k
            )
            
            logger.info(f"Retrieved {len(results)} chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            raise
    
    def construct_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]],
        history: List[Dict[str, str]]
    ) -> str:
        """
        Construct prompt combining system instructions, context, history, and query.
        
        Args:
            query: User query text
            context: List of retrieved document chunks
            history: Conversation history (list of role/content dicts)
            
        Returns:
            str: Formatted prompt for LLM
        """
        # System instructions
        system_prompt = """You are a helpful financial assistant. Your role is to provide accurate, 
context-aware answers to financial questions based on the provided documents.

Guidelines:
- Answer questions based ONLY on the provided context from financial documents
- If the context doesn't contain enough information to answer the question, clearly state that
- Be concise and professional in your responses
- Cite specific information from the documents when relevant
- If asked about topics not covered in the documents, politely indicate the limitation
"""
        
        # Build context section
        context_section = "\n\n=== RELEVANT FINANCIAL DOCUMENTS ===\n"
        if context:
            for i, chunk in enumerate(context, 1):
                filename = chunk.get('metadata', {}).get('filename', 'Unknown')
                text = chunk.get('document', '')
                context_section += f"\n[Document {i}: {filename}]\n{text}\n"
        else:
            context_section += "\nNo relevant documents found.\n"
        
        # Build conversation history section
        history_section = ""
        if history:
            history_section = "\n\n=== CONVERSATION HISTORY ===\n"
            for msg in history:
                role = msg['role'].upper()
                content = msg['content']
                history_section += f"\n{role}: {content}\n"
        
        # Build final prompt
        prompt = f"""{system_prompt}
{context_section}
{history_section}

=== CURRENT QUESTION ===
{query}

Please provide a helpful answer based on the context above."""
        
        return prompt
    
    def query(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Process a user query and generate a response using RAG pipeline.
        
        Args:
            user_query: The user's question
            session_id: Optional session ID for conversation continuity
            max_retries: Maximum number of retry attempts for LLM failures
            
        Returns:
            Dictionary containing:
                - response: Generated answer text
                - sources: List of source documents used
                - session_id: Session identifier (created if not provided)
                
        Raises:
            Exception: If query processing fails after retries
        """
        logger.info(f"Processing query with session_id={session_id}")
        
        # Create or validate session
        if session_id is None:
            session_id = self.session_manager.create_session()
            logger.info(f"Created new session: {session_id}")
        elif not self.session_manager.session_exists(session_id):
            logger.warning(f"Session {session_id} not found, creating new session")
            session_id = self.session_manager.create_session()
        
        try:
            # Step 1: Retrieve relevant context
            context_chunks = self.retrieve_context(user_query)
            
            # Step 2: Get conversation history
            history = self.session_manager.get_history(session_id, limit=5)
            
            # Step 3: Check if we have sufficient context
            if not context_chunks:
                logger.warning("No relevant context found for query")
                fallback_response = (
                    "I apologize, but I don't have enough information in the available "
                    "financial documents to answer your question. Please try rephrasing "
                    "your question or upload relevant documents."
                )
                
                # Store the interaction
                self.session_manager.add_message(session_id, 'user', user_query)
                self.session_manager.add_message(session_id, 'assistant', fallback_response)
                
                return {
                    'response': fallback_response,
                    'sources': [],
                    'session_id': session_id
                }
            
            # Step 4: Construct prompt
            prompt = self.construct_prompt(user_query, context_chunks, history)
            
            # Step 5: Generate response with retry logic
            response_text = None
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Generating response (attempt {attempt + 1}/{max_retries + 1})")
                    
                    response = self.chat_model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_tokens
                        )
                    )
                    
                    response_text = response.text
                    logger.info("Response generated successfully")
                    break
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries:
                        continue
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")
                        raise Exception(f"Failed to generate response after {max_retries + 1} attempts: {last_error}")
            
            # Step 6: Extract source information
            sources = []
            seen_docs = set()
            for chunk in context_chunks:
                metadata = chunk.get('metadata', {})
                doc_id = metadata.get('document_id', 'unknown')
                
                # Avoid duplicate sources
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    sources.append({
                        'document_id': doc_id,
                        'filename': metadata.get('filename', 'Unknown'),
                        'chunk_text': chunk.get('document', '')[:200] + '...',  # Preview
                        'relevance_score': 1.0 - chunk.get('distance', 0.0)  # Convert distance to score
                    })
            
            # Step 7: Store conversation in session
            self.session_manager.add_message(session_id, 'user', user_query)
            self.session_manager.add_message(session_id, 'assistant', response_text)
            
            logger.info(f"Query processed successfully with {len(sources)} sources")
            
            return {
                'response': response_text,
                'sources': sources,
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise
