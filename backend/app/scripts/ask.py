import asyncio
import json
import sys
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService


async def ask(document_id: int, question: str) -> None:
    embedding_service = EmbeddingService()
    chat_service = ChatService()

    async with AsyncSessionLocal() as db:
        retrieval_service = RetrievalService(db)

        # 1. Fetch document to determine user_id and verify it exists
        doc = await db.get(Document, document_id)
        if not doc:
            print(f"Error: Document with ID {document_id} not found.")
            return

        print(f"\nDocument Title: {doc.title} (ID: {doc.id}, Status: {doc.status.value if hasattr(doc.status, 'value') else doc.status})")
        print(f"Question: {question}\n")
        print("Embedding question...")

        # 2. Embed the question
        query_emb = await embedding_service.embed_query(question)

        # 3. Retrieve relevant chunks
        print(f"Searching top chunks for document {document_id}...")
        chunks = await retrieval_service.search(
            user_id=doc.user_id,
            document_ids=[document_id],
            query_embedding=query_emb,
            top_k=6,
            min_similarity=0.2,
        )

        sources = chat_service.build_sources(chunks)
        print(f"Retrieved {len(chunks)} relevant context blocks.\n")

        print("Streaming answer from Azure OpenAI:")
        print("=" * 60)

        prompt_tokens = 0
        completion_tokens = 0

        async for item in chat_service.stream_answer(question=question, chunks=chunks):
            if item.get("type") == "token":
                sys.stdout.write(item["text"])
                sys.stdout.flush()
            elif item.get("type") == "usage":
                prompt_tokens = item.get("prompt_tokens", 0)
                completion_tokens = item.get("completion_tokens", 0)

        print("\n" + "=" * 60)
        print("\nSources (Citations):")
        print(json.dumps(sources, indent=2))
        if prompt_tokens or completion_tokens:
            print(f"\nToken Usage -> Prompt: {prompt_tokens}, Completion: {completion_tokens}")


def main() -> None:
    if len(sys.argv) < 3:
        print('Usage: python -m app.scripts.ask <document_id> "<question>"')
        sys.exit(1)

    try:
        doc_id = int(sys.argv[1])
    except ValueError:
        print("Error: <document_id> must be an integer.")
        sys.exit(1)

    q = sys.argv[2]
    asyncio.run(ask(doc_id, q))


if __name__ == "__main__":
    main()
