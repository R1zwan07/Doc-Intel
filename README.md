# Doc-Intel
# 📚 DocIntel – AI-Powered Document Intelligence System

## 🚀 Overview

**DocIntel** is an AI-driven Document Intelligence System designed to transform static PDF documents into **interactive, structured, and intelligent study materials**.

The system enables users to:

* Extract meaningful insights from PDFs
* Generate structured summaries and key points
* Ask contextual questions using AI (RAG-based Q&A)
* Visualize diagrams and important content

This project is built with a **modular, scalable architecture** using FastAPI and local LLMs via Ollama.

---

## 🧠 Key Features

### 📄 Smart PDF Processing

* Extracts text and images from uploaded PDFs
* Handles multi-page documents efficiently
* Supports real-time processing feedback (WebSocket-based progress updates)

### 📝 AI-Based Summarization

* Generates structured summaries for better understanding
* Extracts 30–50 important key points
* Designed for **exam-oriented learning**

### 💬 Intelligent Q&A System (RAG)

* Ask questions directly from the document
* Context-aware answers using chunk-based retrieval
* Uses Retrieval-Augmented Generation (RAG)

### 🖼️ Diagram Extraction

* Extracts real diagrams/images from PDFs
* Displays them in an interactive UI

### 📤 Export Options

* Export results as:

  * PDF

### 🌙 Modern UI

* Responsive frontend (mobile + desktop)
* Dark mode support
* Floating AI chat assistant
  (see frontend: )

---

## 🏗️ Architecture

```text
Frontend (HTML + JS)
        ↓
FastAPI Backend
        ↓
Pipeline:
[PDF Processor] → [Text Chunking] → [RAG Engine] → [Ollama LLM]
                                ↓
                [Summary + Q&A + Key Points]
```

---

## 🧱 Tech Stack

### Backend

* FastAPI
* PyMuPDF (fitz)
* pdfplumber
* WebSockets
* Python

### AI / NLP

* Ollama (Local LLM)
* Custom RAG Engine
* Text Chunking
* Keyword-based Retrieval (upgradeable to embeddings)

### Frontend

* HTML, CSS, JavaScript
* Responsive UI
* Interactive chat interface

---

## 📁 Project Structure

```text
backend/
│
├── main.py                 # FastAPI entry point
├── routes/                # API endpoints
├── services/              # Business logic
├── core/                  # RAG + chunking logic
├── models/                # Pydantic schemas
│
frontend/
│
├── index.html             # UI interface
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/docintel.git
cd docintel
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Install Ollama

Download and install Ollama:
https://ollama.ai

Run the model:

```bash
ollama run llama2
```

---

### 5️⃣ Run Backend Server

```bash
python main.py
```

Server runs at:

```
http://127.0.0.1:8000
```

---

### 6️⃣ Run Frontend

```bash
cd frontend
python -m http.server 3000
```

Open:

```
http://localhost:3000
```

---

## 📡 API Endpoints

### 📤 Upload PDF

```
POST /upload
```

### 💬 Ask Question

```
POST /ask
```

### 📊 Health Check

```
GET /health
```

### 📥 Export

```
GET /export/pdf
GET /export/txt
GET /export/markdown
```

---

## 🔄 Workflow

1. Upload PDF
2. System extracts text + images
3. Generates:

   * Summary
   * Key Points
   * Diagrams
4. User asks questions via chat
5. AI responds using document context

---

## ⚠️ Current Limitations

* Uses keyword-based retrieval (not embeddings yet)
* Performance depends on document size
* Ollama must be running locally

---

## 🚀 Future Improvements

* Replace vector store with FAISS / ChromaDB
* Add multilingual support (important for rural education)
* Voice-based interaction (Text-to-Speech)
* Better semantic search using embeddings
* Adaptive learning (difficulty-based explanations)

---

## 🎯 Use Cases

* 📖 Students preparing for exams
* 📑 Research paper summarization
* 🧑‍🏫 Teaching and content explanation
* 📚 Rural education support systems

---

## 👨‍💻 Author

**Mohammed Rizwan S**
Computer Science Engineering Student
AI & Cloud Enthusiast

---

## ⭐ Final Note

DocIntel is not just a PDF tool — it is a step toward building an
**AI-powered personalized learning ecosystem**, especially aimed at improving accessibility and quality of education.

---
