"""
Final Recommendations Agent — AIMO
────────────────────────────────────
Generates personalized, empathetic recommendations for the student based on:
  - The structured context gathered by agente_contexto
  - The clinical risk classification from agente_clasificador

Routing by risk level:
  - LOW    → Groq LLaMA (llama-3.3-70b-versatile)
  - MEDIUM → AWS Bedrock (Claude Sonnet 4.5)
  - HIGH   → Groq LLaMA, brief message directing to university appointment page

Uses prompts/aimo_recommendations.txt as system prompt (low/medium only).
This is the last agent in the pipeline and its output is shown directly to the student.
"""

import os
import json
from src.config_api import get_groq_client, get_default_params, get_bedrock_client

UNIVERSITY_APPT_URL = (
    "https://portal.unicauca.edu.co/versionP/bienestar-universitario/"
    "salud-para-estudiantes/psicologia-y-psiquiatria"
)

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")


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


def _build_input(context_data: dict, clasificacion: dict) -> str:
    context_clean = {k: v for k, v in context_data.items() if k != 'complete'}
    input_data = {
        "context_summary": context_clean,
        "risk_assessment":  clasificacion,
    }
    return json.dumps(input_data, ensure_ascii=False, indent=2)


def _generar_via_groq(system_prompt: str, input_text: str) -> str:
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.7
    params["stream"] = False
    params["max_completion_tokens"] = 1200
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": input_text},
    ]
    completion = client.chat.completions.create(messages=messages, **params)
    return completion.choices[0].message.content or ""


def _generar_via_bedrock(system_prompt: str, input_text: str) -> str:
    # Uses the Bedrock Converse API — works with any model (Nova, Llama, Mistral, Anthropic)
    client = get_bedrock_client()
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": input_text}]}],
        inferenceConfig={"maxTokens": 1200, "temperature": 0.7},
    )
    return response["output"]["message"]["content"][0]["text"]


def _generar_riesgo_alto(context_data: dict, clasificacion: dict) -> str:
    """
    For HIGH risk: use Groq to generate a brief empathetic message that
    urgently directs the student to book an appointment. No recommendations.
    """
    context_clean = {k: v for k, v in context_data.items() if k != 'complete'}
    system = (
        "Eres un asistente de apoyo emocional para estudiantes universitarios. "
        "El estudiante está atravesando una situación emocionalmente grave. "
        "Escribe un mensaje MUY BREVE (máximo 3 oraciones) en español que: "
        "1. Reconozca con calidez lo difícil de su situación, mencionando un detalle específico que compartió. "
        "2. Le diga de forma directa y tranquilizadora que debe hablar con un profesional hoy. "
        "No hagas recomendaciones de autocuidado. No uses términos clínicos. "
        "Solo el mensaje de texto, sin JSON ni etiquetas."
    )
    user_msg = json.dumps({
        "context_summary": context_clean,
        "risk_assessment": clasificacion,
    }, ensure_ascii=False, indent=2)

    try:
        client = get_groq_client()
        params = get_default_params()
        params["temperature"] = 0.4
        params["stream"] = False
        params["max_completion_tokens"] = 200
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ],
            **params,
        )
        opening = (completion.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"[recomendaciones] ✗ Error generando apertura para riesgo alto: {e}")
        opening = "Lo que estás viviendo es muy difícil, y mereces apoyo real ahora mismo."

    return (
        f"{opening}\n\n"
        "Por favor, agenda una cita con el servicio de psicología de la "
        "Universidad del Cauca. Están disponibles para acompañarte de forma "
        f"confidencial y sin juicios:\n{UNIVERSITY_APPT_URL}"
    )


def generar_recomendaciones(context_data: dict, clasificacion: dict) -> str:
    """
    Generates the final personalized recommendations for the student.

    Routes to different backends depending on risk level:
      - low    → Groq LLaMA
      - medium → AWS Bedrock (Claude Sonnet 4.5)
      - high   → Groq LLaMA, appointment redirect (no recommendations)

    Parameters
    ----------
    context_data : dict
        Structured context from agente_contexto.
    clasificacion : dict
        Risk classification from agente_clasificador.

    Returns
    -------
    str — Text to display to the student.
    """
    risk_level = clasificacion.get("risk_level", "medium")
    print(f"[recomendaciones] Nivel de riesgo: {risk_level}")

    if risk_level == "high":
        response = _generar_riesgo_alto(context_data, clasificacion)
        print(f"[recomendaciones] ✓ Respuesta riesgo alto ({len(response)} chars)")
        return response

    system_prompt = _load_prompt()
    input_text = _build_input(context_data, clasificacion)

    try:
        if risk_level == "low":
            response = _generar_via_groq(system_prompt, input_text)
        else:  # medium
            response = _generar_via_bedrock(system_prompt, input_text)

        print(f"[recomendaciones] ✓ Respuesta generada vía "
              f"{'Groq' if risk_level == 'low' else 'Bedrock'} ({len(response)} chars)")
        return response

    except Exception as e:
        print(f"[recomendaciones] ✗ Error ({risk_level}): {e}")
        return (
            "Gracias por compartir conmigo cómo te sientes. "
            "Te recomiendo hablar con el psicólogo de la Universidad del Cauca: "
            f"{UNIVERSITY_APPT_URL}"
        )
