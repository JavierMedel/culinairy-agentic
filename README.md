# CulinAIry Agentic 🍽️

**Agentic AI Meal Planner** powered by **NVIDIA NIM** and **AWS**.  
CulinAIry Agentic autonomously plans weekly meals, retrieves recipes, and generates optimized shopping lists using LLM reasoning.

---

## 🚀 Features

- 🤖 **Agentic Workflow** — Automates meal planning with multi-step reasoning.
- 🧠 **LLM Integration** — Uses NVIDIA NIM for fast, context-aware decision making.
- 🛒 **Smart Shopping Lists** — Dynamically generated based on planned meals.
- 🥗 **Recipe Retrieval** — Pulls from a structured recipe database (CulinAIry format).
- ☁️ **Cloud-Ready** — Runs seamlessly on AWS infrastructure.

---

# CulinAIry Agentic App

## Architecture Overview

```mermaid
flowchart TD
    subgraph Frontend
        WebUI[Web Application<br>(React/Vite)]
    end

    subgraph Backend
        FastAPI[FastAPI Orchestrator]
        AI_Agent[AI Agent<br>(Reasoning + Orchestration)]
        Embeddings[Retrieval Embedding NIM]
        Reasoning[LLM Reasoning NIM<br>llama-3.1-nemotron-nano-8B-v1]
        RecipeDB[Recipe Database]
    end

    WebUI -->|API Calls| FastAPI
    FastAPI --> AI_Agent
    AI_Agent --> Embeddings
    AI_Agent --> Reasoning
    AI_Agent --> RecipeDB
    FastAPI -->|Serve Recipes + Recommendations| WebUI



## 🧩 Architecture
AWS • NVIDIA NIM • EKS / SageMaker • FastAPI • React • FAISS • S3

## Start the Server
cd backend
uvicorn main:app --reload --port 8080
