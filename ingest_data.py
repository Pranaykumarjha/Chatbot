import chromadb
import cohere
from dotenv import load_dotenv
import os
import PyPDF2
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

def extract_text_from_pdf(pdf_file_path):
    """
    Extracts text from a PDF file using PyPDF2.
    """
    text = ""
    with open(pdf_file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Step 1: Extract text from PDF
pdf_path = "Competitive Programmer's Handbook.pdf"
pdf_text = extract_text_from_pdf(pdf_path)

# Step 2: Split the text into smaller, manageable chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Each chunk will have up to 500 characters
    chunk_overlap=100 # Chunks will overlap by 100 characters to maintain context
)
docs = text_splitter.create_documents([pdf_text])

# Step 3: Generate embeddings for each chunk and store in ChromaDB
client = chromadb.PersistentClient()

# It's crucial to delete the old collection before re-ingesting with new chunks
try:
    client.delete_collection(name="rag_collection_pdfs")
    print("Old collection deleted to prevent dimension mismatch.")
except Exception:
    pass # Ignore if the collection doesn't exist

collection = client.get_or_create_collection(name="rag_collection_pdfs")

print(f"Ingesting {len(docs)} chunks into ChromaDB...")
for i, doc in enumerate(docs):
    embedding = co.embed(
        texts=[doc.page_content],
        model="embed-english-v3.0",
        input_type="search_document"
    ).embeddings[0]

    collection.add(
        ids=[f"doc_{i}"],
        documents=[doc.page_content],
        embeddings=[embedding]
    )
    if (i + 1) % 10 == 0:
        print(f"Ingested {i + 1}/{len(docs)} chunks.")

print("\nIngestion complete. ChromaDB collection 'rag_collection_pdfs' is ready!")
