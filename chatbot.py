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

# --- 2. Session Management ---
chat_history_db = {}

def add_to_history(session_id, user_message, bot_response):
    if session_id not in chat_history_db:
        chat_history_db[session_id] = []
    chat_history_db[session_id].append({"role": "User", "message": user_message})
    chat_history_db[session_id].append({"role": "Chatbot", "message": bot_response})

def get_history(session_id):
    history = chat_history_db.get(session_id, [])
    return [{"role": turn['role'].upper(), "text": turn['message']} for turn in history]

# --- 3. RAG Retrieval and Response ---
def get_response(user_input, session_id):
    conversation_history = get_history(session_id)

    # Connect to ChromaDB
    try:
        client = chromadb.PersistentClient()
        collection = client.get_collection(name="rag_collection_pdfs")
    except Exception as e:
        return f"Error connecting to ChromaDB: {e}"

    # Embed user query
    user_query_embedding = co.embed(
        texts=[user_input],
        model="embed-english-v3.0",
        input_type="search_query"
    ).embeddings[0]

    # Retrieve top 3 relevant chunks
    results = collection.query(
        query_embeddings=[user_query_embedding],
        n_results=3
    )

    # Format retrieved docs for Cohere chat
    formatted_documents = []
    if results['documents'] and results['documents'][0]:
        for doc_text in results['documents'][0]:
            formatted_documents.append({"snippet": doc_text})

    # --- System preamble ---
    preamble_prompt = """
    You are an expert tutor on the topics provided in the documents.
    Use the following retrieved documents and chat history to answer the user's question accurately and thoroughly.
    If the documents don't contain enough information, you may also use your general knowledge to answer the question completely.
    When giving multiple points, always format them as bullet points, each on a separate line starting with "* ".
    """

    # --- Get Cohere response ---
    response = co.chat(
        model="command-xlarge-nightly",
        message=user_input,
        chat_history=conversation_history,
        preamble=preamble_prompt,
        documents=formatted_documents
    )

    bot_response = response.text

    # --- Post-process: ensure each bullet is on its own line ---
    if "*" in bot_response:
        bot_response = bot_response.replace("* ", "\n* ").strip()
    bot_response = "\n".join([line for line in bot_response.split("\n") if line.strip() != ""])

    # --- Save to session ---
    add_to_history(session_id, user_input, bot_response)

    return bot_response

# --- 4. Chat Loop ---
if __name__ == "__main__":
    session_id = "user1"
    print("Welcome to your RAG-powered chatbot. Type 'exit' to quit.")

    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break

        response = get_response(user_message, session_id)
        print("Chatbot:", response)
