import os
from src.config_api import get_groq_client, get_default_params

def cargar_prompt_aimo():
    """Lee el system prompt de AIMO desde el archivo .txt"""
    ruta_prompt = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'aimo_v1.txt')
    try:
        with open(ruta_prompt, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de prompt en {ruta_prompt}")
        return "Actúa como un asistente empático." # Fallback de emergencia

def generar_respuesta_aimo(mensaje_usuario, historial=None):
    """
    Se comunica con Groq para generar la respuesta de AIMO.
    Utiliza streaming para imprimir en consola en tiempo real.
    """
    client = get_groq_client()
    params = get_default_params()
    
    # Configuraciones específicas para AIMO basadas en tu snippet
    params["temperature"] = 0.6
    params["stream"] = True

    # Si no hay historial previo, lo inicializamos con el system prompt
    if historial is None:
        historial = [
            {"role": "system", "content": cargar_prompt_aimo()}
        ]
    
    # Agregamos el nuevo mensaje del usuario al historial
    historial.append({"role": "user", "content": f"USER: {mensaje_usuario}"})

    print("\n🤖 AIMO: ", end="", flush=True)
    
    respuesta_completa = ""
    
    try:
        # Llamada a la API
        completion = client.chat.completions.create(
            messages=historial,
            **params
        )

        # Procesamiento del streaming (letra por letra)
        for chunk in completion:
            contenido = chunk.choices[0].delta.content or ""
            print(contenido, end="", flush=True)
            respuesta_completa += contenido
            
        print() # Salto de línea al terminar de escribir
        
        # Agregamos la respuesta de AIMO al historial para mantener el contexto
        historial.append({"role": "assistant", "content": respuesta_completa})
        
        return respuesta_completa, historial

    except Exception as e:
        print(f"\nError al generar respuesta de AIMO: {e}")
        return "Lo siento, tuve un problema de conexión. ¿Podrías repetirlo?", historial