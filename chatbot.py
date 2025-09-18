import chromadb
import cohere
from dotenv import load_dotenv
import os

# --- 1. Load your API keys ---
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")
if api_key:
    api_key = api_key.strip()
else:
    print("Error: COHERE_API_KEY not found in .env file.")
    exit()

co = cohere.Client(api_key)

# --- 2. Session Management Code ---
# A simple dictionary to act as our in-memory database
chat_history_db = {}

def add_to_history(session_id, user_message, bot_response):
    """
    Adds a new message pair to a user's chat history.
    """
    if session_id not in chat_history_db:
        chat_history_db[session_id] = []
    
    # Store messages in the format expected by the Cohere Chat API
    chat_history_db[session_id].append({"role": "User", "message": user_message})
    chat_history_db[session_id].append({"role": "Chatbot", "message": bot_response})

def get_history(session_id):
    """
    Retrieves the entire chat history for a given session ID.
    """
    history = chat_history_db.get(session_id, [])
    # Convert our internal history format to the API's format
    return [{"role": turn['role'].upper(), "text": turn['message']} for turn in history]

# --- 3. Retrieval and Generation Logic ---
def get_response(user_input, session_id):
    # A. Retrieve past conversation from our session manager
    conversation_history = get_history(session_id)
    
    # B. Prepare the RAG context from ChromaDB
    # --- Connect to ChromaDB
    try:
        client = chromadb.PersistentClient()
        collection = client.get_collection(name="rag_collection_pdfs")
    except Exception as e:
        return f"Error connecting to ChromaDB: {e}"

    # --- Use Cohere to get the embedding for the user's question
    user_query_embedding = co.embed(
        texts=[user_input],
        model="embed-english-v3.0",
        input_type="search_query"
    ).embeddings[0]

    # --- Query the collection for the most relevant documents
    results = collection.query(
        query_embeddings=[user_query_embedding],
        n_results=3
    )
    
    # --- Correctly format the retrieved documents for the Cohere chat API
    formatted_documents = []
    if results['documents'] and results['documents'][0]:
        for i, doc_text in enumerate(results['documents'][0]):
            formatted_documents.append({"snippet": doc_text})
    
    # D. Prepare the preamble (system prompt) for the LLM
    preamble_prompt = """
    You are an expert tutor on the topics provided in the documents.
    Use the following retrieved documents and chat history to answer the user's question accurately and thoroughly.
    If the provided documents don't contain enough information to answer the question, state that you cannot answer from the given context.
    Do not use any external knowledge.
    """
    
    # E. Call the Cohere chat endpoint with the prepared prompt and documents
    response = co.chat(
        model="command-r",
        message=user_input,
        chat_history=conversation_history,
        preamble=preamble_prompt,
        documents=formatted_documents, # Correctly pass the formatted documents
    )

    bot_response = response.text
    
    # F. Add the new turn to the history
    add_to_history(session_id, user_input, bot_response)

    return bot_response

# --- 4. Main Chatbot Loop (the user interface) ---
if __name__ == "__main__":
    session_id = "user1" # A unique ID for this chat session
    print("Welcome to your RAG-powered chatbot. Type 'exit' to quit.")
    
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        
        # Get the response using our full logic
        response = get_response(user_message, session_id)
        print("Chatbot:", response)
