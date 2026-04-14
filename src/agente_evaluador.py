import os
import json
import re
from src.config_api import get_groq_client, get_default_params

# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    """Lee un archivo de prompt desde la carpeta /prompts."""
    ruta = os.path.join(os.path.dirname(__file__), '..', 'prompts', filename)
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[evaluador] ADVERTENCIA: No se encontró {ruta}")
        return ""

def _extract_json(raw: str) -> dict | None:
    """Extrae el primer objeto JSON válido de una cadena de texto."""
    if not raw:
        return None
    # Eliminar bloques markdown si el modelo los devuelve
    raw = re.sub(r'```(?:json)?', '', raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Buscar el primer { ... } balanceado
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
                        return json.loads(raw[start:i+1])
                    except json.JSONDecodeError:
                        return None
    return None

def _call_evaluator(system_prompt: str, user_content: str, label: str) -> dict | None:
    """Ejecuta una llamada G-Eval al modelo y devuelve el JSON parseado."""
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.1          # máxima consistencia
    params["stream"] = False
    params["max_completion_tokens"] = 600 # suficiente para 1 métrica + justificación

    mensajes = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]

    print(f"\n{'─'*40}")
    print(f"[G-Eval] Evaluando: {label}")
    print(f"{'─'*40}")

    try:
        completion = client.chat.completions.create(messages=mensajes, **params)
        raw = completion.choices[0].message.content
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

# ── Evaluador principal ───────────────────────────────────────────────────────

def evaluar_interaccion(mensaje_usuario: str, respuesta_aimo: str) -> dict | None:
    """
    Ejecuta 3 llamadas G-Eval independientes:
      1. AERI (perspective_taking, fantasy, personal_distress)
      2. Relevance
      3. Semantically Appropriate

    Devuelve un dict con todas las métricas + composite_score,
    o None si todas las llamadas fallan.

    Nota sobre empathic_concern (EC):
    EC fue eliminada porque 'semantically_appropriate' es un superconjunto:
    cubre la calidez y preocupación de EC, y además evalúa seguridad
    psicológica y ausencia de positividad tóxica — haciendo EC redundante.
    """
    conversacion = (
        f"Student: {mensaje_usuario}\n"
        f"AIMO: {respuesta_aimo}"
    )

    # ── 1. AERI (PT, FT, PD) ─────────────────────────────────────────────────
    aeri_prompt = _load_prompt('evaluador_v1.txt')
    aeri_result = _call_evaluator(aeri_prompt, conversacion, "AERI (PT/FT/PD)")

    # ── 2. Relevance ──────────────────────────────────────────────────────────
    rel_prompt = _load_prompt('relevance_v1.txt')
    rel_prompt_filled = rel_prompt.replace('{{User_Query}}', mensaje_usuario).replace('{{Model_Response}}', respuesta_aimo)
    rel_result = _call_evaluator(rel_prompt_filled, conversacion, "Relevance")

    # ── 3. Semantically Appropriate ───────────────────────────────────────────
    sa_prompt = _load_prompt('semantically_appropriate_v1.txt')
    sa_prompt_filled = sa_prompt.replace('{{User_Query}}', mensaje_usuario).replace('{{Model_Response}}', respuesta_aimo)
    sa_result = _call_evaluator(sa_prompt_filled, conversacion, "Semantically Appropriate")

    # ── Combinar resultados ───────────────────────────────────────────────────
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
    # Weights derived from:
    # - Xu, Z., & Jiang, J. (2024). "Multi-dimensional Evaluation of Empathetic
    #   Dialogue Responses." Findings of EMNLP 2024, pp. 2066-2087.
    #   https://doi.org/10.18653/v1/2024.findings-emnlp.113
    #   → Demonstrates that perspective-taking and cognitive engagement correlate
    #     most strongly with dialogue satisfaction → highest weight (0.30).
    # - Abd-Alrazaq, A. A., et al. (2020). "Effectiveness and Safety of Using
    #   Chatbots to Improve Mental Health: Systematic Review and Meta-Analysis."
    #   Journal of Medical Internet Research, 22(7), e16021.
    #   https://doi.org/10.2196/16021
    #   → Frames safety/appropriateness as primary evaluation criterion for
    #     mental health chatbots → semantic_appropriate weighted above fantasy.
    METRIC_WEIGHTS = {
        "perspective_taking":       0.30,
        "personal_distress":        0.20,   # inverted: (6-PD) * weight
        "relevance":                0.25,
        "semantically_appropriate": 0.15,
        "fantasy":                  0.10,
    }

    pt  = evaluation.get('perspective_taking', {}).get('score')
    ft  = evaluation.get('fantasy', {}).get('score')
    pd_ = evaluation.get('personal_distress', {}).get('score')
    rel = evaluation.get('relevance', {}).get('score')
    sa  = evaluation.get('semantically_appropriate', {}).get('score')

    weighted_sum  = 0.0
    total_weight  = 0.0

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
    evaluation['composite_score'] = composite
    evaluation['weighting_scheme'] = 'xu2024_abdAlrazaq2020'

    print(f"\n[evaluador] ✓ Composite score: {composite}/5")
    print(f"[evaluador] Métricas obtenidas: {list(evaluation.keys())}\n")

    return evaluation
