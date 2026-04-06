import os
from src.config_api import get_groq_client, get_default_params

def cargar_prompt_evaluador():
    """Lee la rúbrica G-Eval desde el archivo .txt"""
    ruta_prompt = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'evaluador_v1.txt')
    try:
        with open(ruta_prompt, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de prompt en {ruta_prompt}")
        return "Evalúa si la respuesta es empática del 1 al 5." # Fallback

def evaluar_interaccion(mensaje_usuario, respuesta_aimo):
    """
    Agente 2: Toma la interacción, la envía a Groq usando la rúbrica G-Eval,
    y devuelve la retroalimentación estructurada.
    """
    client = get_groq_client()
    params = get_default_params()
    
    # Configuraciones específicas para el Evaluador
    # Temperatura baja (0.2) para que sea consistente, objetivo y estricto
    params["temperature"] = 0.2 
    params["stream"] = False # No queremos streaming, queremos leer el reporte completo

    # Formateamos el input para que el evaluador no se confunda
    input_evaluacion = (
        f"--- CONVERSACIÓN A EVALUAR ---\n"
        f"Estudiante: {mensaje_usuario}\n"
        f"AIMO: {respuesta_aimo}\n"
        f"------------------------------"
    )

    mensajes = [
        {"role": "system", "content": cargar_prompt_evaluador()},
        {"role": "user", "content": input_evaluacion}
    ]

    print("\n" + "="*50)
    print("EVALUADOR G-EVAL ANALIZANDO LA RESPUESTA...")
    print("="*50)

    try:
        completion = client.chat.completions.create(
            messages=mensajes,
            **params
        )
        
        evaluacion = completion.choices[0].message.content
        
        print(evaluacion)
        print("="*50 + "\n")
        
        return evaluacion

    except Exception as e:
        print(f"Error al generar la evaluación: {e}")
        return None