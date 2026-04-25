"""
DEPRECATED — agente_aimo.py
─────────────────────────────
This module was the v1 response generator. Its logic has been absorbed into
the v2 pipeline:

  - Adaptive tone injection (TONE_MODULES, _construir_prompt_adaptativo)
    → now in src/agente_contexto.py

  - Session memory compression (_comprimir_historial)
    → now in src/agente_contexto.py (token-based threshold)

  - Simple response generation (generar_respuesta_aimo)
    → replaced by the 3-stage pipeline in api.py
      (agente_contexto → agente_clasificador → agente_recomendaciones)

This file is kept only to avoid breaking any external references during
transition. Do not import from it in new code.
"""
