from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import math
import os

# Load configuration
load_dotenv()

# Create AI client
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

# Model that turns text into numbers (set EMBED_MODEL in .env to change it)
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


def load_documents():
    """Read every .txt file in the knowledge folder. Return {filename: text}."""

    documents = {}

    for file in sorted(Path("knowledge").glob("*.txt")):
        documents[file.name] = file.read_text(encoding="utf-8")

    return documents


def create_embedding(text):
    """Turn text into a list of numbers that represents its meaning."""

    response = client.embeddings.create(model=EMBED_MODEL, input=text)

    return response.data[0].embedding


def cosine_similarity(vector1, vector2):
    """Compare two embeddings. Closer to 1 means more similar meaning."""

    dot = sum(a * b for a, b in zip(vector1, vector2))
    length1 = math.sqrt(sum(a * a for a in vector1))
    length2 = math.sqrt(sum(b * b for b in vector2))

    return dot / (length1 * length2)


def rank_documents(question_embedding, document_embeddings):
    """Return a list of (score, filename), best match first."""

    scores = []

    for filename, embedding in document_embeddings.items():
        score = cosine_similarity(question_embedding, embedding)
        scores.append((score, filename))

    scores.sort(reverse=True)

    return scores


def make_prompt(context, question):
    """Put the chosen document and the question into one prompt."""

    return f"""Answer the question using only the information in the context.
If the answer is not in the context, say:
'I couldn't find that information in the knowledge base.'

Context:

{context}

Question:

{question}
"""


def ask_ai(prompt):
    """Send a prompt to the model and return the answer."""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content
