from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import random
import secrets
import string
import os

# Load configuration
load_dotenv()

# Create AI client
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


# ---------- Tools: normal Python functions, no AI inside ----------

def get_current_time():
    """Return the current date and time."""

    now = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    return f"Current date and time: {now}"


def roll_dice():
    """Roll a dice and return the number."""

    return f"You rolled {random.randint(1, 6)}"


def generate_password(length=12):
    """Generate a secure random password."""

    characters = (
        string.ascii_letters +
        string.digits +
        string.punctuation
    )

    password = ""

    for _ in range(length):
        password += secrets.choice(characters)

    return f"Your new password: {password}"


# Tool name -> function. The planner returns a name, this finds the function.
TOOLS = {
    "get_current_time": get_current_time,
    "roll_dice": roll_dice,
    "generate_password": generate_password,
}


# ---------- Planner: the AI decides which tool is needed ----------

def choose_tool(user_request):
    """Ask the AI which tool is needed. Return the tool name, or None."""

    planner_prompt = f"""You are a planner. Choose the right tool for the user request.

Available tools:
- get_current_time: use when the user asks for the current date or time
- roll_dice: use when the user asks to roll a dice
- generate_password: use when the user wants a new password

If no tool is needed, answer: none
Reply with ONLY the tool name.

User request: {user_request}
/no_think"""
    # "/no_think" makes qwen3 skip its thinking part, which is faster.
    # Remove that line if you use a different model.

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": planner_prompt}],
        temperature=0
    )

    reply = response.choices[0].message.content

    # Ignore any <think>...</think> part, keep only the final answer
    reply = reply.split("</think>")[-1].strip().lower()

    # Accept the reply only if it contains a known tool name
    for name in TOOLS:
        if name in reply:
            return name

    return None


# ---------- Normal answer, when no tool is needed ----------

def ask_ai(question):
    """Send a question to the model and return the answer."""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": question + " /no_think"}]
    )

    answer = response.choices[0].message.content

    return answer.split("</think>")[-1].strip()
