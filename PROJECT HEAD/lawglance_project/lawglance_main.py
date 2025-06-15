# Necessary imports
import json
import os
import datetime
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import sent_tokenize
from word_processor import WordProcessor
from calendar_manager import CalendarManager
from communication_handler import CommunicationHandler
from research_enhancer import ResearchEnhancer
from auth_handler import AuthHandler
# New imports
from document_analyzer import DocumentAnalyzer
from concept_extractor import ConceptExtractor
from document_editor import DocumentEditor
from semantic_analyzer import SemanticAnalyzer

class Lawglance:
    """Handles the conversational RAG for legal queries with enhanced document understanding."""
    store = {}

    def __init__(self, llm, embeddings, vector_store, calendar_client_config=None, comm_creds=None, legal_db_url=None):
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.step_count = 0

        # Initialize components
        self.auth_handler = AuthHandler(calendar_client_config) if calendar_client_config else None
        self.calendar = CalendarManager() if calendar_client_config else None
        self.comm_handler = CommunicationHandler(**comm_creds) if comm_creds else None
        self.research = ResearchEnhancer(legal_db_url) if legal_db_url else None

        # Initialize enhanced document processing components
        self.word_processor = WordProcessor()
        
        # Download necessary NLTK resources if not already available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
            
        # Enhanced QA pipeline with deeper context understanding
        self.tokenizer = AutoTokenizer.from_pretrained("deepset/roberta-base-squad2")
        self.qa_model = AutoModelForQuestionAnswering.from_pretrained("deepset/roberta-base-squad2")
        self.qa_pipeline = pipeline("question-answering", model=self.qa_model, tokenizer=self.tokenizer)
        
        # New document analysis components
        self.doc_analyzer = DocumentAnalyzer(self.embeddings)
        self.concept_extractor = ConceptExtractor()
        self.doc_editor = DocumentEditor()
        self.semantic_analyzer = SemanticAnalyzer() # Initialize SemanticAnalyzer
        
        self.load_state()

    def __retriever(self, query):
        """Retrieve relevant documents based on the query."""
        print(f"[DEBUG] __retriever called with query: {query}")
        return self.vector_store.query(query, k=10, score_threshold=0.75)

    def llm_answer_generator(self, query):
        """Generate an answer using the LLM based on the query."""
        retriever = self.__retriever(query)
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        history_aware_retriever = create_history_aware_retriever(self.llm, retriever, contextualize_q_prompt)
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful legal assistant who is tasked with answering the following question based on the provided context: {input}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", """You are provided with some context containing legal contents that might include relevant sections or articles which can help you answer the question. Your task is to answer the question based on the context. Ensure that the answer is derived from the relevant parts of the context only.\n\nRelevant Context: \n{context}\n\nPlease return only the answer as output."""),
        ])
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        return create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Retrieve or create a chat history for the session."""
        if session_id not in Lawglance.store:
            Lawglance.store[session_id] = ChatMessageHistory()
        return Lawglance.store[session_id]

    def save_state(self):
        """Save current state to file with rotation and validation."""
        try:
            if os.path.exists('ai_state.json'):
                os.rename('ai_state.json', 'ai_state_prev.json')

            state = {
                'store': self.store,
                'step_count': self.step_count,
                'timestamp': datetime.datetime.now().isoformat(),
                'system_status': 'operational'
            }

            if not isinstance(state['step_count'], int) or state['step_count'] < 0:
                raise ValueError(f"Invalid step count: {state['step_count']}")
            if not isinstance(state['store'], dict):
                raise TypeError("Store must be a dictionary")

            with open('ai_state.tmp', 'w') as f:
                json.dump(state, f, indent=2)
            os.replace('ai_state.tmp', 'ai_state.json')

            print(f"State persisted successfully at {state['timestamp']}")

        except Exception as e:
            print(f"State preservation failed: {str(e)}")
            if os.path.exists('ai_state_prev.json'):
                os.rename('ai_state_prev.json', 'ai_state.json')
                print("Restored previous state file")

    def load_state(self):
        """Load and validate state from file with fallback."""
        try:
            if os.path.exists('ai_state.json'):
                with open('ai_state.json', 'r') as f:
                    state = json.load(f)

                required_fields = ['store', 'step_count', 'timestamp']
                if not all(field in state for field in required_fields):
                    raise ValueError("Missing required state fields")

                if not isinstance(state['store'], dict):
                    raise TypeError("Invalid store format")

                if not isinstance(state['step_count'], int) or state['step_count'] < 0:
                    raise ValueError(f"Invalid step count: {state['step_count']}")

                state_time = datetime.datetime.fromisoformat(state['timestamp'])
                if (datetime.datetime.now() - state_time).days > 7:
                    print("Warning: Loading state older than 7 days")

                self.store = state['store']
                self.step_count = state['step_count']
                print(f"Loaded valid state from {state['timestamp']}")
                print(f"[DEBUG] Loaded state: step_count = {self.step_count}, store size = {len(self.store)}")

            elif os.path.exists('ai_state_prev.json'):
                print("Loading from backup state")
                os.rename('ai_state_prev.json', 'ai_state.json')
                self.load_state()

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"State validation failed: {str(e)}")
            if os.path.exists('ai_state_prev.json'):
                print("Attempting backup load")
                os.rename('ai_state_prev.json', 'ai_state.json')
                self.load_state()

    def process_document(self, file_path, analyze=False):
        """Process a document and optionally perform deep analysis.
        
        Args:
            file_path: Path to the document
            analyze: If True, performs semantic analysis on the document
            
        Returns:
            Document content or analysis based on parameters
        """
        content = self.word_processor.read_document(file_path)
        
        if not analyze:
            return content
            
        # Perform deeper document analysis
        analysis = self.doc_analyzer.analyze(content)
        key_concepts = self.concept_extractor.extract_concepts(content)
        
        return {
            "content": content,
            "summary": analysis["summary"],
            "key_points": analysis["key_points"],
            "concepts": key_concepts,
            "complexity_score": analysis["complexity_score"],
            "document_type": analysis["document_type"]
        }

    def edit_document(self, file_path, instructions):
        """Edit a document based on natural language instructions.
        
        Args:
            file_path: Path to the document
            instructions: Natural language description of edits to perform
            
        Returns:
            Status message indicating edits performed
        """
        return self.doc_editor.edit_document(file_path, instructions)
        
    def compare_documents(self, doc_path1, doc_path2):
        """Compare two legal documents and identify similarities and differences.
        
        Args:
            doc_path1: Path to first document
            doc_path2: Path to second document
            
        Returns:
            Comparison analysis
        """
        content1 = self.word_processor.read_document(doc_path1)
        content2 = self.word_processor.read_document(doc_path2)
        
        return self.doc_analyzer.compare_documents(content1, content2)
        
    def extract_legal_entities(self, document_content):
        """Extract legal entities from document content.
        
        Args:
            document_content: Text content of the document
            
        Returns:
            Dictionary of extracted legal entities by category
        """
        return self.doc_analyzer.extract_legal_entities(document_content)
        
    def generate_answer(self, context, question):
        """Generate an answer using the AI model based on the context and question.
        
        Enhanced to handle longer contexts by chunking and synthesizing responses.
        """
        max_length = 512  # Standard context length limit
        if len(context) <= max_length:
            result = self.qa_pipeline(question=question, context=context)
            return result['answer']
            
        # For long documents, split into chunks with overlap
        sentences = sent_tokenize(context)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length - 100:  # Leave room for overlap
                current_chunk += " " + sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence  # Start new chunk with current sentence
                
        if current_chunk:  # Add the last chunk
            chunks.append(current_chunk)
            
        # Get answers from each chunk
        answers = []
        confidence_scores = []
        
        for chunk in chunks:
            result = self.qa_pipeline(question=question, context=chunk)
            answers.append(result['answer'])
            confidence_scores.append(result['score'])
            
        # Return best answer or synthesize a composite answer
        best_idx = confidence_scores.index(max(confidence_scores))
        return answers[best_idx]

    def conversational(self, query):
        """Handle conversational queries with enhanced document capabilities."""
        # Research enhancement
        if "research" in query.lower() and self.research:
            research_summary = self.research.enhance(query)
            query = f"{query}\nAdditional research context: {research_summary}"

        # Calendar functionality
        if 'connect calendar' in query.lower() and self.auth_handler:
            self.auth_handler.start_server()
            return f"Please visit: {self.auth_handler.get_auth_url()}"

        if 'schedule' in query.lower() or 'meeting' in query.lower():
            return self._handle_calendar_request(query)

        # Enhanced document processing capabilities
        if 'process document' in query.lower():
            analyze = 'analyze' in query.lower()
            file_path = query.split()[-1]  # Assuming file path is the last word in the query
            return self.process_document(file_path, analyze)
            
        if 'edit document' in query.lower():
            parts = query.split(' edit document ')
            if len(parts) == 2:
                instructions = parts[1]
                file_path = instructions.split()[0]
                edit_instructions = ' '.join(instructions.split()[1:])
                return self.edit_document(file_path, edit_instructions)
            
        if 'compare documents' in query.lower():
            parts = query.lower().split('compare documents')
            if len(parts) == 2:
                doc_paths = parts[1].strip().split(' and ')
                if len(doc_paths) == 2:
                    return self.compare_documents(doc_paths[0].strip(), doc_paths[1].strip())
            
        if 'extract entities from' in query.lower():
            file_path = query.split()[-1]
            content = self.word_processor.read_document(file_path)
            return self.extract_legal_entities(content)

        if 'generate answer' in query.lower():
            parts = query.split('|')
            if len(parts) == 3:
                context, question = parts[1], parts[2]
                return self.generate_answer(context, question)

        if 'extract arguments from' in query.lower():
            file_path = query.split()[-1]
            content = self.word_processor.read_document(file_path)
            return self.semantic_analyzer.extract_legal_arguments(content)

        # Default RAG conversation handling
        rag_chain = self.llm_answer_generator(query)
        self.step_count += 1
        if self.step_count % 3 == 0:
            self.save_state()

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )
        response = conversational_rag_chain.invoke(
            {"input": query},
            config={"configurable": {"session_id": "abc123"}},
        )
        return response['answer']

    def _handle_calendar_request(self, query):
        """Handle calendar-related queries."""
        if not self.calendar:
            return "Calendar integration not configured"

        if 'list' in query.lower():
            events = self.calendar.list_events()
            return "\n".join([e['summary'] for e in events[:5]]) or "No upcoming events"

        if 'create' in query.lower():
            time_str = " ".join(query.split()[-3:])
            try:
                event_time = datetime.datetime.strptime(time_str, "%B %d %Y")
                self.calendar.create_event("Legal Meeting", event_time)
                return f"Meeting scheduled for {event_time.strftime('%b %d %Y')}"
            except ValueError as ve:
                print(f"[DEBUG] Calendar create event failed: {ve} for query segment: {time_str}")
                return "Could not parse time. Please use format 'Month Day Year'"

        print(f"[DEBUG] Calendar request not understood: {query}")
        return "Calendar request not understood"

    def finalize_auth(self):
        """Finalize the authentication process."""
        if self.auth_handler and self.auth_handler.auth_code:
            token_info = self.auth_handler.exchange_code()
            self.calendar.save_credentials(token_info)
            return "Calendar connected successfully"
        return "No pending authentication"
