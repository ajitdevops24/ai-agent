# Day 05: AI Assistant for Documents

## Goal
Make the assistant read a document and answer from it: summarize it, explain it, or answer a question about it.

## What I built
A command-based document assistant split into two files:

| File | Responsibility |
|------|----------------|
| `tools.py` | `read_file()` reads a document from `data/`, `make_prompt()` builds the prompt, `ask_ai()` calls the model |
| `assistant.py` | The chat loop: reads my input, checks it, and calls the functions above |

Sample document: `data/project.txt` (a fictional project charter with name, timeline, budget and team).

## Commands
| Command | What it does |
|---------|--------------|
| `summarize <file>` | Short summary of the document |
| `explain <file>` | Simple explanation of the document |
| `ask <file> <question>` | Answers using only the information in the document |
| `quit` | Exit |

## Tech used
Python, Ollama, `qwen3:1.7b`, `openai` library, `python-dotenv`, VS Code on WSL (Ubuntu)

## How to run
```bash
# from the repo root
source .venv/bin/activate
cd Day05-ai-document
python3 assistant.py
```
Make sure Ollama is running first. This folder needs its own `.env` (copy `.env.example`). Documents go in the `data/` folder.

Try:
- `summarize project.txt`
- `ask project.txt Give me the project name and its manager name`
- `ask project.txt What is the total budget?`

## Output
![document assistant demo](./screenshots/doc-demo.png)

- `ask project.txt who is supervisor` answered from the document
- `what is cost of project` (no command word) was rejected with a help message, with no model call
- `ask data.txt who is manager` printed "File not found", with no model call

## How it works
```
You type: ask project.txt What is the budget?
     |
split into: command = ask, file = project.txt, question = What is the budget?
     |
read_file()    -> reads data/project.txt
make_prompt()  -> puts the document text and the question into one prompt
ask_ai()       -> sends the prompt to the model
     |
prints the answer
```
The prompt tells the model to answer only from the document and to say "I couldn't find that information in the document" if the answer is missing. `temperature=0` keeps answers consistent.

## What I learned
- To work with a document, I put its text inside the prompt. The model only knows what is in the prompt.
- Telling the model to use only the document reduces made-up answers
- Checking input in code (unknown command, missing file) is faster and more reliable than sending everything to the model
- Keeping the work in `tools.py` and only the loop in `assistant.py` makes the code easier to read and extend

## Limitations (honest notes)
- The model can still guess. The document has no "supervisor", but it answered with the Sponsor. Small models need checking against the source.
- Whole documents are sent to the model, so long files hit the context limit. I cut or reject very long files. This is the problem RAG solves.
- Only `.txt` files are supported, and files are read once per question
- No conversation memory, so each question stands alone

## Next
Day 06: first RAG system. Instead of sending the whole document, split it into chunks and send only the parts relevant to the question.
