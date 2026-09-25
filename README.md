# ⚖️ Judicial AI – Legal Document Intelligence Platform

Judicial AI is an AI-powered platform that analyzes legal judgments using **LLaMA 3.1 (Ollama)**, **RAG**, and **multi-agent reasoning**, with optional web-based legal research.

---

## 🚀 Features
- 📄 PDF legal judgment analysis
- 🧠 LLaMA 3.1 (local inference via Ollama)
- 🔎 RAG using FAISS vector database
- 🤖 Multi-agent reasoning pipeline
- 🌐 Optional web research using Gemini
- 📱 Mobile-friendly (hackathon ready)

---

## 🏗️ Architecture
Frontend (React) → FastAPI Backend → Ollama (LLaMA 3.1)  
                                ↳ FAISS (RAG)  
                                ↳ Gemini + Web Search (optional)

---

## ⚠️ Deployment Note
This project uses **Ollama**, which requires local model execution.  
Backend must run on a **local machine or VPS**.  
Serverless platforms (Vercel/Netlify) are **not supported for backend**.

---

## 🧪 Run Backend Locally

```bash
ollama serve
cd backend
python main.py
