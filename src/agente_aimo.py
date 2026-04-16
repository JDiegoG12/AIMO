"""
AIMO Response Generator
────────────────────────
Generates AIMO's empathic responses via Groq API with two research enhancements:

MEJORA 2 — Adaptive Prompt Injection
  Theoretical basis:
  - Empathy-based design in mental health chatbots:
    Sanjeewa, R., et al. (2024). "Empathic Conversational Agent Platform
    Designs and Their Evaluation in the Context of Mental Health: Systematic
    Review." JMIR Mental Health, 11, e58974.
    https://doi.org/10.2196/58974
    → 2024 systematic review of 19 studies showing that person-centered,
      non-directive, emotionally attuned chatbot design (Rogerian principles:
      empathy, unconditional acceptance, authenticity) is the dominant
      effective architecture for mental health conversational agents.

  - Intensity-based tone adaptation (no premature advice):
    Pedamallu, H., et al. (2022). "Technology-Delivered Adaptations of
    Motivational Interviewing for Prevention and Management of Chronic
    Diseases: Scoping Review." Journal of Medical Internet Research, 24(8),
    e35283. https://doi.org/10.2196/35283
    → Justifies withholding directive suggestions at high emotional activation;
      reflective listening and validation take priority until readiness stage.

  - Academic topic module:
    Barbayannis, G., et al. (2022). "Academic Stress and Mental Well-Being
    in College Students: Correlations, Affected Groups, and COVID-19."
    Frontiers in Psychology, 13, 886344.
    https://doi.org/10.3389/fpsyg.2022.886344
    → Empirical study (n=843) showing academic stress is the dominant stressor
      in college students (r=0.53 with poor mental health), motivating a
      dedicated tone module that avoids reinforcing perfectionism.

MEJORA 3 — Session Memory Summarizer
  Theoretical basis:
  - Wang, Q., et al. (2023). "Recursively Summarizing Enables Long-Term
    Dialogue Memory in Large Language Models." Neurocomputing (accepted).
    https://doi.org/10.48550/arXiv.2308.15022
    → Proposes recursive summarization of conversation history in LLMs as
      the optimal strategy for maintaining coherence across long dialogues,
      outperforming flat truncation — directly implements the same pattern
      used in AIMO's session compressor.
"""

import os
from src.config_api import get_groq_client, get_default_params

# ── Mejora 2: Tone modules ────────────────────────────────────────────────────
# Keys: (emotion, level) where level = "high" | "medium" | "any"
#       (topic,   "topic") for thematic context
# "high"   → intensity >= 4
# "medium" → intensity 2-3
# "any"    → any intensity (emotion always applies, e.g. loneliness)

TONE_MODULES = {
    ("sadness",   "high"):   "Use slow, gentle pacing. Prioritize emotional presence over suggestions. Omit the 'simple suggestion' component if intensity >= 4.",
    ("anxiety",   "high"):   "Use grounding, present-focused language. Avoid future projections. Reduce the reflection component, expand validation.",
    ("anger",     "medium"): "Validate the frustration before any reframe. Do not redirect emotion — let it land first.",
    ("overwhelm", "high"):   "Break response into very small, manageable language. Avoid lists of suggestions.",
    ("loneliness","any"):    "Emphasize being heard and not being alone. Delay any action-oriented suggestion.",
    ("academic",  "topic"):  "Acknowledge academic pressure without reinforcing perfectionism or productivity pressure.",
    ("social",    "topic"):  "Acknowledge relational complexity without taking sides or making assumptions.",
}


def _construir_prompt_adaptativo(base_prompt: str, clasificacion: dict | None) -> str:
    """
    Injects tone modules at the end of the base system prompt based on the
    emotional classification from agente_clasificador.

    Combines: emotional module (by emotion + intensity level) + topic module.
    If crisis_signal is True, appends a safety override directive.
    Returns base_prompt unchanged when clasificacion is None or no match.
    """
    if not clasificacion:
        return base_prompt

    emotion   = clasificacion.get("emotion", "neutral")
    intensity = int(clasificacion.get("intensity", 2))
    topic     = clasificacion.get("topic", "unknown")
    crisis    = bool(clasificacion.get("crisis_signal", False))

    modules = []

    # Determine intensity tier
    if intensity >= 4:
        level = "high"
    elif intensity >= 2:
        level = "medium"
    else:
        level = "low"

    # Emotional module: try level-specific, then "any"
    em_key = (emotion, level)
    if em_key in TONE_MODULES:
        modules.append(TONE_MODULES[em_key])
    elif (emotion, "any") in TONE_MODULES:
        modules.append(TONE_MODULES[(emotion, "any")])

    # Topic module
    topic_key = (topic, "topic")
    if topic_key in TONE_MODULES:
        modules.append(TONE_MODULES[topic_key])

    # Crisis signal override (highest priority — appended last so LLM sees it
    # at the end of the system prompt where it carries the most weight)
    if crisis:
        modules.append(
            "PRIORITY OVERRIDE: The student may be in crisis. Lead with immediate "
            "compassionate presence. Gently encourage them to speak with a campus "
            "counselor or mental health professional. Omit practical suggestions "
            "and focus entirely on emotional safety and connection."
        )

    if not modules:
        return base_prompt

    directive = " ".join(modules)
    return base_prompt + f"\n\nCURRENT CONTEXT DIRECTIVE:\n{directive}"


