"""
Emotional State Classifier — AIMO pre-processor
────────────────────────────────────────────────
Makes ONE Groq call before generar_respuesta_aimo to classify the user's
emotional state, intensity, crisis signal, and topic.

Theoretical basis:
- Emotion taxonomy & prevalence in university students:
  Sheldon, E., et al. (2021). "Prevalence and risk factors for mental health
  problems in university undergraduate students: A systematic review with
  meta-analysis." Journal of Affective Disorders, 287, 282-292.
  https://doi.org/10.1016/j.jad.2021.03.054
  → Validates depression, anxiety, loneliness, and related affective states
    as the most prevalent emotional categories in undergraduate populations.

- Intensity-based response calibration:
  Pedamallu, H., et al. (2022). "Technology-Delivered Adaptations of
  Motivational Interviewing for the Prevention and Management of Chronic
  Diseases: Scoping Review." Journal of Medical Internet Research, 24(8),
  e35283. https://doi.org/10.2196/35283
  → Justifies calibrating empathic response to emotional activation level:
    reflective listening at high intensity, directive suggestions only when
    the student is in a readiness state.
"""

import json
import re
from src.config_api import get_groq_client, get_default_params

_CLASSIFIER_SYSTEM_PROMPT = """\
You are an emotional state classifier for a university student support chatbot.
Analyze the student's message and respond ONLY with a JSON object in this exact format:
{"emotion": "<sadness|anxiety|anger|overwhelm|loneliness|neutral>",
 "intensity": <1-5>,
 "crisis_signal": <true|false>,
 "topic": "<academic|social|family|identity|unknown>"}

Rules:
- emotion: choose the single most dominant affect
- intensity: 1=barely present, 5=overwhelming
- crisis_signal: true ONLY if there are explicit or strongly implied indicators
  of self-harm, suicidal ideation, or acute safety risk
- topic: primary life domain of the stressor
No explanation, no preamble — JSON only."""

_FALLBACK: dict = {
    "emotion": "neutral",
    "intensity": 2,
    "crisis_signal": False,
    "topic": "unknown",
}


def _extract_json(raw: str) -> dict | None:
    """Extract the first valid JSON object from a string."""
    if not raw:
        return None
    raw = re.sub(r'```(?:json)?', '', raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find('{')
        if start == -1:
            return None
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
                        return None
    return None


def clasificar_estado_emocional(
    mensaje_usuario: str,
    historial_reciente: list,
) -> dict:
    """
    Classifies the emotional state of the user message.

    Uses only the last 2 messages from history for context (not the full
    history) to keep the call lightweight and focused on the current turn.

    Parameters
    ----------
    mensaje_usuario : str
        The user's current message.
    historial_reciente : list
        Full session history; only the last 2 entries are used.

    Returns
    -------
    dict with keys: emotion, intensity, crisis_signal, topic.
    Falls back to neutral defaults on any failure.
    """
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.1
    params["max_completion_tokens"] = 600   # qwen3 uses <think> tokens before JSON
    params["stream"] = False

    # Use only the last 2 messages for context (lightweight)
    context_msgs = historial_reciente[-2:] if historial_reciente else []

    messages = [{"role": "system", "content": _CLASSIFIER_SYSTEM_PROMPT}]
    messages.extend(context_msgs)
    messages.append({"role": "user", "content": mensaje_usuario})

    try:
        completion = client.chat.completions.create(messages=messages, **params)
        raw = completion.choices[0].message.content
        result = _extract_json(raw)

        if result and "emotion" in result and "intensity" in result:
            result["crisis_signal"] = bool(result.get("crisis_signal", False))
            result.setdefault("topic", "unknown")
            print(
                f"[clasificador] ✓ emotion={result['emotion']} "
                f"intensity={result['intensity']} "
                f"crisis={result['crisis_signal']} "
                f"topic={result['topic']}"
            )
            return result

        print("[clasificador] ✗ JSON inválido — usando fallback")
        return _FALLBACK.copy()

    except Exception as e:
        print(f"[clasificador] ✗ Error: {e} — usando fallback")
        return _FALLBACK.copy()
