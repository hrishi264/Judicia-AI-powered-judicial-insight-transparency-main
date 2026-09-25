import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# CHANGE: Using Local HuggingFace Embeddings instead of Google
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Define paths
DATA_FOLDER = "data"
VECTOR_STORE_PATH = os.path.join(DATA_FOLDER, "vector_store")
LAWS_FILE = os.path.join(DATA_FOLDER, "laws.txt")
PRECEDENTS_FILE = os.path.join(DATA_FOLDER, "precedents.txt")

# Setup Embeddings (LOCAL - No API Key needed for this part)
# This downloads a small, fast model (all-MiniLM-L6-v2) to your machine.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vector_store():
    """
    Reads laws.txt and precedents.txt, chunks them, and builds a FAISS index.
    Run this ONCE to create the 'database'.
    """
    print("🔄 Building Vector Store from dummy data...")
    
    docs = []
    
    # Load Laws
    if os.path.exists(LAWS_FILE):
        try:
            loader = TextLoader(LAWS_FILE, encoding='utf-8')
            docs.extend(loader.load())
            print(f"   - Loaded {LAWS_FILE}")
        except Exception as e:
            print(f"   ⚠️ Error loading laws.txt: {e}")

    # Load Precedents
    if os.path.exists(PRECEDENTS_FILE):
        try:
            loader = TextLoader(PRECEDENTS_FILE, encoding='utf-8')
            docs.extend(loader.load())
            print(f"   - Loaded {PRECEDENTS_FILE}")
        except Exception as e:
             print(f"   ⚠️ Error loading precedents.txt: {e}")

    if not docs:
        print("❌ No documents found. Vector store not created.")
        return

    # Split text into chunks (Recursive is better for context)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    split_docs = text_splitter.split_documents(docs)

    # Create Vector Store
    try:
        vector_store = FAISS.from_documents(split_docs, embeddings)
        # Save to disk
        vector_store.save_local(VECTOR_STORE_PATH)
        print(f"✅ Vector Store saved to: {VECTOR_STORE_PATH}")
    except Exception as e:
        print(f"❌ Error creating vector store: {e}")

def get_retriever():
    """
    Loads the saved Vector Store and returns a retriever interface.
    """
    if not os.path.exists(VECTOR_STORE_PATH):
        print("⚠️ Vector Store not found. Building it now...")
        build_vector_store()
    
    # Allow dangerous deserialization is required for local files
    vector_store = FAISS.load_local(
        VECTOR_STORE_PATH, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    return vector_store.as_retriever(search_kwargs={"k": 3})

if __name__ == "__main__":
    build_vector_store()