from openai import OpenAI
from dotenv import load_dotenv
import json
import os

# Load configuration
load_dotenv()

# Create AI client (this talks to Ollama)
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


def get_schema(tool):
    """Get the input schema of a tool (the attribute name differs between FastMCP versions)."""

    schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None)

    return schema or {}


def describe_tools(tools):
    """Turn the tools found on the server into text the planner can read."""

    lines = []

    for tool in tools:
        arguments = get_schema(tool).get("properties", {})
        lines.append(f"- {tool.name}: {tool.description}\n  Arguments: {json.dumps(arguments)}")

    return "\n".join(lines)


def format_steps(state):
    """Turn the steps done so far into text the AI can read."""

    if not state["steps"]:
        return "No steps done yet."

    lines = []

    for number, step in enumerate(state["steps"], start=1):
        lines.append(f"Step {number}: {step['action']} {step['arguments']} -> {step['result']}")

    return "\n".join(lines)


def extract_json(text):
    """Find the JSON object inside the model's reply."""

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"The planner did not return JSON. It said: {text!r}")

    return json.loads(text[start:end + 1])


def ask_model(prompt):
    """Send one prompt to the model and return its reply without any <think> part."""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "user", "content": prompt + "\n/no_think"}],
        temperature=0
    )

    return response.choices[0].message.content.split("</think>")[-1].strip()


def plan_next_step(state, tools):
    """Ask the AI for the next step. Return (action, arguments)."""

    prompt = f"""You are an AI planner. You decide ONLY the next step.

Goal:
{state["goal"]}

Steps done so far:
{format_steps(state)}

Available tools:
{describe_tools(tools)}

Rules:
1. Choose only ONE next step.
2. Never repeat a step that is already done.
3. Use the results above to choose the next step and its arguments.
4. When you have enough information to answer the goal, choose FINISH.
5. Reply with ONLY a JSON object, in one of these formats:
{{"action": "tool_name", "arguments": {{"argument_name": "value"}}}}
{{"action": "FINISH", "arguments": {{}}}}
"""

    plan = extract_json(ask_model(prompt))

    action = plan.get("action")
    arguments = plan.get("arguments") or {}

    if action == "FINISH":
        return "FINISH", {}

    # Check the plan before it is used
    tool = None

    for candidate in tools:
        if candidate.name == action:
            tool = candidate

    if tool is None:
        raise ValueError(f"The planner chose an unknown tool: {action!r}")

    if not isinstance(arguments, dict):
        raise ValueError("The planner's arguments must be a JSON object.")

    allowed = get_schema(tool).get("properties", {})
    unexpected = set(arguments) - set(allowed)

    if unexpected:
        raise ValueError(f"Unsupported arguments for {action}: {', '.join(sorted(unexpected))}")

    return action, arguments


def write_final_answer(state):
    """Turn everything the agent collected into a short answer."""

    prompt = f"""The user's goal:
{state["goal"]}

Results collected:
{format_steps(state)}

Write a short, clear answer to the goal using ONLY the results above.
If something looks wrong, say what it is and why.
If the results are not enough, say what is missing. Do not invent facts."""

    return ask_model(prompt)
