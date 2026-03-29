import requests
from bs4 import BeautifulSoup
import ollama

OLLAMA_MODEL = "llama3.2:1b"
ASSISTANT_NAME = "Saturday"

# ── Portfolio links ───────────────────────────────────────────
PORTFOLIOS = {
    "personal"  : "https://portfolio.atullyamaharjan.com.np/",
    "startup"   : "https://portfolio-startup.onrender.com/",
}

# ── Scrape portfolio text ─────────────────────────────────────
def scrape_portfolio(url):
    try:
        res  = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]
    except Exception as e:
        return f"Error scraping: {e}"

# ── Check if site is up ───────────────────────────────────────
def check_site_status(url):
    try:
        res = requests.get(url, timeout=10)
        return {
            "up"      : True,
            "status"  : res.status_code,
            "time_ms" : int(res.elapsed.total_seconds() * 1000)
        }
    except requests.exceptions.ConnectionError:
        return {"up": False, "status": "unreachable", "time_ms": 0}
    except requests.exceptions.Timeout:
        return {"up": False, "status": "timeout",     "time_ms": 0}
    except Exception as e:
        return {"up": False, "status": str(e),        "time_ms": 0}

# ── Ask Ollama about portfolio content ────────────────────────
def ask_about_portfolio(content, question):
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Saturday, a personal assistant. "
                        "Answer questions based ONLY on the portfolio content provided. "
                        "Keep answers short — 2 to 3 sentences. "
                        "If the answer is not in the content, say 'I could not find that in the portfolio.'"
                    )
                },
                {
                    "role": "user",
                    "content": f"Portfolio content:\n{content}\n\nQuestion: {question}"
                }
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ Ollama error: {e}"

# ── Get portfolio status ──────────────────────────────────────
def get_portfolio_status():
    lines = ["🌐 **Portfolio Status:**\n"]
    for name, url in PORTFOLIOS.items():
        s = check_site_status(url)
        if s["up"]:
            lines.append(f"✅ **{name}** — UP `{s['time_ms']}ms`\n🔗 {url}")
        else:
            lines.append(f"❌ **{name}** — DOWN `{s['status']}`\n🔗 {url}")
    return "\n".join(lines)

# ── Get portfolio links ───────────────────────────────────────
def get_portfolio_links():
    lines = ["🔗 **My Portfolios:**\n"]
    for name, url in PORTFOLIOS.items():
        lines.append(f"**{name.capitalize()}** → {url}")
    return "\n".join(lines)

# ── Ask about portfolio ───────────────────────────────────────
def ask_portfolio_question(question):
    combined_content = ""
    for name, url in PORTFOLIOS.items():
        content = scrape_portfolio(url)
        combined_content += f"\n\n--- {name} portfolio ---\n{content}"
    return ask_about_portfolio(combined_content, question)

# ── Get specific portfolio ────────────────────────────────────
def get_specific_portfolio(name):
    if name not in PORTFOLIOS:
        return f"❌ Portfolio '{name}' not found."
    url = PORTFOLIOS[name]
    s   = check_site_status(url)
    status_text = f"✅ UP `{s['time_ms']}ms`" if s["up"] else "❌ DOWN"
    return (
        f"🔗 **{name.capitalize()} Portfolio**\n"
        f"{url}\n"
        f"Status: {status_text}"
    )