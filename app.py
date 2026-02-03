import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId

def create_app():
    app = Flask(__name__)

    # ---- CORS ----
    # Set this in App Runner env:
    # CORS_ORIGIN=https://<your-amplify-domain>.amplifyapp.com
    cors_origin = os.getenv("CORS_ORIGIN", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origin}})

    # ---- MongoDB ----
    # Set these in App Runner env:
    # MONGODB_URI=mongodb+srv://...
    # MONGODB_DB=webinar_db
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "webinar_db")

    if not mongo_uri:
        # Make it obvious in logs if env var is missing
        raise RuntimeError("Missing env var: MONGODB_URI")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    messages_col = db["messages"]

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "time": datetime.utcnow().isoformat()})

    # ---------- API used by your index.html ----------
    @app.get("/api/messages")
    def list_messages():
        docs = list(messages_col.find().sort("created_at", -1).limit(50))
        out = []
        for d in docs:
            out.append({
                "id": str(d["_id"]),
                "name": d.get("name", ""),
                "text": d.get("text", ""),
                "created_at": d.get("created_at", ""),
            })
        return jsonify(out), 200

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
        res = messages_col.insert_one(doc)

        return jsonify({
            "id": str(res.inserted_id),
            **doc
        }), 201

    @app.delete("/api/messages/<msg_id>")
    def delete_message(msg_id: str):
        try:
            oid = ObjectId(msg_id)
        except (InvalidId, TypeError):
            return jsonify({"error": "invalid id"}), 400

        res = messages_col.delete_one({"_id": oid})
        if res.deleted_count == 0:
            return jsonify({"error": "not found"}), 404

        return jsonify({"ok": True}), 200

    return app

app = create_app()

if __name__ == "__main__":
    # local run
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
