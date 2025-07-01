import os
import json
import pika
import threading
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")
clients = []
event_loop = None

@app.on_event("startup")
async def startup_event():
    global event_loop
    event_loop = asyncio.get_running_loop()
    print("🌀 Event loop capturado en startup.")

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print("🟢 WebSocket conectado")
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        clients.remove(websocket)
        print("🔴 WebSocket desconectado")

def broadcast_message(msg):
    for ws in clients:
        try:
            asyncio.run_coroutine_threadsafe(ws.send_text(msg), event_loop)
        except Exception as e:
            print(f"[⚠️ Error enviando mensaje]: {e}")

def start_rabbit_listener():
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", 5672))
    user = os.getenv("RABBITMQ_USER", "user")
    password = os.getenv("RABBITMQ_PASSWORD", "password")
    exchange = os.getenv("EXCHANGE_NAME", "llmchatroom")

    creds = pika.PlainCredentials(user, password)
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=creds))
    channel = conn.channel()

    channel.exchange_declare(exchange=exchange, exchange_type="fanout", durable=True)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=exchange, queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            msg = body.decode()
            print(f"[📨 Recibido] {msg}")
            broadcast_message(msg)
        except Exception as e:
            print(f"[⚠️ Error procesando mensaje]: {e}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print("🔁 Escuchando mensajes desde RabbitMQ...")
    channel.start_consuming()

# HTML UI con mejora de experiencia
os.makedirs("templates", exist_ok=True)
with open("templates/index.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Chatroom</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e1e; color: #eee; margin: 0; padding: 0; }
        header { background: #333; padding: 10px; text-align: center; font-size: 24px; color: #0f0; }
        #messages { padding: 10px; height: 80vh; overflow-y: scroll; border-bottom: 1px solid #555; }
        .msg { margin: 5px 0; }
        .meta { color: #999; font-size: 12px; }
        .markdown {
            background: #2a2a2a;
            padding: 10px;
            border-radius: 6px;
            margin-top: 4px;
        }
        .markdown h1, .markdown h2 { color: #4fc3f7; }
        .markdown p, .markdown ul, .markdown ol { color: #ccc; }
        .markdown code {
            background-color: #333;
            color: #e0e0e0;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
        }
        .markdown pre {
            background-color: #222;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        form { display: flex; padding: 10px; background: #2a2a2a; }
        input, select { margin-right: 10px; padding: 5px; }
        input[type=text] { flex: 1; }
    </style>
</head>
<body>
    <header>💬 LLM Chatroom Monitor</header>
    <div id="messages"></div>
    <form id="msgForm">
        <select id="sender">
            <option value="user">Tú (usuario)</option>
            <option value="agent1">Agente 1</option>
            <option value="agent2">Agente 2</option>
            <option value="agent3">Agente 3</option>
        </select>
        <input type="text" id="message" placeholder="Escribe un mensaje..." required />
        <button type="submit">Enviar</button>
    </form>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        const ws = new WebSocket("ws://" + location.host + "/ws");
        const messagesDiv = document.getElementById("messages");
        ws.onmessage = event => {
            const data = JSON.parse(event.data);
            const div = document.createElement("div");
            div.className = "msg";
            const parsedMarkdown = marked.parse(data.message);
            let timeString = "";
            if (data.timestamp && typeof data.timestamp === "number") {
                const d = new Date(data.timestamp * 1000);
                if (!isNaN(d.getTime())) {
                    timeString = d.toLocaleTimeString();
                }
            }
            div.innerHTML = `
                <div><strong>${data.sender}</strong> → <em>${data.receiver || 'TODOS'}</em>:</div>
                <div class="markdown">${parsedMarkdown}</div>
                <div class='meta'>${timeString}</div>
            `;
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        };

        const form = document.getElementById("msgForm");
        form.onsubmit = async e => {
            e.preventDefault();
            const sender = document.getElementById("sender").value;
            const message = document.getElementById("message").value;
            const body = JSON.stringify({ sender, receiver: "", message });
            await fetch("/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: body
            });
            document.getElementById("message").value = "";
        };
    </script>
</body>
</html>
""")

@app.post("/send")
async def send_message(payload: dict):
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", 5672))
    user = os.getenv("RABBITMQ_USER", "user")
    password = os.getenv("RABBITMQ_PASSWORD", "password")
    exchange = os.getenv("EXCHANGE_NAME", "llmchatroom")

    creds = pika.PlainCredentials(user, password)
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=creds))
    channel = conn.channel()

    msg = {
        "sender": payload.get("sender", "user"),
        "receiver": payload.get("receiver", ""),
        "message": payload.get("message", ""),
        "timestamp": time.time()
    }

    channel.basic_publish(
        exchange=exchange,
        routing_key="",
        body=json.dumps(msg).encode()
    )
    conn.close()
    return {"status": "sent"}

if __name__ == "__main__":
    threading.Thread(target=start_rabbit_listener, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8081)
