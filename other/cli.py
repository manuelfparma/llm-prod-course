import os
import logging
import sys
from pathlib import Path


from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env file when running locally (Docker injects env vars directly).
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")

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
INPUT_FILE = "getting_killed_lite.md"
context = open(os.path.join(os.path.dirname(__file__), INPUT_FILE)).read()


def ask_context_file(message: str):
    if not messages:
        # First system message
        messages.append({"role": "system", "content": SYSTEM})

    augmented = f"Context:\n----\n{context}\n----\n\nQuestion: {message}"
    llm_input = messages + [{"role": "user", "content": augmented}]

    # FIXME: solo imprime 1 token y muere
    reply = _call_stream(llm_input)

    # Add only the user question, NOT THE WHOLE CONTEXT
    messages.append({"role": "user", "content": message})
    messages.append({"role": "assistant", "content": reply})


def main():
    while True:
        print("-" * 100)
        s = input('ASK: ')
        if not s:
            exit()
        # ask_stream(s)
        ask_context_file(s)

if __name__ == "__main__":
    main()
