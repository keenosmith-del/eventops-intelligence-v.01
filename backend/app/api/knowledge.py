from fastapi import APIRouter
from psycopg.rows import dict_row

from app.core.database import connect_db

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge provenance"])


@router.get("/sources")
def sources():
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT document_id,record_id,record_type,content,event_id,metadata,embedding IS NOT NULL AS indexed FROM knowledge_records ORDER BY document_id,record_id"
        )
        rows = cursor.fetchall()
    docs = {}
    for row in rows:
        doc = docs.setdefault(
            row["document_id"],
            {
                "document_id": row["document_id"],
                "record_count": 0,
                "indexed_count": 0,
                "records": [],
            },
        )
        doc["record_count"] += 1
        doc["indexed_count"] += int(row["indexed"])
        doc["records"].append(row)
    return {"total_records": len(rows), "sources": list(docs.values())}
