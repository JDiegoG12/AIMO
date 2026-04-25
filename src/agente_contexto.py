"""
Context Gathering Agent — AIMO v2
───────────────────────────────────
Conducts a natural, empathetic multi-turn conversation to gather psychological
context from the student. Uses prompts/aimo_answer.txt as system prompt.

Improvements over v1:
  - Adaptive tone injection: adjusts system prompt per-turn based on the
    emotion/intensity detected in the previous turn (TONE_MODULES).
    Theoretical basis: Sanjeewa et al. (2024), Pedamallu et al. (2022).
  - Token-based history compression: compresses when estimated tokens exceed
    TOKEN_COMPRESS_THRESHOLD instead of using a fixed message count.
    Theoretical basis: Wang et al. (2023) — recursive summarization.
  - Robust output parsing: multi-strategy JSON repair + one retry when the
    <context> block is entirely absent from the model output.
  - Structured logging via src.logger.

Output per turn:
  - visible_response : natural text shown to the student
  - context_json     : internal structured summary (hidden from student)
  - updated_history  : conversation history for continuity across turns

context_json fields:
  complete, history, background, beliefs, functional_impact,
  previous_attempts, emotion, intensity, topic, crisis_signal
"""

import os
import re
import json
from src.config_api import get_groq_client, get_default_params
from src.logger import get_logger

logger = get_logger("aimo.contexto")

# ── Constants ─────────────────────────────────────────────────────────────────

# Compress history when estimated token count (chars / 4) exceeds this value.
# Llama-3.3-70b has a 128K context window; we compress well before that to
# keep costs and latency low during multi-turn conversations.
TOKEN_COMPRESS_THRESHOLD = 3_000

# ── Tone modules (Mejora: Adaptive Prompt Injection) ─────────────────────────
# Keys: (emotion, level) or (topic, "topic")
# "high"   → intensity >= 4
# "medium" → intensity 2-3
# "any"    → any intensity level
# Theoretical basis:
#   Sanjeewa et al. (2024) JMIR Mental Health — Rogerian empathy design.
#   Pedamallu et al. (2022) JMIR — withhold directive suggestions at high activation.

TONE_MODULES: dict[tuple[str, str], str] = {
    ("sadness",    "high"):   "Usa un ritmo lento y suave. Prioriza la presencia emocional sobre cualquier sugerencia. Omite propuestas prácticas si la intensidad emocional es muy alta.",
    ("anxiety",    "high"):   "Usa lenguaje enfocado en el presente. Evita proyecciones futuras. Amplía la validación emocional y reduce reflexiones abstractas.",
    ("anger",      "medium"): "Valida la frustración antes de cualquier reencuadre. No redirigir la emoción — deja que aterrice primero.",
    ("overwhelm",  "high"):   "Usa lenguaje simple y fragmentado. Evita listas o múltiples ideas a la vez. Una cosa a la vez.",
    ("loneliness", "any"):    "Enfatiza que el estudiante está siendo escuchado y que no está solo. Retrasa cualquier sugerencia orientada a la acción.",
    ("academic",   "topic"):  "Reconoce la presión académica sin reforzar el perfeccionismo ni la presión por productividad.",
    ("social",     "topic"):  "Reconoce la complejidad relacional sin tomar partido ni hacer suposiciones.",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_prompt() -> str:
    ruta = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'aimo_answer.txt')
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("No se encontró aimo_answer.txt — usando prompt mínimo")
        return "Eres un asistente empático para estudiantes universitarios."


def _construir_prompt_adaptativo(base_prompt: str, context_json: dict | None) -> str:
    """
    Injects tone directives at the end of base_prompt based on emotion data
    extracted from the PREVIOUS turn's context_json.
    Returns base_prompt unchanged when context_json is None or no match found.
    """
    if not context_json:
        return base_prompt

    emotion   = context_json.get("emotion", "neutral")
    intensity = int(context_json.get("intensity", 1))
    topic     = context_json.get("topic", "general")
    crisis    = bool(context_json.get("crisis_signal", False))

    modules: list[str] = []

    level = "high" if intensity >= 4 else "medium" if intensity >= 2 else "low"

    em_key = (emotion, level)
    if em_key in TONE_MODULES:
        modules.append(TONE_MODULES[em_key])
    elif (emotion, "any") in TONE_MODULES:
        modules.append(TONE_MODULES[(emotion, "any")])

    topic_key = (topic, "topic")
    if topic_key in TONE_MODULES:
        modules.append(TONE_MODULES[topic_key])

    if crisis:
        modules.append(
            "PRIORIDAD MÁXIMA: El estudiante puede estar en crisis. Ofrece presencia "
            "compasiva inmediata. Anímalo con cuidado a buscar apoyo profesional en el "
            "campus. Omite sugerencias prácticas y enfócate en la seguridad emocional."
        )

    if not modules:
        return base_prompt

    directive = " ".join(modules)
    return base_prompt + f"\n\nDIRECTIVA DE TONO PARA ESTE TURNO:\n{directive}"


