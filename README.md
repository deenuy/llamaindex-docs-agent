# 🦙 LlamaIndex Docs Agent

**An enterprise-grade AI assistant for navigating LlamaIndex documentation.**  
Refactored for modular, production-ready architecture with FastAPI, ReAct Agent, OpenAI, Qdrant, and Tavily search.  
Clean, secure, observable, and ready for real-world deployment.

<p align="center">
  <img src="https://img.shields.io/github/license/your-repo/llamaindex-docs-agent?style=flat-square" />
  <img src="https://img.shields.io/badge/Made%20with-FastAPI-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square" />
</p>

---

## 🚀 Features

✅ **Multi-Source Retrieval:** Vector + Summary Index with Router Agent  
✅ **FastAPI with Rich Documentation:** Auto-generated Swagger & Redoc  
✅ **Security:** API Key-based authentication  
✅ **Observability:** Global Request ID (ContextVar injection)  
✅ **Structured Logging:** Context-aware logs for distributed environments  
✅ **Error Handling:** Unified responses with detailed tracing  
✅ **Rate Limiting:** Global throttling protection  
✅ **Health Checks:** Verifies OpenAI, Qdrant, Tavily connectivity  
✅ **Gradio Interface:** User-friendly web front-end  
✅ **Enterprise Startup Script:** Robust, idempotent service start  
✅ **Makefile Automation:** Streamlined install, run, and data load

---

## 📦 Tech Stack

- **Python 3.10+**
- **FastAPI** — Web framework
- **Pydantic** — Data validation
- **Qdrant** — Vector database
- **OpenAI GPT-4o-mini** — Language model
- **Tavily API** — Web search augmentation
- **Gradio** — Front-end UI
- **SlowAPI** — Rate limiting
- **ContextVar Logging** — Per-request logging context
- **Structured Project Layout** — Clean, maintainable architecture

---

## 🛠️ Setup & Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/llamaindex-docs-agent.git
cd llamaindex-docs-agent
```

### 2. Install Dependencies (Recommended)

```bash
make init
```

> ⚙️ This includes `.venv` setup and `pip install -e .`

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```bash
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
API_KEY=your-secure-api-key  # API security token
```

### 4. Start Services

We recommend **using the startup script** for seamless bootstrapping:

```bash
bash scripts/start_services.sh
```

This script:
- Starts Qdrant server
- Waits for readiness
- Checks vector store collections
- Auto-loads data if needed
- Boots FastAPI app

### Alternative: Manual run (Developer mode)

```bash
make load_data  # Load your documents into Qdrant
make run        # Start FastAPI app
```

---

## 🎥 Demo

Launch the Gradio web interface at:  
**[http://localhost:8000/gradio](http://localhost:8000/gradio)**

Example queries:
- "How do I install LlamaIndex?"
- "Explain hybrid search in LlamaIndex."
- "What is a Query Engine Tool?"

> 🚀 API is also available at:  
> [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ⚙️ API Endpoints

### Health Check

```http
GET /health
```

- Checks OpenAI, Qdrant, Tavily connections
- Includes `request_id` for traceability

### Chat Endpoint

```http
POST /message/
Headers:
  X-API-KEY: your-api-key
Body:
  {
    "message": "How do I install LlamaIndex?"
  }
```

Response:
```json
{
  "message": "LlamaIndex can be installed using pip install llama-index."
}
```

---

## 🧩 Project Structure

```
app/
├── agents/               # Agent orchestration
├── api/                  # FastAPI routers
├── clients/              # External API clients (Qdrant, Tavily)
├── data_loader/          # Scripts to load vector store data
├── frontend/             # Gradio web app
├── middleware/           # API key, request ID, error handling
├── retrieval_engine/     # Vector and summary engines
├── services/             # Business logic layer
├── utils/                # Logger and config loader
main.py                   # App entrypoint
scripts/start_services.sh # Startup script
Makefile                  # Automation tasks
```

---

## 🚦 Roadmap

- [x] Logging with Request ID (ContextVar)
- [x] Modular app architecture
- [x] API security (X-API-KEY)
- [x] Health checks with OpenAI, Qdrant, Tavily
- [x] Gradio web front-end
- [x] Startup script for idempotent service start
- [ ] Dockerization (`Dockerfile`, `docker-compose.yml`)
- [ ] Test coverage with pytest
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] OpenTelemetry for distributed tracing

---

## ✅ Testing & Quality Assurance

Coming soon:
- Unit tests with pytest
- API tests with HTTPX
- GitHub Actions CI/CD pipeline

---

## 📄 License

This project is licensed under the MIT License.  
See [LICENSE](LICENSE) for details.

---

## 🙌 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [LlamaIndex](https://www.llamaindex.ai/)
- [Qdrant](https://qdrant.tech/)
- [Tavily](https://tavily.com/)
- [OpenAI](https://openai.com/)

---

## 🙏 Credits & Attribution

This project is inspired by and originally designed by [Astra Bertelli (AstraBert)](https://github.com/AstraBert/llamaindex-docs-agent).

Her pioneering work laid the foundation for:
- ReAct agent design
- Retrieval orchestration with LlamaIndex
- Initial FastAPI API and Gradio integration

I have refactored and extended this project to:
- ✅ Enterprise-grade architecture
- ✅ Modular service & agent design
- ✅ Middleware-first pattern for security, logging, observability
- ✅ FastAPI best practices for production
- ✅ End-to-end request tracing with ContextVar

> 🔥 Full respect to AstraBert for her original contribution!

---

## 🤝 Contributing

Contributions are welcome!

1. Fork it 🚀
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request 🎉

> ⭐ Star the repo to show your support!

---

## 📬 Contact

> Built and maintained by **Deenu Gengiti**  
> 📫 Reach out: deenuy@gmail.com

---