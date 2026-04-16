"""
Context Gathering Agent — AIMO
───────────────────────────────
Conducts a natural, empathetic multi-turn conversation to gather psychological
context from the student. Uses prompts/aimo_answer.txt as system prompt.

Output per turn:
  - visible_response : natural text shown to the student (no JSON/technical terms)
  - context_json     : internal structured summary (hidden from student)
  - updated_history  : conversation history for continuity across turns

context_json includes a 'complete' field set to True when enough context has
been gathered across all five dimensions (history, background, beliefs,
functional_impact, previous_attempts).
"""

import os
import re
import json
from src.config_api import get_groq_client, get_default_params


def _load_prompt() -> str:
    ruta = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'aimo_answer.txt')
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("[contexto] ADVERTENCIA: No se encontró aimo_answer.txt")
        return "Eres un asistente empático para estudiantes universitarios."


def _parse_output(raw: str) -> tuple[str, dict | None]:
    """
    Parses <response>...</response> and <context>...</context> blocks.

    Handles all common model output variations:
    - Both tags present (ideal)
    - Opening <response> tag missing (model starts text directly)
    - Extra whitespace or markdown fences around the JSON

    Returns
    -------
    (visible_response, context_json_or_None)
    """
    # ── 1. Extract context JSON (always at the end) ───────────────────────────
    ctx_match = re.search(r'<context>(.*?)</context>', raw, re.DOTALL)
    context_json = None

    if ctx_match:
        ctx_raw = ctx_match.group(1).strip()
        ctx_raw = re.sub(r'```(?:json)?', '', ctx_raw).strip().rstrip('`').strip()
        try:
            context_json = json.loads(ctx_raw)
        except json.JSONDecodeError:
            start = ctx_raw.find('{')
            end   = ctx_raw.rfind('}')
            if start != -1 and end > start:
                try:
                    context_json = json.loads(ctx_raw[start:end + 1])
                except json.JSONDecodeError:
                    print("[contexto] X No se pudo parsear el bloque <context>")

    # ── 2. Extract visible response ───────────────────────────────────────────
    # Strategy A: both <response> tags present
    resp_match = re.search(r'<response>(.*?)</response>', raw, re.DOTALL)
    if resp_match:
        visible = resp_match.group(1).strip()
    else:
        # Strategy B: model skipped the opening tag — grab text before </response>
        end_tag_pos = raw.find('</response>')
        if end_tag_pos != -1:
            visible = raw[:end_tag_pos].strip()
        else:
            # Strategy C: no response tags at all — remove the context block
            visible = re.sub(r'<context>.*?</context>', '', raw, flags=re.DOTALL).strip()

    # ── 3. Safety cleanup — strip any residual XML that reached visible text ──
    visible = re.sub(r'<context>.*?</context>', '', visible, flags=re.DOTALL)
    visible = re.sub(r'</?response>',           '', visible)
    visible = re.sub(r'</?context>',            '', visible)
    visible = visible.strip()

    return visible, context_json


def obtener_contexto(
    mensaje_usuario: str,
    historial: list | None = None,
) -> tuple[str, dict | None, list]:
    """
    Runs one turn of the context-gathering conversation.

    Parameters
    ----------
    mensaje_usuario : str
        The student's current message.
    historial : list | None
        Conversation history from previous turns; None on first turn.

    Returns
    -------
    (visible_response, context_json_or_None, updated_history)

    context_json fields:
        complete        – bool, True when all five dimensions are covered
        history         – main problem and its duration
        background      – personal/family context
        beliefs         – thoughts and beliefs about the situation
        functional_impact – effect on daily life
        previous_attempts – coping strategies already tried
    """
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.65
    params["stream"] = False
    params["max_completion_tokens"] = 1200

    system_prompt = _load_prompt()

    if historial is None:
        historial = [{"role": "system", "content": system_prompt}]

    historial.append({"role": "user", "content": mensaje_usuario})

    try:
        completion = client.chat.completions.create(messages=historial, **params)
        raw = completion.choices[0].message.content or ""

        # Strip <think>...</think> reasoning before parsing output blocks
        raw_clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

        visible, context_json = _parse_output(raw_clean)

        # Store only the visible response in history (not the XML/JSON parts)
        historial.append({"role": "assistant", "content": visible})

        is_complete = bool(context_json and context_json.get("complete", False))
        print(
            f"[contexto] turno procesado — complete={is_complete}, "
            f"context={'presente' if context_json else 'ausente'}"
        )

        return visible, context_json, historial

    except Exception as e:
        print(f"[contexto] ✗ Error: {e}")
        fallback = "Lo siento, tuve un problema de conexión. ¿Podrías repetirme lo que me contabas?"
        historial.append({"role": "assistant", "content": fallback})
        return fallback, None, historial