def _estimar_tokens(messages: list) -> int:
    """Rough token estimate: total characters / 4."""
    return sum(len(m.get("content", "")) for m in messages) // 4


def _comprimir_historial(historial: list, client, base_params: dict) -> list:
    """
    Compresses conversation history when estimated tokens exceed the threshold.

    Strategy (Wang et al., 2023 — recursive summarization):
      - Generates a 3-sentence summary focused on:
          (1) main emotional theme
          (2) key personal facts shared by the student
          (3) tone and rapport established
      - Reconstructs history as: [system_prompt, summary_msg, last_4_msgs]
    """
    compress_params = base_params.copy()
    compress_params["temperature"] = 0.1
    compress_params["max_completion_tokens"] = 150
    compress_params["stream"] = False

    compress_system = (
        "Resume esta conversación de apoyo emocional en máximo 3 oraciones. "
        "Incluye SOLO: (1) tema emocional principal, (2) datos personales clave "
        "compartidos por el estudiante, (3) tono y rapport establecido. "
        "No incluyas información identificable. Responde solo con el resumen."
    )

    convo_msgs = [m for m in historial if m["role"] != "system"]
    convo_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in convo_msgs
    )

    resumen = "Contexto previo de la conversación no disponible."
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": compress_system},
                {"role": "user",   "content": convo_text},
            ],
            **compress_params,
        )
        resumen = completion.choices[0].message.content.strip()
        logger.info("Historial comprimido — resumen: %.80s...", resumen)
    except Exception as e:
        logger.error("Error al comprimir historial: %s", e)

    system_msg = next(
        (m for m in historial
         if m["role"] == "system"
         and not m["content"].startswith("[RESUMEN DE SESIÓN")),
        None,
    )

    summary_msg = {
        "role": "system",
        "content": f"[RESUMEN DE SESIÓN — turnos anteriores]: {resumen}",
    }

    last_4 = convo_msgs[-4:]
    new_historial: list = []
    if system_msg:
        new_historial.append(system_msg)
    new_historial.append(summary_msg)
    new_historial.extend(last_4)
    return new_historial


