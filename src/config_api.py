import os
from dotenv import load_dotenv
from groq import Groq

# ==========================================
# CARGA DE VARIABLES Y CLIENTE
# ==========================================
# Carga las variables del archivo .env oculto
load_dotenv()

# Inicializa el cliente. Groq buscará automáticamente la variable GROQ_API_KEY
try:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY en el archivo .env")
        
    client = Groq(api_key=api_key)
except Exception as e:
    print(f"Error de configuración: {e}")
    raise e

# ==========================================
# CONFIGURACIÓN DEL MODELO Y PARÁMETROS BASE
# ==========================================
# Extraídos de tu snippet de código
MODEL_NAME = "qwen/qwen3-32b"  

# Parámetros por defecto compartidos
DEFAULT_PARAMS = {
    "model": MODEL_NAME,
    "max_completion_tokens": 4096,
    "top_p": 0.95,
    "stop": None
}

def get_groq_client():
    """Devuelve la instancia del cliente para ser usada por los agentes."""
    return client

def get_default_params():
    """Devuelve el diccionario con los parámetros base."""
    return DEFAULT_PARAMS.copy()