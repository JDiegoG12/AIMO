"""
Final Recommendations Agent — AIMO
────────────────────────────────────
Generates personalized, empathetic recommendations for the student based on:
  - The structured context gathered by agente_contexto
  - The clinical risk classification from agente_clasificador

Uses prompts/aimo_recommendations.txt as system prompt.
This is the last agent in the pipeline and its output is shown directly
to the student.
"""

import os
import json
from src.config_api import get_groq_client, get_default_params


def _load_prompt() -> str:
    ruta = os.path.join(
        os.path.dirname(__file__), '..', 'prompts', 'aimo_recommendations.txt'
    )
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("[recomendaciones] ADVERTENCIA: No se encontró aimo_recommendations.txt")
        return (
            "Eres un asistente de apoyo emocional para estudiantes universitarios. "
            "Genera recomendaciones empáticas y personalizadas en español."
        )


def generar_recomendaciones(context_data: dict, clasificacion: dict) -> str:
    """
    Generates the final personalized recommendations for the student.

    Parameters
    ----------
    context_data : dict
        Structured context from agente_contexto (history, background, beliefs,
        functional_impact, previous_attempts).
    clasificacion : dict
        Risk classification from agente_clasificador (risk_level, signals,
        recommended_action).

    Returns
    -------
    str — Recommendations text to display to the student.
    """
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.7
    params["stream"] = False
    params["max_completion_tokens"] = 1200

    system_prompt = _load_prompt()

    # Build the combined input: context + risk assessment
    context_clean = {k: v for k, v in context_data.items() if k != 'complete'}
    input_data = {
        "context_summary": context_clean,
        "risk_assessment":  clasificacion,
    }
    input_text = json.dumps(input_data, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": input_text},
    ]

    try:
        completion = client.chat.completions.create(messages=messages, **params)
        response = completion.choices[0].message.content or ""
        print(f"[recomendaciones] ✓ Respuesta generada ({len(response)} chars)")
        return response

    except Exception as e:
        print(f"[recomendaciones] ✗ Error: {e}")
        return (
            "Gracias por compartir conmigo cómo te sientes. "
            "Te recomiendo hablar con el psicólogo de la Universidad del Cauca: "
            "https://bienestar.unicauca.edu.co/psicologia"
        )
