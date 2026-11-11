from openai import OpenAI
from dotenv import load_dotenv
import os

# Load configuration
load_dotenv()

# Create AI client
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


def read_file(filename):
    """Read a file from the data folder. Return None if it does not exist."""

    path = os.path.join("data", filename)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def make_prompt(command, content, question=""):
    """Build the prompt for summarize, explain or ask."""

    if command == "summarize":
        return f"Summarize the following document.\n\nDocument:\n\n{content}"

    if command == "explain":
        return f"Explain the following document in simple words.\n\nDocument:\n\n{content}"

    # command == "ask"
    return f"""Answer the question using only the information in the document.
If the answer is not in the document, say:
'I couldn't find that information in the document.'

Document:

{content}

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