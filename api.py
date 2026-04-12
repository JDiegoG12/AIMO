"""
AIMO Flask API
──────────────
Expone los agentes AIMO y Evaluador como endpoints REST.

Endpoints:
  POST /api/chat   { "message": "...", "session_id": "..." }
                   → { "response": "...", "evaluation": {...}, "classification": {...} }

  POST /api/reset  { "session_id": "..." }
                   → { "ok": true }

Uso:
  pip install flask flask-cors
  python api.py
"""

import json
import re
import sys
import os

from flask import Flask, request, jsonify
from flask_cors import CORS

# Asegura que el directorio AIMO esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from src.agente_aimo         import generar_respuesta_aimo
from src.agente_evaluador    import evaluar_interaccion
from src.agente_clasificador import clasificar_estado_emocional

app = Flask(__name__)
CORS(app)  # Permite peticiones desde el dev server de Vite (localhost:5173)

# Historial de conversaciones por session_id (en memoria)
_sessions: dict = {}


def _separar_thinking(texto: str) -> tuple[str, str | None]:
    """
    Separates <think>...</think> reasoning from the actual response.
    Returns (clean_response, thinking_text_or_None).
    """
    match = re.search(r'<think>(.*?)</think>', texto, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        clean    = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
        return clean, thinking
    return texto, None


@app.route("/api/chat", methods=["POST"])
def chat():
    data      = request.get_json(silent=True) or {}
    mensaje   = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not mensaje:
        return jsonify({"error": "El campo 'message' es obligatorio."}), 400

    # Recuperar o inicializar el historial de la sesión
    historial = _sessions.get(session_id)

    # ── Mejora 1: Clasificar estado emocional ─────────────────────────────────
    # Uses only the last 2 messages from history for context (lightweight call).
    # crisis_signal triggers safety override inside _construir_prompt_adaptativo.
    historial_reciente = historial[-2:] if historial else []
    clasificacion = clasificar_estado_emocional(mensaje, historial_reciente)

    # ── Generar respuesta de AIMO (con clasificación para prompt adaptativo) ──
    try:
        respuesta_raw, historial_actualizado = generar_respuesta_aimo(
            mensaje,
            historial,
            clasificacion=clasificacion,
        )
        # Separate <think> chain-of-thought from the visible response
        respuesta, thinking = _separar_thinking(respuesta_raw)
        # Store clean response in history (no <think> tags visible to next turns)
        if historial_actualizado and historial_actualizado[-1]["role"] == "assistant":
            historial_actualizado[-1]["content"] = respuesta
        _sessions[session_id] = historial_actualizado
    except Exception as e:
        print(f"[api] Error en agente AIMO: {e}")
        return jsonify({"error": str(e)}), 500

    # ── Evaluar la interacción ─────────────────────────────────────────────────
    evaluacion = None
    try:
        raw = evaluar_interaccion(mensaje, respuesta)
        if isinstance(raw, str):
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start != -1 and end > start:
                evaluacion = json.loads(raw[start:end])
            else:
                evaluacion = json.loads(raw)
        elif isinstance(raw, dict):
            evaluacion = raw
    except Exception as e:
        print(f"[api] Error al parsear evaluación: {e}")
        evaluacion = None  # No fatal: la UI muestra evaluación opcional

    return jsonify({
        "response":       respuesta,
        "thinking":       thinking,
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
    print("  AIMO API corriendo en http://localhost:5000")
    print("═" * 50)
    app.run(debug=True, port=5000)
