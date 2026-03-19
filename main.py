from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from io import BytesIO
import uuid
import re, time
import json
import psutil, GPUtil
from typing import List, Optional
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from uuid import uuid4

from bm25_service import build_bm25_index
from bm25_service import delete_bm25_index

from chunking import chunk_text
from embedding_service import embed_texts
from vector_store import add_embeddings, search, delete_document_embeddings
from rag_service import answer_query, answer_query_stream

from backend.database import engine, SessionLocal
from backend.models import Base, Conversation, Message, Document

from vector_store import rebuild_index_excluding_doc

# -----------------------------
# Create DB Tables
# -----------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Local RAG API", version="2.0")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Utility: OCR Clean
# -----------------------------
def clean_ocr_text(text: str) -> str:
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return text.strip()


# ============================================================
# ROOT
# ============================================================
@app.get("/")
def home():
    return {"message": "Local RAG API running."}


# ============================================================
# DOCUMENTS
# ============================================================
@app.get("/documents")
def get_documents():
    db = SessionLocal()
    try:
        docs = db.query(Document).all()

        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "total_pages": doc.total_pages,
            }
            for doc in docs
        ]
    finally:
        db.close()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        print("\n==============================")
        print("📥 Upload request received")
        print("📄 Filename:", file.filename)

        start_time = time.time()

        db = SessionLocal()

        file_bytes = await file.read()
        print("📦 File size:", len(file_bytes), "bytes")

        doc_id = str(uuid.uuid4())
        metadata_list = []

        reader = PdfReader(BytesIO(file_bytes))
        print("📖 Pages detected:", len(reader.pages))
        total_pages = len(reader.pages)

        # -----------------------------
        # TEXT EXTRACTION
        # -----------------------------
        for page_number, page in enumerate(reader.pages, start=1):

            extracted = page.extract_text()

            if extracted and extracted.strip():
                chunks = chunk_text(
                    extracted,
                    doc_id=doc_id,
                    source=file.filename,
                    page=page_number
                    )
                metadata_list.extend(chunks)

                print("Total chunks created:", len(metadata_list))
                build_bm25_index(doc_id, metadata_list)
                print("📚 BM25 index built")

        # -----------------------------
        # OCR FALLBACK
        # -----------------------------
        if not metadata_list:

            print("⚠ No selectable text. Running OCR...")

            images = convert_from_bytes(file_bytes)

            for page_number, image in enumerate(images, start=1):

                extracted = pytesseract.image_to_string(image)

                if extracted and extracted.strip():
                    chunks = chunk_text(
                        extracted,
                        doc_id=doc_id,
                        source=file.filename,
                        page=page_number
                        )
                    metadata_list.extend(chunks)

                    print("Total chunks created:", len(metadata_list))
                    build_bm25_index(doc_id, metadata_list)
                    print("📚 BM25 index built")

        if not metadata_list:

            print("❌ No readable text found.")
            db.close()

            return {"error": "No readable text found."}

        print("🧠 Total chunks created:", len(metadata_list))

        # -----------------------------
        # GENERATE EMBEDDINGS
        # -----------------------------
        texts = [item["text"] for item in metadata_list]

        embeddings = embed_texts(texts)

        for i in range(len(metadata_list)):
            metadata_list[i]["embedding"] = embeddings[i]

        # -----------------------------
        # ADD TO FAISS
        # -----------------------------
        add_embeddings(embeddings, metadata_list)

        print("📊 Embeddings added to FAISS")

        # -----------------------------
        # SAVE DOCUMENT METADATA
        # -----------------------------
        db.add(Document(
            id=doc_id,
            filename=file.filename,
            total_pages=total_pages
        ))

        db.commit()
        db.close()

        elapsed = round(time.time() - start_time, 2)

        print("✅ Document indexed successfully")
        print("🆔 Doc ID:", doc_id)
        print("⏱ Time taken:", elapsed, "seconds")
        print("==============================\n")

        return {
            "status": "Document indexed successfully",
            "doc_id": doc_id,
            "filename": file.filename
        }

    except Exception as e:

        print("❌ Upload error:", str(e))

        return {"error": str(e)}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    db = SessionLocal()
    try:
        print(f"[DOC DELETE] Requested doc_id={doc_id}")

        doc = db.query(Document).filter(Document.id == doc_id).first()
        print(f"[DOC DELETE] DB doc found: {doc is not None}")

        if not doc:
            db.close()
            return {
                "status": "error",
                "error": "Document not found"
            }

        removed_chunks = delete_document_embeddings(doc_id)

        delete_bm25_index(doc_id)
        print(f"[DOC DELETE] BM25 index removed for {doc_id}")

        db.delete(doc)
        db.commit()
        print(f"[DOC DELETE] DB row deleted for {doc_id}")

        check_doc = db.query(Document).filter(Document.id == doc_id).first()
        print(f"[DOC DELETE] Exists after commit: {check_doc is not None}")

        return {
            "status": "success",
            "doc_id": doc_id,
            "removed_chunks": removed_chunks
        }

    except Exception as e:
        db.rollback()
        print(f"[DOC DELETE ERROR] {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()

# ============================================================
# CHAT
# ============================================================
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    doc_id: Optional[str] = None
    history: Optional[List[dict]] = None



@app.post("/chat")
def chat(request: ChatRequest):

    db = SessionLocal()

    try:

        conversation = None

        # -----------------------------
        # Load Existing Conversation
        # -----------------------------
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id
            ).first()

        # -----------------------------
        # Create New Conversation
        # -----------------------------
        if not conversation:
            conversation = Conversation(
                id=str(uuid4()),
                title=request.query[:50]
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        conversation_id = conversation.id

        # -----------------------------
        # Load History
        # -----------------------------
        previous_messages = db.query(Message) \
            .filter(Message.conversation_id == conversation_id) \
            .order_by(Message.created_at) \
            .all()

        history = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in previous_messages
        ]

        # -----------------------------
        # Streaming Generator
        # -----------------------------
        def event_generator():

            full_answer = ""

            for token in answer_query_stream(
                request.query,
                doc_id=request.doc_id,
                history=history
            ):

                full_answer += token

                yield f"data: {json.dumps({'token': token})}\n\n"

            # -----------------------------
            # Save Messages AFTER streaming
            # -----------------------------
            db.add(Message(
                role="user",
                content=request.query,
                conversation_id=conversation_id
            ))

            db.add(Message(
                role="assistant",
                content=full_answer,
                conversation_id=conversation_id
            ))

            db.commit()

            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    finally:
        db.close()
