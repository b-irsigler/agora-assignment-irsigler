# Architecture Plan

## Data Contract: How preprocessing.py and index.html communicate

### Embedded data structure (injected as `window.__CHUNKS__`)

```json
[
  {
    "id": 0,
    "pdf": "Agora_12_Insights_on_Germanys_Energiewende_web.pdf",
    "title": "12 Insights on Germany's Energiewende",
    "page": 5,
    "chunkIndex": 3,
    "text": "The chunk text content here...",
    "embedding": [0.012, -0.034, ...]
  }
]
```

Key fields:
- **id** — global unique index across all chunks
- **pdf** — source filename
- **title** — human-readable publication title
- **page** — page number where this chunk starts
- **chunkIndex** — sequential index within this PDF (needed for 2 chunks before/after context)
- **text** — the actual text content
- **embedding** — the vector from text-embedding-3-small (1536 dimensions)

### Injection mechanism

preprocessing.py looks for a placeholder in index.html:

```html
<script id="chunk-data" type="application/json">[]</script>
```

And replaces the `[]` with the actual JSON array.

---

## index.html Architecture

Single HTML file with inline CSS and JS. No frameworks, no build tools.

### State object

```javascript
state = {
  screen: 'setup', // setup | stakeholder | question | results | summary
  apiKey: '',
  baseURL: '',
  stakeholder: '',
  query: '',
  results: [],       // top 5 search results
  selectedChunk: null,
  summary: ''
}
```

### Screens

| Screen | HTML Elements | Actions |
|---|---|---|
| Setup | API key input, Base URL input, Next button | Validate non-empty → advance |
| Stakeholder | 4 radio buttons/cards, Back + Next buttons | Select one → advance |
| Question | Text input, example question chips, Back + Search button | Embed query → cosine sim → top 5 → advance |
| Results | List of 5 cards with title/page/snippet/score/Summarize button, Back button | Click Summarize → call chat API → advance |
| Summary | Summary text block, Back button | Display stakeholder-tailored summary |

### API calls from browser

1. Embedding — `POST {baseURL}/v1/embeddings` with model `text-embedding-3-small`
2. Chat/Summarization — `POST {baseURL}/v1/chat/completions` with model `gpt-4o`

### Back button behavior

- Back from Stakeholder → Setup: clear stakeholder
- Back from Question → Stakeholder: clear query
- Back from Results → Question: clear results (retrieval results cleared)
- Back from Summary → Results: clear summary, selectedChunk

---

## preprocessing.py Architecture

### Pipeline

1. Read PDFs from ./original-publications
2. Extract text per page using pdfplumber
3. Chunk text: 500 tokens, 50 overlap (track page numbers)
4. Call OpenAI embedding API for each chunk
5. Build JSON array of chunk objects
6. Read index.html, find placeholder script tag, replace with JSON data
7. Write updated index.html

### Dependencies

- pdfplumber — PDF text extraction
- openai — embedding API calls
- tiktoken — accurate token counting for chunking

### Environment

- Needs OPENAI_API_KEY and OPENAI_BASE_URL environment variables

---

## File size estimate

With N=2 PDFs, ~100 pages total, ~200 chunks:
- Embeddings: 200 × 1536 floats × ~8 chars = ~2.4MB
- Text: ~200KB
- Total index.html: ~3-4MB — acceptable for MVP
