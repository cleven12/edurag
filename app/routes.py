from flask import Blueprint, request, jsonify
from .chatbot import chat
from .db import save_message, get_history, init_db
import uuid

bp = Blueprint("main", __name__)

@bp.before_app_request
def setup():
    init_db()

@bp.route("/chat", methods=["POST"])
def chat_endpoint():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"ok": False, "error": "invalid JSON"}), 400

        question = data.get("message", "").strip()
        if not question:
            return jsonify({"ok": False, "error": "message is required"}), 400

        sid = data.get("session_id") or str(uuid.uuid4())

        history = get_history(sid)
        answer = chat(sid, question, history)

        save_message(sid, "user", question)
        save_message(sid, "assistant", answer)

        return jsonify({
            "ok": True,
            "session_id": sid,
            "message": {
                "role": "assistant",
                "content": answer
            }
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "running"})