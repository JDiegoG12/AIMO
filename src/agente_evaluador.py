"""
G-Eval Evaluator — AIMO (powered by OpenAI GPT)
─────────────────────────────────────────────────
Runs three independent LLM-as-a-Judge evaluations using OpenAI's GPT API.
Evaluation is triggered ONLY when the final recommendations are delivered —
NOT on every conversational turn.

Input:
  - context_texto     : JSON string with the structured context gathered by
                        agente_contexto (history, background, beliefs, etc.)
  - clasificacion_texto: JSON string with the risk classification from
                        agente_clasificador (risk_level, signals, action)

Metrics:
  1. AERI          — perspective_taking, fantasy, personal_distress
  2. Relevance     — how well the output addresses the student's situation
  3. Semantically Appropriate — safety, empathy, psychological suitability

Composite score uses the same weighted scheme as previous versions:
  PT=30%, REL=25%, PD=20%, SA=15%, FT=10%  (Xu & Jiang 2024; Abd-Alrazaq 2020)
"""

import os
import json
import re
from src.config_api import get_openai_client

# OpenAI model used for all evaluation calls
OPENAI_EVAL_MODEL = "gpt-4o-mini"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    """Loads an evaluation prompt from the /prompts directory."""
    ruta = os.path.join(os.path.dirname(__file__), '..', 'prompts', filename)
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[evaluador] ADVERTENCIA: No se encontró {ruta}")
        return ""


def _extract_json(raw: str) -> dict | None:
    """Extracts the first valid JSON object from a string."""
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


def _call_evaluator(system_prompt: str, user_content: str, label: str) -> dict | None:
    """Executes a single G-Eval call via OpenAI and returns the parsed JSON."""
    try:
        client = get_openai_client()
    except RuntimeError as e:
        print(f"  [SKIP] {label}: {e}")
        return None

    mensajes = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]

    print(f"\n{'─'*40}")
    print(f"[G-Eval/OpenAI] Evaluando: {label}")
    print(f"{'─'*40}")

    try:
        completion = client.chat.completions.create(
            model=OPENAI_EVAL_MODEL,
            messages=mensajes,
            temperature=0.1,
            max_tokens=600,
        )
        raw = completion.choices[0].message.content or ""
        print(f"  Raw → {raw[:200]}{'...' if len(raw) > 200 else ''}")
        result = _extract_json(raw)
        if result:
            print(f"  ✓ {label}: score={result.get('score')}")
        else:
            print(f"  ✗ No se pudo parsear JSON para {label}")
        return result
    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
        return None


# ── Main evaluator ────────────────────────────────────────────────────────────

def evaluar_interaccion(contexto_texto: str, clasificacion_texto: str) -> dict | None:
    """
    Runs 3 independent G-Eval calls using OpenAI GPT.

    Called ONLY when the final recommendations are generated.

    Parameters
    ----------
    contexto_texto : str
        JSON string of the structured context from agente_contexto.
    clasificacion_texto : str
        JSON string of the risk classification from agente_clasificador.

    Returns
    -------
    dict with all metrics + composite_score, or None if all calls fail.
    """
    # Combined input passed to every evaluator
    contenido_eval = (
        f"Contexto recopilado del estudiante:\n{contexto_texto}\n\n"
        f"Clasificación de riesgo psicológico:\n{clasificacion_texto}"
    )

    # ── 1. AERI (PT, FT, PD) ─────────────────────────────────────────────────
    aeri_prompt  = _load_prompt('evaluador_v1.txt')
    aeri_result  = _call_evaluator(aeri_prompt, contenido_eval, "AERI (PT/FT/PD)")

    # ── 2. Relevance ──────────────────────────────────────────────────────────
    rel_prompt = _load_prompt('relevance_v1.txt')
    rel_prompt_filled = (
        rel_prompt
        .replace('{{User_Query}}',     contexto_texto)
        .replace('{{Model_Response}}', clasificacion_texto)
    )
    rel_result = _call_evaluator(rel_prompt_filled, contenido_eval, "Relevance")

    # ── 3. Semantically Appropriate ───────────────────────────────────────────
    sa_prompt = _load_prompt('semantically_appropriate_v1.txt')
    sa_prompt_filled = (
        sa_prompt
        .replace('{{User_Query}}',     contexto_texto)
        .replace('{{Model_Response}}', clasificacion_texto)
    )
    sa_result = _call_evaluator(sa_prompt_filled, contenido_eval, "Semantically Appropriate")

    # ── Combine results ───────────────────────────────────────────────────────
    evaluation = {}

    if aeri_result:
        for key in ('perspective_taking', 'fantasy', 'personal_distress'):
            if key in aeri_result:
                evaluation[key] = aeri_result[key]

    if rel_result and 'score' in rel_result:
        evaluation['relevance'] = rel_result

    if sa_result and 'score' in sa_result:
        evaluation['semantically_appropriate'] = sa_result

    if not evaluation:
        print("[evaluador] ✗ Ninguna métrica disponible — devolviendo None")
        return None

    # ── Composite score (weighted) ────────────────────────────────────────────
    METRIC_WEIGHTS = {
        "perspective_taking":        0.30,
        "personal_distress":         0.20,   # inverted: (6 - score) * weight
        "relevance":                 0.25,
        "semantically_appropriate":  0.15,
        "fantasy":                   0.10,
    }

    pt  = evaluation.get('perspective_taking', {}).get('score')
    ft  = evaluation.get('fantasy',            {}).get('score')
    pd_ = evaluation.get('personal_distress',  {}).get('score')
    rel = evaluation.get('relevance',          {}).get('score')
    sa  = evaluation.get('semantically_appropriate', {}).get('score')

    weighted_sum = 0.0
    total_weight = 0.0

    if pt  is not None:
        weighted_sum += pt  * METRIC_WEIGHTS["perspective_taking"]
        total_weight += METRIC_WEIGHTS["perspective_taking"]
    if ft  is not None:
        weighted_sum += ft  * METRIC_WEIGHTS["fantasy"]
        total_weight += METRIC_WEIGHTS["fantasy"]
    if pd_ is not None:
        weighted_sum += (6 - pd_) * METRIC_WEIGHTS["personal_distress"]
        total_weight += METRIC_WEIGHTS["personal_distress"]
    if rel is not None:
        weighted_sum += rel * METRIC_WEIGHTS["relevance"]
        total_weight += METRIC_WEIGHTS["relevance"]
    if sa  is not None:
        weighted_sum += sa  * METRIC_WEIGHTS["semantically_appropriate"]
        total_weight += METRIC_WEIGHTS["semantically_appropriate"]

    composite = round(weighted_sum / total_weight, 2) if total_weight > 0 else None
    evaluation['composite_score']   = composite
    evaluation['weighting_scheme']  = 'xu2024_abdAlrazaq2020'

    print(f"\n[evaluador] ✓ Composite score: {composite}/5")
    print(f"[evaluador] Métricas obtenidas: {list(evaluation.keys())}\n")

    return evaluation
