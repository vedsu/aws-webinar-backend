import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId

def create_app():
    app = Flask(__name__)

    # CORS: allow your Amplify domain (or use "*" for quick testing)
    allowed_origin = os.getenv("CORS_ORIGIN", "*")
    CORS(app, resources={r"/*": {"origins": allowed_origin}})

    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "webinar_db")

    if not mongo_uri:
        raise RuntimeError("MONGODB_URI env var is required")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    messages = db["messages"]

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "time": datetime.utcnow().isoformat()})

    @app.get("/api/messages")
    def list_messages():
        docs = list(messages.find().sort("created_at", -1).limit(50))
        result = []
        for d in docs:
            result.append({
                "id": str(d["_id"]),
                "name": d.get("name", ""),
                "text": d.get("text", ""),
                "created_at": d.get("created_at", "")
            })
        return jsonify(result)

    @app.post("/api/messages")
    def create_message():
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        text = (data.get("text") or "").strip()

        if not name or not text:
            return jsonify({"error": "name and text are required"}), 400

        doc = {
            "name": name,
            "text": text,
            "created_at": datetime.utcnow().isoformat()
        }
        inserted = messages.insert_one(doc)
        return jsonify({"id": str(inserted.inserted_id), **doc}), 201

    @app.delete("/api/messages/<msg_id>")
    def delete_message(msg_id):
        try:
            oid = ObjectId(msg_id)
        except Exception:
            return jsonify({"error": "invalid id"}), 400

        res = messages.delete_one({"_id": oid})
        if res.deleted_count == 0:
            return jsonify({"error": "not found"}), 404

        return jsonify({"ok": True})

    return app

app = create_app()

if __name__ == "__main__":
    # local dev
    app.run(host="0.0.0.0", port=8000, debug=True)
