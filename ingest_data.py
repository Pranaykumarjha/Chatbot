import chromadb
import cohere
from dotenv import load_dotenv
import os
import PyPDF2
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- 1. Load API keys and connect to Cohere ---
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")
if api_key:
    api_key = api_key.strip()
else:
    print("Error: COHERE_API_KEY not found in .env file.")
    exit()

co = cohere.Client(api_key)

# --- 2. PDF text extraction ---
def extract_text_from_pdf(pdf_file_path):
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    with open(pdf_file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

pdf_path = "CS3451-INTRODUCTION TO OPERATING SYSTEM-1807676842-Unit-I - Introduction (1).pdf"
pdf_text = extract_text_from_pdf(pdf_path)

# --- 3. Split text into chunks ---
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,   # Increase if you want fewer chunks
    chunk_overlap=100
)
docs = text_splitter.create_documents([pdf_text])

# --- 3a. Optional: quick test ingestion ---
# docs = docs[:50]  # Uncomment this line to ingest only first 50 chunks for testing

# --- 4. Set up ChromaDB ---
client = chromadb.PersistentClient()

try:
    client.delete_collection(name="rag_collection_pdfs")
    print("Old collection deleted to prevent dimension mismatch.")
except Exception:
    pass  # ignore if doesn't exist

collection = client.get_or_create_collection(name="rag_collection_pdfs")

# --- 5. Batch embedding ingestion with trial key limits ---
batch_size = 10  # Trial key: 40 requests/min → 10 per batch safe
total = len(docs)
print(f"Ingesting {total} chunks into ChromaDB in batches of {batch_size}...")

for i in range(0, total, batch_size):
    batch_docs = docs[i:i+batch_size]
    texts = [doc.page_content for doc in batch_docs]

    # Embed batch
    try:
        embeddings = co.embed(
            texts=texts,
            model="embed-english-v3.0",
            input_type="search_document"
        ).embeddings
    except cohere.errors.TooManyRequestsError:
        print("Rate limit hit. Waiting 60 seconds before retrying...")
        time.sleep(60)
        embeddings = co.embed(
            texts=texts,
            model="embed-english-v3.0",
            input_type="search_document"
        ).embeddings

    # Add embeddings to ChromaDB
    for j, embedding in enumerate(embeddings):
        collection.add(
            ids=[f"doc_{i+j}"],
            documents=[texts[j]],
            embeddings=[embedding]
        )

    print(f"Ingested {min(i+batch_size, total)}/{total} chunks...")
    time.sleep(1)  # small delay to avoid hitting rate limit too fast

print("\nIngestion complete. ChromaDB collection 'rag_collection_pdfs' is ready!")
