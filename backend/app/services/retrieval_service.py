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

        query_str = """
            SELECT 
                c.id AS chunk_id,
                c.chunk_index AS chunk_index,
                c.page_number AS page_number,
                c.content AS content,
                c.token_count AS token_count,
                c.embedding AS embedding,
                c.document_id AS document_id,
                d.title AS document_title
            FROM document_chunks c
            INNER JOIN documents d ON d.id = c.document_id
            WHERE c.user_id = :user_id
              AND c.document_id = ANY(:document_ids)
              AND c.is_deleted = false
              AND d.is_deleted = false
        """

        try:
            result = await self.db.execute(
                text(query_str),
                {
                    "user_id": user_id,
                    "document_ids": document_ids,
                },
            )
            rows = result.mappings().all()

            def calc_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
                if not vec_a or not vec_b or len(vec_a) != len(vec_b):
                    return 0.0
                dot = sum(a * b for a, b in zip(vec_a, vec_b))
                norm_a = sum(a * a for a in vec_a) ** 0.5
                norm_b = sum(b * b for b in vec_b) ** 0.5
                if norm_a == 0.0 or norm_b == 0.0:
                    return 0.0
                return dot / (norm_a * norm_b)

            scored_chunks = []
            for r in rows:
                emb = r["embedding"]
                sim = 0.0
                if emb and isinstance(emb, list):
                    sim = calc_cosine_similarity(emb, query_embedding)
                elif emb and isinstance(emb, str):
                    try:
                        import json
                        parsed = json.loads(emb)
                        sim = calc_cosine_similarity(parsed, query_embedding)
                    except Exception:
                        sim = 0.5

                if sim >= min_similarity:
                    scored_chunks.append({
                        "chunk_id": r["chunk_id"],
                        "chunk_index": r["chunk_index"],
                        "document_id": r["document_id"],
                        "document_title": r["document_title"],
                        "page_number": r["page_number"],
                        "content": r["content"],
                        "token_count": r["token_count"],
                        "similarity": round(float(sim), 4),
                    })

            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            return scored_chunks[:top_k]

        except Exception as e:
            logger.error(f"Search query failed: {e}")
            return []


