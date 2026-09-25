import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Define paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
VECTOR_STORE_PATH = os.path.join(DATA_FOLDER, "vector_store")
LAWS_FILE = os.path.join(DATA_FOLDER, "laws.txt")
PRECEDENTS_FILE = os.path.join(DATA_FOLDER, "precedents.txt")

# Setup Embeddings (LOCAL - No API Key needed)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vector_store():
    """
    Reads laws.txt and precedents.txt, chunks them, and builds a FAISS index.
    Run this ONCE to create the 'database'.
    """
    print("🔄 Building Vector Store from legal documents...")
    print(f"   Data folder: {DATA_FOLDER}")
    
    docs = []
    
    # Load Laws
    if os.path.exists(LAWS_FILE):
        try:
            loader = TextLoader(LAWS_FILE, encoding='utf-8')
            docs.extend(loader.load())
            print(f"   ✅ Loaded {LAWS_FILE}")
        except Exception as e:
            print(f"   ⚠️ Error loading laws.txt: {e}")
    else:
        print(f"   ❌ laws.txt not found at: {LAWS_FILE}")

    # Load Precedents
    if os.path.exists(PRECEDENTS_FILE):
        try:
            loader = TextLoader(PRECEDENTS_FILE, encoding='utf-8')
            docs.extend(loader.load())
            print(f"   ✅ Loaded {PRECEDENTS_FILE}")
        except Exception as e:
            print(f"   ⚠️ Error loading precedents.txt: {e}")
    else:
        print(f"   ❌ precedents.txt not found at: {PRECEDENTS_FILE}")

    if not docs:
        print("❌ No documents found. Vector store not created.")
        print(f"   Make sure laws.txt and precedents.txt exist in: {DATA_FOLDER}")
        return

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    split_docs = text_splitter.split_documents(docs)
    print(f"   📄 Split into {len(split_docs)} chunks")

    # Create Vector Store
    try:
        # Ensure vector_store directory exists
        os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
        
        vector_store = FAISS.from_documents(split_docs, embeddings)
        
        # Save to disk
        vector_store.save_local(VECTOR_STORE_PATH)
        print(f"✅ Vector Store saved to: {VECTOR_STORE_PATH}")
        print(f"   Total documents indexed: {len(split_docs)}")
    except Exception as e:
        print(f"❌ Error creating vector store: {e}")

def get_retriever():
    """
    Loads the saved Vector Store and returns a retriever interface.
    """
    if not os.path.exists(VECTOR_STORE_PATH):
        print("⚠️ Vector Store not found. Building it now...")
        build_vector_store()
    
    try:
        vector_store = FAISS.load_local(
            VECTOR_STORE_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        return vector_store.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        print(f"❌ Error loading vector store: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏗️  BUILDING VECTOR DATABASE")
    print("="*60 + "\n")
    
    build_vector_store()
    
    print("\n" + "="*60)
    print("✅ VECTOR DATABASE BUILD COMPLETE")
    print("="*60 + "\n")