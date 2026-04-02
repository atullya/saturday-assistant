import requests
import json
import os
import sys

# Add parent dir to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import get_endpoint_logger

api_logger = get_endpoint_logger("todo_api")

API_BASE = os.getenv("TODO_API_BASE", "http://localhost:5000/api/todos")

# ── Helper: todo API calls ───────────────────────────────────
def api_get(url):
    api_logger.info(f"Issuing GET Request to {url}")
    try:
        resp = requests.get(url)
        api_logger.debug(f"GET Response Status: {resp.status_code}")
        return resp.json()
    except Exception as e:
        api_logger.error(f"GET Request to {url} Failed: {str(e)}")
        return {"error": str(e)}

def api_post(url, data):
    api_logger.info(f"Issuing POST Request to {url} with data: {json.dumps(data)}")
    try:
        resp = requests.post(url, json=data)
        api_logger.debug(f"POST Response Status: {resp.status_code}")
        return resp.json()
    except Exception as e:
        api_logger.error(f"POST Request to {url} Failed: {str(e)}")
        return {"error": str(e)}

def api_patch(url):
    api_logger.info(f"Issuing PATCH Request to {url}")
    try:
        resp = requests.patch(url)
        api_logger.debug(f"PATCH Response Status: {resp.status_code}")
        return resp.json()
    except Exception as e:
        api_logger.error(f"PATCH Request to {url} Failed: {str(e)}")
        return {"error": str(e)}

def api_delete(url):
    api_logger.info(f"Issuing DELETE Request to {url}")
    try:
        resp = requests.delete(url)
        api_logger.debug(f"DELETE Response Status: {resp.status_code}")
        return resp.json()
    except Exception as e:
        api_logger.error(f"DELETE Request to {url} Failed: {str(e)}")
        return {"error": str(e)}

# ── Format todos ──────────────────────────────────────────────
def format_todos(todos):
    if not todos:
        return "📭 No todos found!"
    lines = []
    for t in todos:
        status = "✅" if t["isCompleted"] else "⏳"
        desc   = f" — {t['description']}" if t.get("description") else ""
        lines.append(f"{status} `#{t['id']}` {t['title']}{desc}")
    return "\n".join(lines)

# ── Todo service functions ────────────────────────────────────
def get_all_todos():
    return api_get(API_BASE)

def get_pending_todos():
    return api_get(f"{API_BASE}/pending")

def get_completed_todos():
    return api_get(f"{API_BASE}/completed")

def add_todo(title):
    return api_post(API_BASE, {"title": title})

def mark_done(todo_id):
    try:
        return api_patch(f"{API_BASE}/{int(todo_id)}/done")
    except ValueError:
        return {"error": "ID must be a number."}

def mark_undone(todo_id):
    try:
        return api_patch(f"{API_BASE}/{int(todo_id)}/undone")
    except ValueError:
        return {"error": "ID must be a number."}

def delete_todo(todo_id):
    try:
        return api_delete(f"{API_BASE}/{int(todo_id)}")
    except ValueError:
        return {"error": "ID must be a number."}

def clear_completed():
    return api_delete(f"{API_BASE}/completed")