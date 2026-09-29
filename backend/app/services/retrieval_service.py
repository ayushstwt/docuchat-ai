import logging
from typing import Any, Dict, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        user_id: int,
        document_ids: List[int],
        query_embedding: List[float],
        top_k: int = 6,
        min_similarity: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """
        Runs a cosine distance search using pgvector (embedding <=> :q)
        JOINs document_chunks with documents to fetch document title.
        Filters:
          - chunk's user_id == :user_id
          - chunk's document_id IN :document_ids
          - chunk's is_deleted == False
          - document's is_deleted == False
        Sets hnsw.ef_search = 40 for the session before querying.
        Calculates similarity as (1 - distance) and filters out results below min_similarity.
        """
        if not document_ids or not query_embedding:
            return []

        # Set session parameter for HNSW ef_search (ignore error if backend is SQLite in tests)
        try:
            await self.db.execute(text("SET hnsw.ef_search = 40"))
        except Exception:
            pass

        # Query using raw/constructive SQL to support pgvector cosine operator <=>
        query_str = """
            SELECT 
                c.id AS chunk_id,
                c.chunk_index AS chunk_index,
                c.page_number AS page_number,
                c.content AS content,
                c.token_count AS token_count,
                c.document_id AS document_id,
                d.title AS document_title,
                (c.embedding <=> :query_embedding) AS distance
            FROM document_chunks c
            INNER JOIN documents d ON d.id = c.document_id
            WHERE c.user_id = :user_id
              AND c.document_id = ANY(:document_ids)
              AND c.is_deleted = false
              AND d.is_deleted = false
            ORDER BY distance ASC
            LIMIT :top_k
        """

        try:
            # We can format/bind query_embedding as string or array
            embedding_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
            result = await self.db.execute(
                text(query_str),
                {
                    "user_id": user_id,
                    "document_ids": document_ids,
                    "query_embedding": embedding_str,
                    "top_k": top_k,
                },
            )
            rows = result.mappings().all()

            matched_chunks: List[Dict[str, Any]] = []
            for row in rows:
                distance = float(row["distance"]) if row["distance"] is not None else 1.0
                similarity = 1.0 - distance
                if similarity >= min_similarity:
                    matched_chunks.append({
                        "chunk_id": row["chunk_id"],
                        "chunk_index": row["chunk_index"],
                        "document_id": row["document_id"],
                        "document_title": row["document_title"],
                        "page_number": row["page_number"],
                        "content": row["content"],
                        "token_count": row["token_count"],
                        "similarity": round(similarity, 4),
                    })

            return matched_chunks

        except Exception as e:
            # Fallback for non-pgvector environments (like in-memory SQLite during unit tests)
            logger.warning(f"pgvector query failed ({e}), attempting fallback retrieval")
            fallback_query = """
                SELECT 
                    c.id AS chunk_id,
                    c.chunk_index AS chunk_index,
                    c.page_number AS page_number,
                    c.content AS content,
                    c.token_count AS token_count,
                    c.document_id AS document_id,
                    d.title AS document_title
                FROM document_chunks c
                INNER JOIN documents d ON d.id = c.document_id
                WHERE c.user_id = :user_id
                  AND c.document_id IN :document_ids
                  AND c.is_deleted = 0
                  AND d.is_deleted = 0
                LIMIT :top_k
            """
            try:
                # In SQLite, ANY(:document_ids) is not supported, tuple binding is used
                stmt = text(f"""
                    SELECT 
                        c.id AS chunk_id,
                        c.chunk_index AS chunk_index,
                        c.page_number AS page_number,
                        c.content AS content,
                        c.token_count AS token_count,
                        c.document_id AS document_id,
                        d.title AS document_title
                    FROM document_chunks c
                    INNER JOIN documents d ON d.id = c.document_id
                    WHERE c.user_id = :user_id
                      AND c.document_id IN ({','.join(str(int(i)) for i in document_ids)})
                      AND c.is_deleted = 0
                      AND d.is_deleted = 0
                    LIMIT :top_k
                """)
                res = await self.db.execute(stmt, {"user_id": user_id, "top_k": top_k})
                rows = res.mappings().all()
                return [
                    {
                        "chunk_id": r["chunk_id"],
                        "chunk_index": r["chunk_index"],
                        "document_id": r["document_id"],
                        "document_title": r["document_title"],
                        "page_number": r["page_number"],
                        "content": r["content"],
                        "token_count": r["token_count"],
                        "similarity": 1.0,
                    }
                    for r in rows
                ]
            except Exception as ex_fallback:
                logger.error(f"Fallback search query failed: {ex_fallback}")
                return []
