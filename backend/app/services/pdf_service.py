from typing import List, Tuple
from pypdf import PdfReader
from app.constants.error_codes import ErrorCode
from app.exceptions.base import ServiceException
import tiktoken


class PdfService:
    def __init__(self) -> None:
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def extract_pages(self, path: str) -> List[Tuple[int, str]]:
        """
        Extract text from each page of a PDF using pypdf.
        Returns a list of (page_number, text) where page_number is 1-based.
        Whitespace is normalized.
        If the whole document has no extractable text, raises ServiceException(ErrorCode.PDF_NO_TEXT).
        """
        reader = PdfReader(path)
        pages: List[Tuple[int, str]] = []
        total_text_length = 0

        for idx, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            # Normalize whitespace: collapse internal runs of whitespace and strip
            normalized = " ".join(extracted.split())
            if normalized:
                total_text_length += len(normalized)
            pages.append((idx, normalized))

        if total_text_length == 0:
            raise ServiceException(ErrorCode.PDF_NO_TEXT)

        return pages

    def chunk_pages(
        self,
        pages: List[Tuple[int, str]],
        target_chunk_tokens: int = 800,
        overlap_tokens: int = 100,
    ) -> List[dict]:
        """
        Chunks extracted pages into list of chunks:
        [{'chunk_index': int, 'page_number': int, 'content': str, 'token_count': int}, ...]
        Uses tiktoken (cl100k_base).
        Target ~800 tokens per chunk with ~100 token overlap.
        Never crosses a page boundary unless a page is tiny (< target_chunk_tokens // 4),
        in which case it merges with the next page while keeping the starting page_number.
        Empty chunks are skipped.
        """
        # Step 1: Pre-process pages to merge tiny pages where appropriate
        merged_pages: List[dict] = []
        tiny_threshold = max(50, target_chunk_tokens // 4)

        for page_num, text in pages:
            trimmed = text.strip()
            if not trimmed:
                continue
            tokens = self.tokenizer.encode(trimmed)
            if not tokens:
                continue

            if merged_pages and len(merged_pages[-1]["tokens"]) < tiny_threshold:
                # Merge into the last small page chunk
                last = merged_pages[-1]
                last["tokens"] = self.tokenizer.encode(last["text"] + " " + trimmed)
                last["text"] = last["text"] + " " + trimmed
                # keep original last["page_number"]
            else:
                merged_pages.append({
                    "page_number": page_num,
                    "text": trimmed,
                    "tokens": tokens,
                })

        # Step 2: Chunk each merged unit
        chunks: List[dict] = []
        chunk_index = 0

        for unit in merged_pages:
            tokens = unit["tokens"]
            page_num = unit["page_number"]

            if len(tokens) <= target_chunk_tokens:
                content = self.tokenizer.decode(tokens).strip()
                if content:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "page_number": page_num,
                        "content": content,
                        "token_count": len(tokens),
                    })
                    chunk_index += 1
            else:
                # Slide window over tokens
                start = 0
                step = target_chunk_tokens - overlap_tokens
                if step <= 0:
                    step = target_chunk_tokens

                while start < len(tokens):
                    end = min(start + target_chunk_tokens, len(tokens))
                    chunk_tokens = tokens[start:end]
                    content = self.tokenizer.decode(chunk_tokens).strip()
                    if content:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "page_number": page_num,
                            "content": content,
                            "token_count": len(chunk_tokens),
                        })
                        chunk_index += 1
                    if end >= len(tokens):
                        break
                    start += step

        return chunks