# ============================================================
# CONVERSATIONS
# ============================================================
@app.get("/conversations")
def list_conversations():
    db = SessionLocal()

    conversations = db.query(Conversation)\
        .order_by(Conversation.created_at.desc())\
        .all()

    result = [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at
        }
        for c in conversations
    ]

    db.close()
    return result


@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    db = SessionLocal()

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        db.close()
        return {"error": "Conversation not found"}

    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at)\
        .all()

    result = {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            }
            for m in messages
        ]
    }

    db.close()
    return result


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    db = SessionLocal()

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        db.close()
        return {"error": "Conversation not found"}

    db.delete(conversation)
    db.commit()
    db.close()

    return {"status": "deleted"}


@app.get("/chat/stream")
def chat_stream(query: str, conversation_id: str | None = None, doc_id: str | None = None):

    db = SessionLocal()

    try:
        conversation = None

        # -----------------------------
        # Load conversation
        # -----------------------------
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()

        # -----------------------------
        # Create new conversation
        # -----------------------------
        if not conversation:
            conversation = Conversation(
                id=str(uuid4()),
                title=query[:50]
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        conversation_id = conversation.id

        # -----------------------------
        # Load conversation history
        # -----------------------------
        previous_messages = db.query(Message) \
            .filter(Message.conversation_id == conversation_id) \
            .order_by(Message.created_at) \
            .all()

        history = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in previous_messages
        ]

        # -----------------------------
        # Streaming generator
        # -----------------------------
        def event_generator():

            full_answer = ""

            for token in answer_query_stream(
                query,
                doc_id=doc_id,
                history=history
            ):

                full_answer += token

                yield f"data: {json.dumps({'token': token})}\n\n"

            # Save messages after streaming
            db.add(Message(
                role="user",
                content=query,
                conversation_id=conversation_id
            ))

            db.add(Message(
                role="assistant",
                content=full_answer,
                conversation_id=conversation_id
            ))

            db.commit()

            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    finally:
        db.close()


@app.get("/system-stats")
def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory().percent

        gpu = 0
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = round(gpus[0].load * 100, 1)

        return {
            "cpu": round(cpu, 1),
            "ram": round(ram, 1),
            "gpu": gpu
        }
    except Exception as e:
        return {
            "cpu": 0,
            "ram": 0,
            "gpu": 0,
            "error": str(e)
        }