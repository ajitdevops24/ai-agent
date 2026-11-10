# AI Agent Development

Build AI agents from scratch in Python, from a first chatbot to a production-ready Research AI Agent Platform, running on local models with Ollama.

## What You Will Build
- AI agents from scratch, and the core architecture behind modern AI agents
- AI assistants with conversation memory, tool usage, document processing and Retrieval-Augmented Generation (RAG)
- Autonomous agents with planning, reasoning, memory and advanced RAG
- Agents integrated with external tools and data sources using the Model Context Protocol (MCP)
- Multi-agent systems where specialized agents work together on complex problems
- Production-ready agents using LangGraph, CrewAI and LangChain
- A complete AI Research Agent that researches, verifies findings, keeps notes and writes structured reports
- A deployed capstone project: Research AI Agent Platform

## Tech Stack
Python, Ollama (`qwen3:1.7b`), OpenAI-compatible API, python-dotenv, Git, VS Code on WSL (Ubuntu). More added as the days progress (LangChain, LangGraph, CrewAI, MCP, FastAPI, Docker).

## Prerequisites
1. Python 3.10+ (`python3 --version`)
2. Visual Studio Code with the WSL extension
3. WSL (Ubuntu) with `zstd` installed
4. Ollama, with the model pulled: `ollama pull qwen3:1.7b`
5. A virtual environment with the packages in `requirements.txt`

## Quick Start
```bash
git clone https://github.com/ajitdevops24/ai-agent.git
cd ai-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama run qwen3:1.7b
```

## Progress
| Day | Topic | Status |
|-----|-------|--------|
| [Day 01](./Day01-hello-ai) | Hello AI: first call to a local LLM | ✅ |
| [Day 02](./Day02-chat-memory) | Chat assistant with conversation memory | ✅ |
| [Day 03](./Day03-prompt-engineering) | Prompt engineering: role-based assistants | ✅ |

## Author
Ajit Kumar Satapathy
