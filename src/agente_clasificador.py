"""
Clinical Risk Classifier — AIMO pipeline
─────────────────────────────────────────
Receives the structured context JSON from agente_contexto and classifies the
psychological risk level using prompts/aimo_classifier.txt.

Theoretical basis:
- Conservative risk escalation heuristics:
  Suicide Prevention Resource Center (2014). "Assessing and Managing Suicide
  Risk: Core Competencies for Mental Health Professionals."
  → Justifies the "when in doubt, escalate" decision rule used by the prompt.

- Functional impairment as triage criterion:
  Üstün, T. B., et al. (2010). "Measuring health and disability: Manual for
  WHO Disability Assessment Schedule." WHO Press.
  → Frames daily-life functional impact as a primary severity indicator.
"""

import os
import re
import json
from src.config_api import get_groq_client, get_default_params
from src.logger import get_logger

logger = get_logger("aimo.clasificador")


def _load_prompt() -> str:
    ruta = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'aimo_classifier.txt')
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("No se encontró aimo_classifier.txt")
        return ""


def _extract_json(raw: str) -> dict | None:
    if not raw:
        return None
    raw = re.sub(r'```(?:json)?', '', raw).strip()
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
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


_FALLBACK: dict = {
    "risk_level": "medium",
    "signals": ["información insuficiente para evaluación precisa"],
    "recommended_action": "caution",
}


def clasificar_riesgo(context_data: dict) -> dict:
    """
    Classifies the psychological risk level from the gathered context.

    Returns dict with: risk_level, signals, recommended_action.
    Falls back to 'medium / caution' on any failure.
    """
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.1
    params["stream"] = False
    params["max_completion_tokens"] = 600

    system_prompt = _load_prompt()
    if not system_prompt:
        logger.warning("Prompt de clasificador vacío — usando fallback")
        return _FALLBACK.copy()

    context_for_classifier = {k: v for k, v in context_data.items() if k != 'complete'}
    input_text = json.dumps(context_for_classifier, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": input_text},
    ]

    try:
        completion = client.chat.completions.create(messages=messages, **params)
        raw = completion.choices[0].message.content or ""
        result = _extract_json(raw)

        if result and "risk_level" in result:
            logger.info(
                "Clasificación: risk_level=%s, action=%s",
                result["risk_level"], result.get("recommended_action"),
            )
            return result

        logger.warning("JSON de clasificación inválido — usando fallback")
        return _FALLBACK.copy()

    except Exception as e:
        logger.error("Error en clasificar_riesgo: %s — usando fallback", e)
        return _FALLBACK.copy()
