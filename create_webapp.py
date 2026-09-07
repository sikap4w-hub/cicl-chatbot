import os

# ============================================================
# Ginagawa nito ang buong web app skeleton: mga folder at file.
# Patakbuhin isang beses: python create_webapp.py
# ============================================================

os.makedirs("static", exist_ok=True)

# ------------------------------------------------------------
# main.py  -> ang FastAPI backend (application layer)
# ------------------------------------------------------------
main_py = '''from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).parent

app = FastAPI(title="CICL Chatbot Support System")

# I-serve ang frontend files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class ChatMessage(BaseModel):
    message: str


@app.get("/")
def home():
    # Ibinabalik ang chat interface
    return FileResponse(BASE / "static" / "index.html")


@app.post("/chat")
def chat(payload: ChatMessage):
    user_text = payload.message.strip()
    reply = generate_reply(user_text)
    return {"reply": reply}


def generate_reply(text: str) -> str:
    # ====================================================
    # PLACEHOLDER muna ang sagot.
    # DITO ikakabit ang totoong NLP intent recognition (SOP 2)
    # at ang response generator mamaya. Ngayon, simpleng
    # rule-based lang para mapatunayan na gumagana ang loop.
    # ====================================================
    low = text.lower()
    if not text:
        return "Pakisulat po ang gusto ninyong itanong."
    if "diversion" in low:
        return ("Ang diversion po ay alternatibong proseso para sa isang bata na "
                "hindi dumadaan agad sa korte. Gusto ninyo bang ipaliwanag pa?")
    if "karapatan" in low or "rights" in low:
        return ("May mga karapatan po kayo bilang menor de edad, tulad ng karapatang "
                "magkaroon ng magulang o social worker sa tabi ninyo.")
    if "laro" in low or "game" in low:
        return "Pwede po kayong maglaro ng Legal Consequence Game sa tab na 'Laro'."
    return ("Naitala ko po ang mensahe ninyo. (Placeholder muna ang sagot; dito "
            "ikakabit ang totoong chatbot.)")
'''

# ------------------------------------------------------------
# static/index.html  -> ang chat + game interface (presentation layer)
# ------------------------------------------------------------
index_html = '''<!DOCTYPE html>
<html lang="tl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CICL Chatbot Support System</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header>
    <h1>CICL Support System</h1>
    <nav>
      <button id="tab-chat" class="tab active" onclick="showView('chat')">Chat</button>
      <button id="tab-game" class="tab" onclick="showView('game')">Laro</button>
    </nav>
  </header>

  <main>
    <!-- CHAT VIEW -->
    <section id="view-chat" class="view">
      <div id="messages" class="messages"></div>
      <div class="input-row">
        <input id="user-input" type="text" placeholder="I-type ang tanong mo..." autocomplete="off">
        <button id="send-btn" onclick="sendMessage()">Send</button>
      </div>
      <p class="note">Speech input (Taglish) ay ikakabit dito mamaya.</p>
    </section>

    <!-- GAME VIEW (placeholder) -->
    <section id="view-game" class="view hidden">
      <div class="game-placeholder">
        <h2>Applied Legal Consequence Game</h2>
        <p>Dito ilalagay ang mga storyboard at branching scenario.</p>
        <p class="note">(Ginagawa pa. Ito ang lalagyan ng laro.)</p>
      </div>
    </section>
  </main>

  <script src="/static/script.js"></script>
</body>
</html>
'''

# ------------------------------------------------------------
# static/style.css
# ------------------------------------------------------------
style_css = '''* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, Helvetica, sans-serif; background: #f4f5f7; color: #222; height: 100vh; display: flex; flex-direction: column; }
header { background: #2b3a67; color: #fff; padding: 14px 20px; }
header h1 { font-size: 20px; font-weight: 600; }
nav { margin-top: 10px; display: flex; gap: 8px; }
.tab { background: transparent; color: #cdd6f4; border: 1px solid #4a5a8a; padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }
.tab.active { background: #fff; color: #2b3a67; font-weight: 600; }
main { flex: 1; overflow: hidden; display: flex; }
.view { flex: 1; display: flex; flex-direction: column; padding: 16px; max-width: 720px; margin: 0 auto; width: 100%; }
.hidden { display: none; }
.messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding: 8px; }
.bubble { max-width: 75%; padding: 10px 14px; border-radius: 14px; line-height: 1.5; font-size: 15px; }
.bubble.user { align-self: flex-end; background: #2b3a67; color: #fff; border-bottom-right-radius: 4px; }
.bubble.bot { align-self: flex-start; background: #e6e9f0; color: #222; border-bottom-left-radius: 4px; }
.input-row { display: flex; gap: 8px; margin-top: 10px; }
#user-input { flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 15px; }
#send-btn { background: #2b3a67; color: #fff; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 15px; }
#send-btn:hover { background: #3a4d85; }
.note { font-size: 12px; color: #888; margin-top: 8px; text-align: center; }
.game-placeholder { margin: auto; text-align: center; color: #555; }
.game-placeholder h2 { margin-bottom: 10px; color: #2b3a67; }
.game-placeholder p { margin: 6px 0; }
'''

# ------------------------------------------------------------
# static/script.js
# ------------------------------------------------------------
script_js = '''function showView(name) {
  document.getElementById("view-chat").classList.toggle("hidden", name !== "chat");
  document.getElementById("view-game").classList.toggle("hidden", name !== "game");
  document.getElementById("tab-chat").classList.toggle("active", name === "chat");
  document.getElementById("tab-game").classList.toggle("active", name === "game");
}

function addBubble(text, who) {
  const div = document.createElement("div");
  div.className = "bubble " + who;
  div.textContent = text;
  const box = document.getElementById("messages");
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendMessage() {
  const input = document.getElementById("user-input");
  const text = input.value.trim();
  if (!text) return;
  addBubble(text, "user");
  input.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    addBubble(data.reply, "bot");
  } catch (err) {
    addBubble("May error sa koneksyon sa server.", "bot");
  }
}

document.getElementById("user-input").addEventListener("keydown", function (e) {
  if (e.key === "Enter") sendMessage();
});

// Panimulang mensahe
addBubble("Kumusta! Ako ang CICL support assistant. Ano ang maitutulong ko?", "bot");
'''

files = {
    "main.py": main_py,
    "static/index.html": index_html,
    "static/style.css": style_css,
    "static/script.js": script_js,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa:", path)

print("\nTapos na! Buksan mo sa VS Code, tapos patakbuhin: uvicorn main:app --reload")