# Multi-Document RAG API

An MVP backend for uploading PDF documents and asking questions grounded in all indexed documents. Original uploads and Chroma vectors are stored under `data/` by default, so additional uploads are indexed incrementally and survive restarts.

## Run locally

Install dependencies, make sure Ollama is running with the configured model, then start the API:

```powershell
python -m pip install -r requirements.txt
ollama pull llama3.2
uvicorn app.main:app --reload
```

Copy `.env.example` into your preferred environment configuration if the defaults do not suit your machine. All runtime values, including model names, storage locations, chunk sizing, and retrieval count are environment-configurable.

## API

`POST /api/v1/documents` accepts one or more PDF files in the `files` multipart field.

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/documents -F "files=@report.pdf"
```

`POST /api/v1/questions` searches all indexed files and answers from the retrieved context. It also returns source file, page, and excerpt details.

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/questions -H "Content-Type: application/json" -d '{\"question\": \"What does the report conclude?\"}'
```

Text and table-like selectable PDF content are extracted with layout preservation. Image-only/scanned PDFs are rejected with a clear message because OCR or a local vision model has not been configured in this MVP.
