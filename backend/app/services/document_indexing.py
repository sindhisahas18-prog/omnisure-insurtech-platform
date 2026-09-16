from datetime import datetime

from sqlalchemy.orm import Session

from app.models.document import DocumentChunk, DocumentStatus, PolicyDocument
from app.services.document_processing import chunk_text, extract_text
from app.services.embeddings import embed_texts
from app.services.vector_store import VectorStore


def index_document(db: Session, document: PolicyDocument) -> PolicyDocument:
    document.status = DocumentStatus.processing
    db.commit()

    try:
        text = extract_text(document.stored_path)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No extractable text found in this document")

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()

        chunk_rows = []
        for i, chunk in enumerate(chunks):
            row = DocumentChunk(document_id=document.id, chunk_index=i, text=chunk)
            db.add(row)
            chunk_rows.append(row)
        db.flush()  # assign ids without committing yet

        vectors = embed_texts(chunks)
        store = VectorStore(str(document.insurance_type.code))
        store.add([str(row.id) for row in chunk_rows], vectors)

        document.chunk_count = len(chunks)
        document.status = DocumentStatus.indexed
        document.indexed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        document.status = DocumentStatus.error
        document.error_message = str(exc)
        db.commit()

    return document
