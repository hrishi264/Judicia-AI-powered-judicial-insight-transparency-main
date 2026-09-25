"""
JUDICIAL AI BACKEND – FULL WORKING VERSION
========================================
• LLaMA 3.1 via Ollama (Local)
• RAG with FAISS
• Multi-Agent Reasoning
• Web Research (Gemini + DuckDuckGo)
• Compatible with existing agents.py
"""

import os
import io
import sys
import re
import json
import PyPDF2
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage

# --------------------------------------------------
# BASIC SETUP
# --------------------------------------------------
# Fix Windows console encoding (cp1252 can't handle Unicode emojis)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv()

from agents import MultiAgentOrchestrator
from database import engine, SessionLocal, get_db
from models import Judgment, Analysis

# --------------------------------------------------
# OLLAMA (LOCAL LLM)
# --------------------------------------------------
llm = None
try:
    llm = ChatOllama(
        model="llama3.1",
        temperature=0.3,
        base_url="http://localhost:11434"
    )
    llm.invoke([HumanMessage(content="ping")])
    print("✅ Ollama LLaMA 3.1 connected")
except Exception as e:
    print("❌ Ollama not running:", e)

# --------------------------------------------------
# GEMINI (CLOUD LLM)
# --------------------------------------------------
gemini_llm = None
if os.getenv("GOOGLE_API_KEY"):
    try:
        gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        print("✅ Gemini connected")
    except Exception as e:
        print("⚠️ Gemini error:", e)
else:
    print("⚠️ GOOGLE_API_KEY missing – web search disabled")

# --------------------------------------------------
# WEB SEARCH
# --------------------------------------------------
search_tool = DuckDuckGoSearchResults(max_results=5)

# --------------------------------------------------
# VECTOR DB (RAG)
# --------------------------------------------------
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
VECTOR_PATH = os.path.join(BASE_DIR, "../data/vector_store")

