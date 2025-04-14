

```text
app/
├── retrieval_engine/    # Vector search, summary search, routing engine
├── agents/             # Agent orchestration (ReAct etc.)
├── services/           # App orchestration layer
├── clients/            # External service clients (Qdrant, Tavily)
├── api/                # FastAPI routes
├── config/             # Configuration loader
├── logger/             # Logging config
├── frontend/           # Gradio UI
└── main.py             # App entrypoint
```