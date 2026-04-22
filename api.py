"""
AIMO Flask API — v2
────────────────────
3-stage pipeline:
  1. Context Agent  (aimo_answer.txt)        — multi-turn natural conversation
  2. Classifier     (aimo_classifier.txt)    — clinical risk assessment
  3. Recommendations (aimo_recommendations.txt) — final personalized output

Evaluation (OpenAI GPT-4o-mini) runs ONLY when recommendations are delivered,
using the context + classification outputs as input.

Endpoints:
  POST /api/chat   { "message": "...", "session_id": "..." }
                   → { "response": "...", "phase": "gathering|complete",
                       "evaluation": {...}|null, "classification": {...}|null }

  POST /api/reset  { "session_id": "..." }
                   → { "ok": true }

Usage:
  pip install flask flask-cors
  python api.py
"""

import json
import sys
import os

from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(__file__))

from src.agente_contexto        import obtener_contexto
from src.agente_clasificador    import clasificar_riesgo
from src.agente_recomendaciones import generar_recomendaciones
from src.agente_evaluador       import evaluar_interaccion

app = Flask(__name__)
CORS(app)

# Session structure per session_id:
# {
#   "context_history": list | None,  — conversation history for context agent
#   "context_data":    dict | None,  — latest accumulated context JSON
#   "phase":           str,          — "gathering" | "complete"
# }
_sessions: dict = {}


@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.get_json(silent=True) or {}
    mensaje    = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not mensaje:
        return jsonify({"error": "El campo 'message' es obligatorio."}), 400

    session = _sessions.get(session_id, {
        "context_history": None,
        "context_data":    None,
        "phase":           "gathering",
    })

    # ── Phase: complete — conversation already finished ───────────────────────
    if session.get("phase") == "complete":
        return jsonify({
            "response": (
                "Ya hemos completado nuestra conversación. "
                "Si deseas comenzar de nuevo, puedes reiniciar la sesión."
            ),
            "phase":          "complete",
            "evaluation":     None,
            "classification": None,
        })

    # ── Phase: gathering — run context agent ──────────────────────────────────
    visible_response, context_json, context_history = obtener_contexto(
        mensaje,
        session.get("context_history"),
    )

    session["context_history"] = context_history

    if context_json:
        session["context_data"] = context_json

    is_complete = bool(context_json and context_json.get("complete", False))

    if not is_complete:
        # Still gathering context — return visible response to student
        _sessions[session_id] = session
        return jsonify({
            "response":       visible_response,
            "phase":          "gathering",
            "evaluation":     None,
            "classification": None,
        })

    # ── Context complete — run classifier + recommendations ───────────────────
    context_data = session["context_data"]

    # 1. Clinical risk classification
    clasificacion = clasificar_riesgo(context_data)

    # 2. Final personalized recommendations
    recomendaciones = generar_recomendaciones(context_data, clasificacion)

    # 3. Evaluation via OpenAI (only for low/medium risk — high just redirects)
    evaluacion = None
    if clasificacion.get("risk_level") != "high":
        try:
            context_str = json.dumps(
                {k: v for k, v in context_data.items() if k != 'complete'},
                ensure_ascii=False,
            )
            clasificacion_str = json.dumps(clasificacion, ensure_ascii=False)
            raw_eval = evaluar_interaccion(context_str, clasificacion_str, recomendaciones)

            if isinstance(raw_eval, dict):
                evaluacion = raw_eval
            elif isinstance(raw_eval, str):
                start = raw_eval.find("{")
                end   = raw_eval.rfind("}") + 1
                if start != -1 and end > start:
                    evaluacion = json.loads(raw_eval[start:end])
        except Exception as e:
            print(f"[api] Error en evaluación: {e}")
            evaluacion = None  # Non-fatal: UI handles missing evaluation gracefully

    # Mark session as complete
    session["phase"] = "complete"
    _sessions[session_id] = session

    return jsonify({
        "response":       recomendaciones,
        "phase":          "complete",
        "evaluation":     evaluacion,
        "classification": clasificacion,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    _sessions.pop(session_id, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("═" * 50)
    print("  AIMO API v2 — http://localhost:5000")
    print("═" * 50)
    app.run(debug=True, port=5000)
