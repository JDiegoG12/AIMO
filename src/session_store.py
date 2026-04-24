"""
Session Store — AIMO (academic analysis)
─────────────────────────────────────────
Persists conversation sessions as JSON files in data/sessions/.
Designed for academic analysis: each file contains the full interaction
record including per-turn intermediate evaluations and final metrics.

Each session file: data/sessions/{session_id}.json

Schema overview:
  session_id       : str
  inicio           : ISO timestamp
  fin              : ISO timestamp (set on finalize)
  duracion_segundos: int (set on finalize)
  total_turnos     : int
  fase_final       : "gathering" | "complete"
  turnos           : list of turn records (see _turno_record)
  clasificacion    : risk classification dict (set on finalize)
  recomendaciones  : final recommendations text (set on finalize)
  evaluacion_final : G-Eval final metrics dict (set on finalize)
  metadata         : models used, flags, etc.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from src.logger import get_logger

logger = get_logger("aimo.session_store")

_SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"
_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_path(session_id: str) -> Path:
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    return _SESSIONS_DIR / f"{safe_id}.json"


def crear_sesion(session_id: str) -> dict:
    """Creates a new in-memory session record (not yet saved to disk)."""
    return {
        "session_id":        session_id,
        "inicio":            _now_iso(),
        "fin":               None,
        "duracion_segundos": None,
        "total_turnos":      0,
        "fase_final":        "gathering",
        "turnos":            [],
        "clasificacion":     None,
        "recomendaciones":   None,
        "evaluacion_final":  None,
        "metadata": {
            "modelos": {
                "contexto":             "llama-3.3-70b-versatile",
                "clasificador":         "llama-3.3-70b-versatile",
                "recomendaciones_low":  "llama-3.3-70b-versatile",
                "recomendaciones_med":  "bedrock/configured-via-env",
                "evaluador_intermedio": "gpt-3.5-turbo",
                "evaluador_final":      "gpt-4",
            },
            "compresion_activada":             False,
            "evaluacion_intermedia_habilitada": True,
        },
    }


def registrar_turno(
    record: dict,
    numero_turno: int,
    mensaje_usuario: str,
    respuesta_agente: str,
    context_snapshot: dict | None,
    evaluacion_intermedia: dict | None,
    tokens_estimados: int,
    compresion_activada: bool = False,
) -> None:
    """Appends a turn entry to the session record (in-place)."""
    if compresion_activada:
        record["metadata"]["compresion_activada"] = True

    turno = {
        "numero":              numero_turno,
        "timestamp":           _now_iso(),
        "fase":                "gathering",
        "usuario":             mensaje_usuario,
        "asistente":           respuesta_agente,
        "context_snapshot":    context_snapshot,
        "evaluacion_intermedia": evaluacion_intermedia,
        "tokens_estimados":    tokens_estimados,
    }
    record["turnos"].append(turno)
    record["total_turnos"] = len(record["turnos"])


def finalizar_sesion(
    record: dict,
    clasificacion: dict | None,
    recomendaciones: str | None,
    evaluacion_final: dict | None,
) -> None:
    """Marks the session as complete and sets final fields (in-place)."""
    fin = _now_iso()
    inicio_dt = datetime.fromisoformat(record["inicio"])
    fin_dt    = datetime.fromisoformat(fin)
    duracion  = int((fin_dt - inicio_dt).total_seconds())

    record["fin"]               = fin
    record["duracion_segundos"] = duracion
    record["fase_final"]        = "complete"
    record["clasificacion"]     = clasificacion
    record["recomendaciones"]   = recomendaciones
    record["evaluacion_final"]  = evaluacion_final


def guardar_sesion(record: dict) -> None:
    """Writes the session record to disk as JSON."""
    path = _session_path(record["session_id"])
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        logger.info("Sesión guardada: %s (%d turnos)", path.name, record["total_turnos"])
    except Exception as e:
        logger.error("Error guardando sesión %s: %s", record["session_id"], e)
