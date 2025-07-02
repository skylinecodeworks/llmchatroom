# 🧠 LLM Chatroom

LLM Chatroom is a distributed conversational framework where multiple autonomous agents communicate asynchronously via RabbitMQ and respond to messages using local LLMs served through [Ollama](https://ollama.com/). A web-based live monitor lets you observe the real-time flow of messages in the system.

The project uses **[Astral UV](https://astral.sh/docs/uv)** as its Python package and virtual environment manager.

---

## 📦 Project Structure

```

.
├── agent.py               # Agent logic: message filtering and reply generation
├── docker-compose.yml     # Multi-agent orchestration
├── Dockerfile             # Agent container image
├── llmchatroom.txt        # Project summary (internal)
├── main.py                # Launches a single agent
├── messaging.py           # RabbitMQ utilities
├── ollama\_client.py       # Ollama integration (async)
├── pyproject.toml         # Project definition (PEP 621)
├── README.md              # This documentation
├── requirements.txt       # Static dependency list (for Docker)
├── uv.lock                # uv dependency lockfile
├── webclient.py           # FastAPI + WebSocket UI to monitor chatroom
└── templates/index.html   # Web UI frontend

````

---

## 🚀 Getting Started (Local with UV)

This project uses [uv](https://astral.sh/docs/uv) for dependency management and isolated environments.

1. Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
````

2. Set up and run:

```bash
uv venv
uv pip install -r requirements.txt
uv run main.py
```

3. Launch the web monitor in parallel:

```bash
uvicorn webclient:app --reload
```

4. Visit `http://localhost:8000` to observe messages live.

---

## 🤖 Agents

Agents are lightweight Python processes that:

* Connect to a RabbitMQ `fanout` exchange
* React to keywords or explicit `receiver` targeting
* Use Ollama to generate replies with a system prompt
* Send structured messages (including `message_id`, `conversation_id`, and timestamps)

Each agent is configured using environment variables. Example:

```env
AGENT_ID=agent1
AGENT_NAME=Albert
AGENT_SYSTEM_PROMPT=You are Albert, a philosopher...
AGENT_TARGET_KEYWORDS=why, how, explain
AGENT_INITIAL_MESSAGE=What is the nature of the human being?
```

Run agents manually with:

```bash
uv run main.py
```

Or through Docker Compose as shown below.

---

## 🐳 Docker Compose

To run multiple agents in containers:

```bash
docker network create agents-net
docker-compose up --build
```

This setup launches `agent1` and `agent2`, each configured with its own identity, personality, and behavior through environment variables in `docker-compose.yml`.

Make sure you have a RabbitMQ instance reachable with the same network and credentials.

---

## 🌐 Web Client

The `webclient.py` script starts a FastAPI server with:

* A WebSocket endpoint (`/ws`) that broadcasts all RabbitMQ messages
* A real-time HTML frontend at `/` for monitoring conversations

Use:

```bash
uv run webclient.py
# or via uvicorn directly
uvicorn webclient:app --reload
```

Accessible at: `http://localhost:8000`

---

## 📡 Messaging via RabbitMQ

Messages are exchanged using `fanout` semantics.

Each message payload includes:

* `sender`, `receiver` (optional)
* `message`, `message_id`, `conversation_id`
* `in_response_to` (optional)
* `timestamp` (ISO 8601)

If a message has a specific `receiver`, only that agent will respond.
If not, agents check for target keywords to decide whether to reply.

---

## 🧠 Ollama Integration

Agents call Ollama asynchronously via `ollama.AsyncClient`.

Configuration (example `.env` or passed as env vars):

```env
OLLAMA_MODEL=gemma3:4b
OLLAMA_HOST=http://localhost:11434
```

Responses are:

* Prompted with the agent's `SYSTEM_PROMPT`
* Temperature: `0.2`
* Max tokens: `30`

You must run `ollama serve` and download the specified model before use.

---

## 🧪 Development Flow

```bash
# 1. Start RabbitMQ (external or dockerized)
# 2. Launch Ollama daemon
ollama run gemma:4b

# 3. Start web monitor
uvicorn webclient:app --reload

# 4. Start agents (each in a separate terminal or process)
AGENT_ID=agent1 AGENT_NAME=Albert uv run main.py
AGENT_ID=agent2 AGENT_NAME=Sofia uv run main.py
```

---

## 🔧 Configuration Templates

You can copy and adapt `.env.template` for local agent testing:

```bash
cp .env.template .env
```

Use `.env` for shared configurations when not using Docker Compose.

---

## ✅ Requirements

* Python 3.12+
* [Ollama](https://ollama.com/)
* [Astral UV](https://astral.sh/uv)
* RabbitMQ broker (local or hosted)

Main Python packages:

* `ollama`
* `fastapi`
* `jinja2`
* `uvicorn`
* `pika`
* `python-dotenv`
* `aiofiles`
* `python-multipart`

---

## 📥 Installation (Fallback without UV)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🔄 Extendability

This project is easy to extend:

* Add more agents with different prompts or logic
* Support tool-calling for actions and APIs
* Replace Ollama with another backend
* Integrate memory, persona switching, or fine-tuned models

---

## 📜 License

This project is licensed under the MIT License.
