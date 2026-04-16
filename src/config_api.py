import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

# ==========================================
# CARGA DE VARIABLES DE ENTORNO
# ==========================================
load_dotenv()

# ==========================================
# CLIENTE GROQ (agentes de contexto, clasificación y recomendaciones)
# ==========================================
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("No se encontró GROQ_API_KEY en el archivo .env")
    _groq_client = Groq(api_key=groq_api_key)
except Exception as e:
    print(f"[config] Error de configuración Groq: {e}")
    raise e

# ==========================================
# CLIENTE OPENAI (agente evaluador)
# ==========================================
_openai_client: OpenAI | None = None
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        _openai_client = OpenAI(api_key=openai_api_key)
        print("[config] OK: OpenAI client inicializado correctamente")
    else:
        print("[config] ADVERTENCIA: OPENAI_API_KEY no encontrada - evaluador deshabilitado")
except Exception as e:
    print(f"[config] Error de configuración OpenAI: {e}")

# ==========================================
# CONFIGURACIÓN DEL MODELO GROQ Y PARÁMETROS BASE
# ==========================================
MODEL_NAME = "llama-3.3-70b-versatile"

DEFAULT_PARAMS = {
    "model":                MODEL_NAME,
    "max_completion_tokens": 4096,
    "top_p":                0.95,
    "stop":                 None,
}


def get_groq_client() -> Groq:
    """Returns the Groq client instance."""
    return _groq_client


def get_openai_client() -> OpenAI:
    """
    Returns the OpenAI client instance.
    Raises RuntimeError if OPENAI_API_KEY was not configured.
    """
    if _openai_client is None:
        raise RuntimeError(
            "OpenAI client no disponible. "
            "Configura OPENAI_API_KEY en las variables de entorno (.env)."
        )
    return _openai_client


def get_default_params() -> dict:
    """Returns a copy of the base Groq parameters dict."""
    return DEFAULT_PARAMS.copy()