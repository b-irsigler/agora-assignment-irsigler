#!/usr/bin/env python3
"""
preprocessing.py — Chunks PDFs, embeds them, and injects data into index.html.

Usage:
    export OPENAI_API_KEY="sk-..."
    export OPENAI_BASE_URL="https://api.openai.com"   # optional, defaults to https://api.openai.com
    python preprocessing.py

Dependencies:
    pip install pdfplumber openai tiktoken
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import pdfplumber
import tiktoken
from openai import OpenAI

# ─── Configuration ───────────────────────────────────────────────────────────

PUBLICATIONS_DIR = Path("./original-publications")
INDEX_HTML_PATH = Path("./index.html")
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500       # tokens
CHUNK_OVERLAP = 50     # tokens
BATCH_SIZE = 20        # embeddings per API call

# ─── PDF Text Extraction ─────────────────────────────────────────────────────

def extract_text_by_page(pdf_path: Path) -> list[dict]:
    """Extract text from each page of a PDF. Returns list of {page, text}."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i + 1, "text": text.strip()})
    return pages


def derive_title(pdf_path: Path) -> str:
    """Derive a human-readable title from the PDF filename."""
    name = pdf_path.stem
    # Replace underscores with spaces
    name = name.replace("_", " ")
    # Remove common suffixes
    for suffix in [" web", " Web", " WEB", " final", " Final", " FINAL"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()


# ─── Chunking ────────────────────────────────────────────────────────────────

def chunk_pages(pages: list[dict], chunk_size: int, overlap: int, encoding) -> list[dict]:
    """
    Chunk page texts using a fixed-size token window with overlap.
    Returns list of {chunkIndex, page, text} where page is the starting page.
    """
    # Concatenate all pages, tracking page boundaries in token space
    all_tokens = []
    page_boundaries = []  # (token_start, page_number)

    for p in pages:
        tokens = encoding.encode(p["text"])
        page_boundaries.append((len(all_tokens), p["page"]))
        all_tokens.extend(tokens)

    if not all_tokens:
        return []

    chunks = []
    chunk_index = 0
    start = 0

    while start < len(all_tokens):
        end = min(start + chunk_size, len(all_tokens))
        chunk_tokens = all_tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)

        # Determine which page this chunk starts on
        page_num = 1
        for boundary_start, boundary_page in page_boundaries:
            if boundary_start <= start:
                page_num = boundary_page
            else:
                break

        chunks.append({
            "chunkIndex": chunk_index,
            "page": page_num,
            "text": chunk_text
        })

        chunk_index += 1
        start += chunk_size - overlap

        # Avoid tiny trailing chunks
        if len(all_tokens) - start < overlap:
            break

    return chunks


# ─── Embedding ───────────────────────────────────────────────────────────────

def embed_chunks(client: OpenAI, chunks: list[dict]) -> list[list[float]]:
    """Embed chunk texts in batches. Returns list of embedding vectors."""
    embeddings = [None] * len(chunks)
    texts = [c["text"] for c in chunks]

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"  Embedding batch {i // BATCH_SIZE + 1} ({len(batch)} chunks)...")

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch
        )

        for j, item in enumerate(response.data):
            embeddings[i + j] = item.embedding

        # Small delay to avoid rate limits
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)

    return embeddings


# ─── HTML Injection ──────────────────────────────────────────────────────────

def inject_into_html(html_path: Path, chunk_data: list[dict]):
    """Replace the placeholder JSON in index.html with actual chunk data."""
    html = html_path.read_text(encoding="utf-8")

    # Find the script tag with id="chunk-data"
    pattern = r'(<script\s+id="chunk-data"\s+type="application/json">)(.*?)(</script>)'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        print("ERROR: Could not find <script id=\"chunk-data\"> placeholder in index.html")
        sys.exit(1)

    json_str = json.dumps(chunk_data, ensure_ascii=False)
    new_html = html[: match.start(2)] + json_str + html[match.end(2) :]

    html_path.write_text(new_html, encoding="utf-8")
    print(f"✅ Injected {len(chunk_data)} chunks into {html_path}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Validate environment
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        print("ERROR: Set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    # Ensure base_url ends with /v1 if it doesn't already
    if not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Validate paths
    if not PUBLICATIONS_DIR.exists():
        print(f"ERROR: Publications directory not found: {PUBLICATIONS_DIR}")
        sys.exit(1)

    if not INDEX_HTML_PATH.exists():
        print(f"ERROR: index.html not found: {INDEX_HTML_PATH}")
        sys.exit(1)

    # Get tokenizer
    encoding = tiktoken.encoding_for_model(EMBEDDING_MODEL)

    # Find PDFs
    pdf_files = sorted(PUBLICATIONS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"ERROR: No PDF files found in {PUBLICATIONS_DIR}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF(s):")
    for f in pdf_files:
        print(f"  - {f.name}")

    # Process each PDF
    all_chunks = []
    global_id = 0

    for pdf_path in pdf_files:
        print(f"\n📄 Processing: {pdf_path.name}")
        title = derive_title(pdf_path)
        print(f"  Title: {title}")

        # Extract text
        pages = extract_text_by_page(pdf_path)
        print(f"  Extracted text from {len(pages)} pages")

        if not pages:
            print("  ⚠️  No text found, skipping.")
            continue

        # Chunk
        chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP, encoding)
        print(f"  Created {len(chunks)} chunks")

        # Build chunk objects
        for chunk in chunks:
            chunk["id"] = global_id
            chunk["pdf"] = pdf_path.name
            chunk["title"] = title
            global_id += 1

        all_chunks.extend(chunks)

    print(f"\n📊 Total chunks: {len(all_chunks)}")

    # Embed all chunks
    print("\n🔢 Embedding chunks...")
    embeddings = embed_chunks(client, all_chunks)

    # Attach embeddings to chunks
    for chunk, embedding in zip(all_chunks, embeddings):
        chunk["embedding"] = embedding

    # Inject into HTML
    print("\n💉 Injecting into index.html...")
    inject_into_html(INDEX_HTML_PATH, all_chunks)

    # Summary stats
    total_tokens = sum(len(encoding.encode(c["text"])) for c in all_chunks)
    print(f"\n✅ Done!")
    print(f"   PDFs processed: {len(pdf_files)}")
    print(f"   Total chunks: {len(all_chunks)}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Embedding dimensions: {len(all_chunks[0]['embedding']) if all_chunks else 0}")


if __name__ == "__main__":
    main()
