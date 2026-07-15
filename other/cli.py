import os
import logging
import sys
import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from collections_manager import create_collection, insert, query
from chunking import chunk_by_chars

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent

# Load .env file when running locally (Docker injects env vars directly).
load_dotenv(dotenv_path=HERE / ".env")

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")

RAG_FILE = HERE / "docs" / "spain.md"
RAG_COLLECTION = HERE / "collections-store"
RAG_EMBED_MODEL: str = os.environ.get("EMBED_MODEL", "nomic-embed-text")
RAG_TOP_K = 10
RAG_THRESHOLD = 0.4
RAG_SIZE = 800
RAG_OVERLAP = 100


if not OPENAI_API_KEY:
    logging.warning(
        "OPENAI_API_KEY is not set. LLM calls will fail until a valid key is provided."
    )

client = OpenAI(
    api_key=OPENAI_API_KEY or "sk-not-configured",
    base_url=OPENAI_BASE_URL,
)

messages: list[dict] = []

def ask_stream(message: str):
    messages.append({"role": "user", "content": message})

    # Send all messages history
    reply = _call_stream(messages)

    messages.append({"role": "assistant", "content": reply})
    

def _call_stream(input_llm: list):
    stream = client.responses.create(
        model=MODEL_NAME,
        input=input_llm,
        stream=True,
        # temperature=2.0,
    )

    reply = ""
    for event in stream:
        # print(event)

        if event.type == 'response.output_text.delta':
            # print(event.delta)
            reply += event.delta
            sys.stdout.write(event.delta)
            sys.stdout.flush()

    sys.stdout.write("\n\n")
    sys.stdout.flush()

    return reply

SYSTEM = "Answer using only the context. If it is not there, say so."

def ask_with_context(message: str, context: str):
    if not messages:
        # First system message
        messages.append({"role": "system", "content": SYSTEM})

    augmented = f"Context:\n----\n{context}\n----\n\nQuestion: {message}"
    llm_input = messages + [{"role": "user", "content": augmented}]

    reply = _call_stream(llm_input)

    # Add only the user question, NOT THE WHOLE CONTEXT
    messages.append({"role": "user", "content": message})
    messages.append({"role": "assistant", "content": reply})


def load_rag_collection():
    doc = RAG_FILE
    assert doc.suffix == ".md"

    # Create collection
    filename = doc.stem
    col = create_collection(
        filename,
        description=f"Collection generated from: {doc.name}",
        metric="cosine",
        persist_path=RAG_COLLECTION,
        )
    
    # TODO: avoid chunking if file is already ingested
    
    # Chunk input file
    file_content = doc.read_text()
    # Chars length strategy
    chunks = chunk_by_chars(file_content, size=RAG_SIZE, overlap=RAG_OVERLAP)
    strategy_label = f"chars(size={RAG_SIZE},overlap={RAG_OVERLAP})"

    # Insert chunks
    ok = 0
    for n, chunk in enumerate(chunks):
        r = insert(col, chunk, {
            "doc_path": str(doc),
            "source": filename,
            "chunk_number": n,
            "chunking_strategy": strategy_label,
            "ingested_at": datetime.date.today().isoformat(),
        })
        ok += r["ok"]
        if not r["ok"]:
            print(f"   ✘ chunk {n}: {r['error']}")
    print(f"4. inserted   {ok}/{len(chunks)} chunks into collection {filename!r} "
          f"({col.count()} total, persisted at {RAG_COLLECTION})")

    return col   


def ask_with_rag(message: str, col):
    hits = query(col, message, top_k=RAG_TOP_K, threshold=RAG_THRESHOLD)
    if not hits:
        print("NO DOCUMENTS WERE FOUND WITH THE CURRENT QUERY PARAMS")
        return
    
    # Build context
    blocks = []
    for h in hits:
        m = h["metadata"]
        blocks.append(f"[{m['source']} · chunk {m['chunk_number']} · {m['doc_path']} "
                      f"· similarity {h['similarity']:.3f}]\n{h['chunk']}")
    context = "\n\n".join(blocks)
    
    # Call LLM:
    ask_with_context(message, context)


def main():
    print("Loading document collection...")
    col = load_rag_collection()
    print("Loading done!")

    while True:
        print("-" * 100)
        s = input('ASK: ').strip()
        if not s:
            exit()
        
        # ask_stream(s)
        # ask_context_file(s)
        ask_with_rag(s, col)


if __name__ == "__main__":
    main()