vector_db = None
if os.path.exists(VECTOR_PATH):
    try:
        vector_db = FAISS.load_local(
            VECTOR_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("✅ Vector DB loaded")
    except Exception as e:
        print("⚠️ Vector DB error:", e)

# --------------------------------------------------
# DATA MODELS
# --------------------------------------------------
class WebQuery(BaseModel):
    query: str

class ChatRequest(BaseModel):
    question: str
    judgment_text: str

class AnalyzeResponse(BaseModel):
    filename: str
    summary: Optional[str] = None
    laws: Optional[str] = None
    analysis: Optional[str] = None
    web_sources: List[dict] = []
    justice_score: Optional[dict] = None
    timeline: Optional[dict] = None
    extracted_text: Optional[str] = None

class HistoryItem(BaseModel):
    id: int
    filename: str
    upload_date: str
    summary_snippet: Optional[str] = None

    model_config = {"from_attributes": True}

class HistoryDetail(BaseModel):
    id: int
    filename: str
    upload_date: str
    summary: Optional[str] = None
    laws: Optional[str] = None
    analysis: Optional[str] = None
    web_sources: list = []
    justice_score: Optional[dict] = None
    timeline: Optional[dict] = None

    model_config = {"from_attributes": True}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def extract_text_from_pdf(data: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text[:10000]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF file")

def extract_urls(raw: str) -> list:
    urls = re.findall(r'https?://[^\s,\]\'"]+', raw)
    cleaned = []
    for u in urls:
        u = re.sub(r'[,\]\)\}\'\"]$', '', u)
        if u.startswith("http") and len(u) > 20:
            cleaned.append(u)
    return cleaned[:5]

# --------------------------------------------------
# 🔥 WEB SEARCH FUNCTION (FIXED FORMAT)
# --------------------------------------------------
def web_search(query: str):
    """
    MUST return:
    {
      "answer": str,
      "sources": [
         {"title": str, "url": str, "snippet": str}
      ]
    }
    """
    if not gemini_llm:
        return {
            "answer": "Web research unavailable (Gemini not configured)",
            "sources": []
        }

    raw_results = search_tool.run(query)
    urls = extract_urls(str(raw_results))

    if not urls:
        return {
            "answer": "No reliable web sources found",
            "sources": []
        }

    # ✅ FIX: sources are DICTIONARIES (not strings)
    sources = []
    for i, url in enumerate(urls):
        sources.append({
            "title": f"Legal Source {i+1}",
            "url": url,
            "snippet": "Relevant legal precedent from web research"
        })

    prompt = f"""
You are a legal research assistant.

Query:
{query}

Sources:
{chr(10).join([s['url'] for s in sources])}

Provide a concise legal analysis (2 paragraphs).
"""

    response = gemini_llm.invoke(prompt)

    return {
        "answer": response.content.strip(),
        "sources": sources
    }

# --------------------------------------------------
# MULTI-AGENT SYSTEM
# --------------------------------------------------
multi_agent = None
if llm:
    try:
        multi_agent = MultiAgentOrchestrator(
            llm=llm,
            web_search_function=web_search   # ✅ WORKING
        )
        print("✅ Multi-Agent initialized (with Web Search)")
    except Exception as e:
        print("❌ Multi-Agent failed:", e)

# --------------------------------------------------
# CORE ANALYSIS
# --------------------------------------------------
def run_analysis(text: str):
    context = ""
    if vector_db:
        docs = vector_db.similarity_search(text, k=3)
        context = "\n".join(d.page_content for d in docs)

    if not multi_agent:
        return {
            "summary": "LLM not active — please ensure Ollama is running with llama3.1 loaded.",
            "analysis": "",
            "laws": "",
            "web_sources": []
        }

    return multi_agent.run(
        judgment_text=text,
        rag_context=context
    )

# --------------------------------------------------
# LIFESPAN (replaces deprecated @app.on_event)
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("\n🚀 JUDICIAL AI BACKEND READY (FULLY WORKING)")
    print("   Open /docs for API testing")
    print("   Share ngrok link with judges\n")
    yield
    # Shutdown
    print("👋 Backend shutting down")

# --------------------------------------------------
# FASTAPI
# --------------------------------------------------
app = FastAPI(
    title="Judicial AI Backend",
    version="2.3.0",
    description="AI-powered legal judgment analysis platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    # TODO: Restrict to specific origins in production
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    data = await file.read()
    text = extract_text_from_pdf(data)
    result = run_analysis(text)

    # Persist to database
    try:
        judgment = Judgment(filename=file.filename)
        db.add(judgment)
        db.flush()

        analysis = Analysis(
            judgment_id=judgment.id,
            summary=result.get("summary", ""),
            laws=result.get("laws", ""),
            analysis_content=result.get("analysis", ""),
            web_research=result.get("web_research", ""),
            web_sources=json.dumps(result.get("web_sources", []))
        )
        db.add(analysis)
        db.commit()
        print(f"💾 Saved analysis for: {file.filename}")
    except Exception as e:
        db.rollback()
        print(f"⚠️ DB save failed (analysis still returned): {e}")

    return {
        "filename": file.filename,
        "summary": result.get("summary"),
        "laws": result.get("laws"),
        "analysis": result.get("analysis"),
        "web_sources": result.get("web_sources", []),
        "justice_score": result.get("justice_score"),
        "timeline": result.get("timeline"),
        "extracted_text": text,
    }

@app.post("/web-search")
def manual_web_search(query: WebQuery):
    return web_search(query.query)

@app.post("/chat")
def chat_with_judgment(req: ChatRequest):
    """Chat with a judgment document using AI."""
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not available. Ensure Ollama is running.")

    prompt = f"""You are a legal assistant. Answer the user's question based ONLY on the judgment text provided.
Be concise, accurate, and use simple language that a non-lawyer can understand.
If the answer is not found in the judgment, say so clearly.

JUDGMENT TEXT:
{req.judgment_text[:6000]}

USER QUESTION:
{req.question}

ANSWER:"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"answer": response.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/history", response_model=List[HistoryItem])
def get_history(db: Session = Depends(get_db)):
    """List all past judgment analyses, newest first."""
    judgments = db.query(Judgment).order_by(Judgment.upload_date.desc()).all()

    items = []
    for j in judgments:
        snippet = None
        if j.analyses:
            latest = j.analyses[-1]
            if latest.summary:
                snippet = latest.summary[:120] + "..." if len(latest.summary) > 120 else latest.summary

        items.append({
            "id": j.id,
            "filename": j.filename,
            "upload_date": j.upload_date.isoformat() if j.upload_date else "",
            "summary_snippet": snippet,
        })

    return items

@app.get("/history/{judgment_id}", response_model=HistoryDetail)
def get_history_detail(judgment_id: int, db: Session = Depends(get_db)):
    """Get full analysis for a specific judgment."""
    judgment = db.query(Judgment).filter(Judgment.id == judgment_id).first()
    if not judgment:
        raise HTTPException(status_code=404, detail="Judgment not found")

    latest_analysis = judgment.analyses[-1] if judgment.analyses else None

    web_sources = []
    if latest_analysis and latest_analysis.web_sources:
        try:
            web_sources = json.loads(latest_analysis.web_sources)
        except (json.JSONDecodeError, TypeError):
            web_sources = []

    return {
        "id": judgment.id,
        "filename": judgment.filename,
        "upload_date": judgment.upload_date.isoformat() if judgment.upload_date else "",
        "summary": latest_analysis.summary if latest_analysis else None,
        "laws": latest_analysis.laws if latest_analysis else None,
        "analysis": latest_analysis.analysis_content if latest_analysis else None,
        "web_sources": web_sources,
    }

@app.get("/health")
def health():
    return {
        "status": "online",
        "ollama": bool(llm),
        "vector_db": bool(vector_db),
        "multi_agent": bool(multi_agent),
        "web_search": bool(gemini_llm)
    }

# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