# ── Mejora 3: Session Memory Summarizer ──────────────────────────────────────

def _comprimir_historial(historial: list, client, base_params: dict) -> list:
    """
    Compresses conversation history when it exceeds 10 messages.

    Strategy (Wang et al., 2023 — recursive summarization):
    - Generates a 3-sentence structured summary focused on:
        (1) main emotional theme
        (2) key personal facts shared by the student
        (3) tone and rapport established
    - Reconstructs history as: [system_prompt, summary_msg, last_4_msgs]
      preserving the 2 most recent complete turns for immediate context.
    """
    compress_params = base_params.copy()
    compress_params["temperature"] = 0.1
    compress_params["max_completion_tokens"] = 150
    compress_params["stream"] = False

    compress_system = (
        "Summarize this emotional support conversation in 3 sentences maximum. "
        "Focus ONLY on: (1) main emotional theme, (2) key personal facts shared "
        "by the student, (3) tone and rapport established. "
        "Do NOT include any identifying details. "
        "Output only the summary, no preamble."
    )

    # Exclude system messages from the conversation text
    convo_msgs = [m for m in historial if m["role"] != "system"]
    convo_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in convo_msgs
    )

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": compress_system},
                {"role": "user",   "content": convo_text},
            ],
            **compress_params,
        )
        resumen = completion.choices[0].message.content.strip()
        print(f"[aimo] ✓ Historial comprimido — resumen: {resumen[:80]}...")
    except Exception as e:
        print(f"[aimo] ✗ Error al comprimir historial: {e}")
        resumen = "Previous conversation context unavailable."

    # Preserve the original (non-summary) system message
    system_msg = next(
        (m for m in historial
         if m["role"] == "system"
         and not m["content"].startswith("[SESSION SUMMARY")),
        None,
    )

    summary_msg = {
        "role": "system",
        "content": f"[SESSION SUMMARY — previous turns]: {resumen}",
    }

    # Keep last 4 non-system messages (= 2 complete user/assistant turns)
    last_4 = convo_msgs[-4:]

    new_historial = []
    if system_msg:
        new_historial.append(system_msg)
    new_historial.append(summary_msg)
    new_historial.extend(last_4)

    return new_historial


# ── Core functions ────────────────────────────────────────────────────────────

def cargar_prompt_aimo() -> str:
    """Reads the AIMO system prompt from the .txt file."""
    ruta_prompt = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'aimo_v1.txt')
    try:
        with open(ruta_prompt, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de prompt en {ruta_prompt}")
        return "Actúa como un asistente empático."


def generar_respuesta_aimo(
    mensaje_usuario: str,
    historial: list | None = None,
    clasificacion: dict | None = None,
) -> tuple[str, list]:
    """
    Generates AIMO's empathic response via Groq API (streaming).

    Parameters
    ----------
    mensaje_usuario : str
        The user's current message.
    historial : list | None
        Existing conversation history. Initialized on first call.
    clasificacion : dict | None
        Emotional classification from agente_clasificador.
        When provided, the system prompt is adaptively modified for this turn.

    Returns
    -------
    (response_text, updated_history)
    """
    client = get_groq_client()
    params = get_default_params()
    params["temperature"] = 0.6
    params["stream"] = True

    base_prompt = cargar_prompt_aimo()
    adapted_prompt = _construir_prompt_adaptativo(base_prompt, clasificacion)

    if historial is None:
        # First turn: initialize with adapted system prompt
        historial = [{"role": "system", "content": adapted_prompt}]
    else:
        # Continuing session: re-adapt the system prompt for this turn.
        # Update only the base system message (not a SESSION SUMMARY message).
        if historial and historial[0]["role"] == "system" \
                and not historial[0]["content"].startswith("[SESSION SUMMARY"):
            historial[0] = {"role": "system", "content": adapted_prompt}

    # Mejora 3: compress history when it grows beyond 10 messages
    # (Wang et al., 2023 — recursive summarization strategy)
    if len(historial) > 10:
        historial = _comprimir_historial(historial, client, params)

    historial.append({"role": "user", "content": f"USER: {mensaje_usuario}"})

    print("\n🤖 AIMO: ", end="", flush=True)
    respuesta_completa = ""

    try:
        completion = client.chat.completions.create(
            messages=historial,
            **params,
        )

        for chunk in completion:
            contenido = chunk.choices[0].delta.content or ""
            print(contenido, end="", flush=True)
            respuesta_completa += contenido

        print()

        historial.append({"role": "assistant", "content": respuesta_completa})
        return respuesta_completa, historial

    except Exception as e:
        print(f"\nError al generar respuesta de AIMO: {e}")
        return "Lo siento, tuve un problema de conexión. ¿Podrías repetirlo?", historial