def _reparar_json(raw: str) -> dict | None:
    """
    Multi-strategy JSON repair for common LLM output issues.
    Tries: direct parse → balanced-brace extraction → quote + trailing-comma fix.
    """
    if not raw:
        return None

    raw = re.sub(r'```(?:json)?', '', raw).strip().rstrip('`').strip()

    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract first balanced {...} block
    start = raw.find('{')
    if start != -1:
        depth = 0
        for i, ch in enumerate(raw[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start:i + 1])
                    except json.JSONDecodeError:
                        break

    # Strategy 3: fix common issues (single quotes, trailing commas)
    candidate = raw[raw.find('{'):raw.rfind('}') + 1] if '{' in raw else raw
    candidate = candidate.replace("'", '"')
    candidate = re.sub(r',\s*}', '}', candidate)
    candidate = re.sub(r',\s*]', ']', candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    return None


def _parse_output(raw: str) -> tuple[str, dict | None]:
    """
    Parses <response>...</response> and <context>...</context> from LLM output.

    Returns (visible_response, context_json_or_None).
    """
    # 1. Extract context JSON
    ctx_match = re.search(r'<context>(.*?)</context>', raw, re.DOTALL)
    context_json = None
    ctx_block_found = bool(ctx_match)

    if ctx_match:
        ctx_raw = ctx_match.group(1).strip()
        context_json = _reparar_json(ctx_raw)
        if context_json is None:
            logger.warning("Bloque <context> presente pero JSON inválido")

    # 2. Extract visible response
    resp_match = re.search(r'<response>(.*?)</response>', raw, re.DOTALL)
    if resp_match:
        visible = resp_match.group(1).strip()
    else:
        end_tag_pos = raw.find('</response>')
        if end_tag_pos != -1:
            visible = raw[:end_tag_pos].strip()
        else:
            visible = re.sub(r'<context>.*?</context>', '', raw, flags=re.DOTALL).strip()

    # 3. Safety cleanup
    visible = re.sub(r'<context>.*?</context>', '', visible, flags=re.DOTALL)
    visible = re.sub(r'</?response>', '', visible)
    visible = re.sub(r'</?context>', '', visible)
    visible = visible.strip()

    return visible, context_json, ctx_block_found


# ── Core function ─────────────────────────────────────────────────────────────

def obtener_contexto(
    mensaje_usuario: str,
    historial: list | None = None,
    contexto_previo: dict | None = None,
) -> tuple[str, dict | None, list]:
    """
    Runs one turn of the context-gathering conversation.

    Parameters
    ----------
    mensaje_usuario : str
        The student's current message.
    historial : list | None
        Conversation history from previous turns; None on first turn.
    contexto_previo : dict | None
        context_json from the previous turn, used to inject tone directives.

    Returns
    -------
    (visible_response, context_json_or_None, updated_history)
    """
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.65
    params["stream"] = False
    params["max_completion_tokens"] = 1200

    base_prompt = _load_prompt()
    adapted_prompt = _construir_prompt_adaptativo(base_prompt, contexto_previo)

    if historial is None:
        historial = [{"role": "system", "content": adapted_prompt}]
    else:
        # Re-adapt tone for this turn based on previous context emotion
        if historial and historial[0]["role"] == "system" \
                and not historial[0]["content"].startswith("[RESUMEN DE SESIÓN"):
            historial[0] = {"role": "system", "content": adapted_prompt}

    # Token-based compression (Wang et al., 2023)
    estimated_tokens = _estimar_tokens(historial)
    if estimated_tokens > TOKEN_COMPRESS_THRESHOLD:
        logger.info(
            "Comprimiendo historial — tokens estimados: %d > umbral %d",
            estimated_tokens, TOKEN_COMPRESS_THRESHOLD,
        )
        historial = _comprimir_historial(historial, client, params)

    historial.append({"role": "user", "content": mensaje_usuario})

    def _llamar(messages: list) -> str:
        completion = client.chat.completions.create(messages=messages, **params)
        raw = completion.choices[0].message.content or ""
        return re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

    try:
        raw_clean = _llamar(historial)
        logger.debug("Raw output (primeros 300 chars): %.300s", raw_clean)

        visible, context_json, ctx_found = _parse_output(raw_clean)

        # Retry once if <context> block was completely absent
        if not ctx_found:
            logger.warning("Bloque <context> ausente — reintentando con corrección de formato")
            retry_messages = historial + [
                {"role": "assistant", "content": raw_clean},
                {
                    "role": "user",
                    "content": (
                        "Tu respuesta no incluyó el bloque <context>...</context>. "
                        "Por favor, reformula incluyendo ambas etiquetas <response> y "
                        "<context> exactamente como se indica en las instrucciones."
                    ),
                },
            ]
            raw_retry = _llamar(retry_messages)
            visible_retry, context_json_retry, _ = _parse_output(raw_retry)
            if context_json_retry is not None:
                visible = visible_retry
                context_json = context_json_retry
                logger.info("Retry exitoso — <context> recuperado")
            else:
                logger.error("Retry fallido — context_json sigue ausente")

        historial.append({"role": "assistant", "content": visible})

        is_complete = bool(context_json and context_json.get("complete", False))
        emotion = context_json.get("emotion", "?") if context_json else "?"
        intensity = context_json.get("intensity", "?") if context_json else "?"
        logger.info(
            "Turno procesado — complete=%s, emotion=%s, intensity=%s, context=%s",
            is_complete, emotion, intensity,
            "presente" if context_json else "ausente",
        )

        return visible, context_json, historial

    except Exception as e:
        logger.error("Error en obtener_contexto: %s", e)
        fallback = "Lo siento, tuve un problema de conexión. ¿Podrías repetirme lo que me contabas?"
        historial.append({"role": "assistant", "content": fallback})
        return fallback, None, historial
