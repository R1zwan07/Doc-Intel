from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi import WebSocket, WebSocketDisconnect
import os
import shutil
import uuid
from datetime import datetime
import traceback
import re
from typing import List, Dict, Any
from pydantic import BaseModel
import fitz
import base64

app = FastAPI(title="Document Intelligence System", version="10.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    question: str
    answer: str
    contexts: List[Dict] = []
    chunks_used: int = 0
    error: str = None

UPLOAD_DIR = "uploads"
SUMMARY_DIR = "summaries"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

document_store = {
    "text": "",
    "chunks": [],
    "doc_id": None,
    "images": [],
    "page_count": 0,
    "page_texts": [],
    "summary": "",
    "key_points": [],
    "filename": ""
}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_progress(self, message: str, progress: int):
        for connection in self.active_connections:
            try:
                await connection.send_json({"progress": progress, "message": message})
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def update_progress(message: str, progress: int):
    await manager.send_progress(message, progress)

def clean_text(text: str) -> str:
    """Clean special characters from text"""
    replacements = {
        '': '▶',
        '': '✓',
        '▪': '•',
        '': '•',
        '': '▶',
        '❑': '•',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extract_pdf_complete(file_path: str) -> Dict:
    doc = fitz.open(file_path)
    result = {
        "text": "",
        "images": [],
        "page_count": len(doc),
        "page_texts": []
    }
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        page_text = clean_text(page_text)
        result["text"] += page_text
        result["page_texts"].append({
            "page_num": page_num + 1,
            "text": page_text
        })
        
        for img in page.get_images():
            try:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha < 4:
                    img_data = pix.tobytes("png")
                    result["images"].append({
                        "page": page_num + 1,
                        "data": base64.b64encode(img_data).decode('utf-8')
                    })
                pix = None
            except:
                pass
    
    doc.close()
    return result

def generate_clean_summary(page_texts: List[Dict], page_count: int, filename: str) -> str:
    """Generate a clean, readable summary - NO page-by-page"""
    summary = []
    
    # Header
    summary.append("=" * 70)
    summary.append(f"📚 DOCUMENT SUMMARY: {filename}")
    summary.append("=" * 70)
    summary.append(f"📑 Total Pages: {page_count}")
    summary.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("=" * 70)
    summary.append("")
    
    # Collect all important points from all pages (no page separation)
    all_important_points = []
    
    for page in page_texts:
        if len(page["text"].strip()) < 50:
            continue
        
        lines = page["text"].split('\n')
        
        for line in lines:
            line = line.strip()
            if 30 < len(line) < 350:
                # Skip redundant module headers
                if 'MODULE-' in line and ('Transport Layer' in line or 'Data Link Layer' in line):
                    continue
                if line.startswith(('▶', '✓', '•', '○', '▪', '1.', '2.', '3.', '4.', '5.')):
                    all_important_points.append(line)
                elif line[0].isupper() and len(line) > 40:
                    all_important_points.append(f"• {line}")
        
        if not all_important_points:
            sentences = re.split(r'[.!?]+', page["text"])
            for sent in sentences[:5]:
                sent = sent.strip()
                if len(sent) > 40:
                    all_important_points.append(f"• {sent}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_points = []
    for point in all_important_points:
        if point not in seen:
            seen.add(point)
            unique_points.append(point)
    
    # Add all points to summary
    for point in unique_points[:50]:
        summary.append(point)
        summary.append("")
    
    return '\n'.join(summary)

def extract_key_points(page_texts: List[Dict]) -> List[str]:
    """Extract clean key points"""
    key_points = []
    
    for page in page_texts:
        lines = page["text"].split('\n')
        
        for line in lines:
            line = line.strip()
            if 30 < len(line) < 400:
                if 'MODULE-' in line and ('Transport Layer' in line or 'Data Link Layer' in line):
                    continue
                    
                important_keywords = [
                    'important', 'key', 'definition', 'concept', 'feature',
                    'protocol', 'transmission', 'data', 'communication', 'error',
                    'correction', 'detection', 'coding', 'network', 'signal',
                    'TCP', 'UDP', 'IP', 'flow control', 'congestion'
                ]
                
                clean_line = re.sub(r'[▪❑]', '', line)
                clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                
                if any(kw.lower() in clean_line.lower() for kw in important_keywords):
                    if len(clean_line) > 40:
                        key_points.append(f"📌 {clean_line}")
                elif clean_line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                    key_points.append(f"📌 {clean_line}")
    
    unique = []
    seen = set()
    for kp in key_points:
        if kp not in seen:
            seen.add(kp)
            unique.append(kp)
    
    return unique[:50]

def extract_diagrams(pdf_path: str) -> List[Dict]:
    doc = fitz.open(pdf_path)
    diagrams = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        for img in page.get_images():
            try:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha < 4:
                    img_data = pix.tobytes("png")
                    diagrams.append({
                        "title": f"📷 Figure from Page {page_num + 1}",
                        "type": "image",
                        "image_data": f"data:image/png;base64,{base64.b64encode(img_data).decode('utf-8')}",
                        "description": f"Diagram extracted from page {page_num + 1}"
                    })
                pix = None
            except:
                pass
    
    doc.close()
    return diagrams

# ==================== EXPORT FUNCTIONS ====================
@app.get("/export/markdown")
async def export_markdown():
    if not document_store["text"]:
        raise HTTPException(status_code=400, detail="No document loaded")
    
    content = f"""# 📚 Document Summary: {document_store['filename']}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Pages:** {document_store['page_count']}

---

## Summary

{document_store.get('summary', 'No summary available')}

---

## Key Points ({len(document_store.get('key_points', []))} points)

"""
    for i, point in enumerate(document_store.get('key_points', [])[:50], 1):
        content += f"{i}. {point}\n\n"
    
    file_path = os.path.join(SUMMARY_DIR, f"{document_store['doc_id']}_summary.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return FileResponse(file_path, filename=f"{document_store['filename']}_summary.md")

@app.get("/export/txt")
async def export_txt():
    if not document_store["text"]:
        raise HTTPException(status_code=400, detail="No document loaded")
    
    content = f"""
{'='*70}
📚 DOCUMENT SUMMARY: {document_store['filename']}
{'='*70}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Pages: {document_store['page_count']}
{'='*70}

{document_store.get('summary', 'No summary available')}

{'='*70}
KEY POINTS ({len(document_store.get('key_points', []))} points)
{'='*70}

"""
    for i, point in enumerate(document_store.get('key_points', [])[:50], 1):
        content += f"{i}. {point}\n\n"
    
    file_path = os.path.join(SUMMARY_DIR, f"{document_store['doc_id']}_summary.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return FileResponse(file_path, filename=f"{document_store['filename']}_summary.txt")

@app.get("/export/pdf")
async def export_pdf():
    if not document_store["text"]:
        raise HTTPException(status_code=400, detail="No document loaded")
    
    doc = fitz.open()
    
    page = doc.new_page()
    y = 50
    page.insert_text((50, y), f"Document Summary: {document_store['filename']}", fontsize=16)
    y += 30
    page.insert_text((50, y), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=10)
    y += 30
    page.insert_text((50, y), f"Total Pages: {document_store['page_count']}", fontsize=10)
    y += 50
    
    summary_text = document_store.get('summary', 'No summary available')
    for line in summary_text.split('\n'):
        if y > 750:
            page = doc.new_page()
            y = 50
        if len(line) > 85:
            line = line[:85] + "..."
        page.insert_text((50, y), line, fontsize=9)
        y += 15
    
    page = doc.new_page()
    y = 50
    page.insert_text((50, y), "KEY POINTS", fontsize=14)
    y += 30
    
    for i, point in enumerate(document_store.get('key_points', [])[:50], 1):
        if y > 750:
            page = doc.new_page()
            y = 50
        short_point = point[:85] + "..." if len(point) > 85 else point
        page.insert_text((50, y), f"{i}. {short_point}", fontsize=9)
        y += 20
    
    pdf_path = os.path.join(SUMMARY_DIR, f"{document_store['doc_id']}_summary.pdf")
    doc.save(pdf_path)
    doc.close()
    
    return FileResponse(pdf_path, filename=f"{document_store['filename']}_summary.pdf")

# ==================== MAIN ENDPOINTS ====================
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global document_store
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        await update_progress("Saving file...", 10)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        await update_progress("Extracting text and images...", 30)
        pdf_data = extract_pdf_complete(file_path)
        
        if not pdf_data["text"] or len(pdf_data["text"]) < 100:
            raise HTTPException(status_code=422, detail="Could not extract sufficient text.")
        
        document_store["text"] = pdf_data["text"]
        document_store["doc_id"] = file_id
        document_store["page_count"] = pdf_data["page_count"]
        document_store["page_texts"] = pdf_data["page_texts"]
        document_store["filename"] = file.filename
        
        words = pdf_data["text"].split()
        document_store["chunks"] = [' '.join(words[i:i+500]) for i in range(0, len(words), 500)]
        
        await update_progress("Generating summary...", 70)
        document_store["summary"] = generate_clean_summary(pdf_data["page_texts"], pdf_data["page_count"], file.filename)
        
        await update_progress("Extracting key points...", 90)
        document_store["key_points"] = extract_key_points(pdf_data["page_texts"])
        
        diagrams = extract_diagrams(file_path)
        
        await update_progress("Complete!", 100)
        
        response_data = {
            "file_id": file_id,
            "filename": file.filename,
            "extracted_text": pdf_data["text"],
            "summary": document_store["summary"],
            "key_points": document_store["key_points"],
            "diagrams": diagrams,
            "page_count": pdf_data["page_count"],
            "processed_at": datetime.now().isoformat()
        }
        
        print(f"✅ Extracted {len(pdf_data['text'])} chars, {len(document_store['key_points'])} key points")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    if not document_store["text"]:
        return QuestionResponse(
            question=request.question,
            answer="Please upload a document first.",
            contexts=[],
            chunks_used=0
        )
    
    question_words = set(request.question.lower().split())
    relevant = []
    
    for chunk in document_store["chunks"]:
        score = len(question_words.intersection(set(chunk.lower().split())))
        if score > 0:
            relevant.append((chunk, score))
    
    relevant.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [c[0] for c in relevant[:8]]
    
    if not top_chunks:
        answer = "I couldn't find specific information about that in the document. Please try rephrasing your question."
    else:
        context = "\n".join(top_chunks)
        sentences = re.split(r'[.!?]+', context)
        answer_sentences = []
        for sent in sentences:
            if any(w in sent.lower() for w in question_words if len(w) > 3):
                clean_sent = clean_text(sent.strip())
                answer_sentences.append(f"• {clean_sent}")
        answer = "\n\n".join(answer_sentences[:10]) if answer_sentences else context[:800]
    
    return QuestionResponse(
        question=request.question,
        answer=answer,
        contexts=[{"text": c[:300]} for c in top_chunks[:3]],
        chunks_used=len(top_chunks)
    )

@app.post("/clear")
async def clear_document():
    global document_store
    document_store = {
        "text": "", "chunks": [], "doc_id": None, "images": [],
        "page_count": 0, "page_texts": [], "summary": "",
        "key_points": [], "filename": ""
    }
    return {"message": "Document cleared"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 DocIntel Server Running v10.0")
    print("=" * 50)
    print("📍 http://127.0.0.1:8000")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)