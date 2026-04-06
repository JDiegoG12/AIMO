import os
import json
from src.agente_aimo import generar_respuesta_aimo
from src.agente_evaluador import evaluar_interaccion

def cargar_escenarios():
    """Carga los escenarios de prueba desde el archivo JSON."""
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'escenarios_prueba.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f" No se encontró el archivo de escenarios en {ruta_json}")
        return []

def modo_chat():
    """Modo de conversación libre (Multi-turno)."""
    print("\n" + "*"*60)
    print("💬 MODO CHAT LIBRE INICIADO")
    print("Habla con AIMO. Escribe 'salir' para volver al menú.")
    print("*"*60)
    
    historial_chat = None  # Esto mantendrá la memoria de la conversación
    
    while True:
        user_input = input("\n🧑 Tú: ")
        
        if user_input.lower() in ['salir', 'exit', 'quit']:
            break
            
        # 1. AIMO responde (y guardamos el historial actualizado)
        respuesta_aimo, historial_chat = generar_respuesta_aimo(user_input, historial_chat)
        
        # 2. El Evaluador califica el turno actual
        evaluar_interaccion(user_input, respuesta_aimo)

def modo_pruebas():
    """Modo automático: Ejecuta los escenarios definidos en el JSON."""
    escenarios = cargar_escenarios()
    
    if not escenarios:
        return
        
    print("\n" + "*"*60)
    print(f"🧪 MODO PRUEBAS INICIADO ({len(escenarios)} escenarios cargados)")
    print("*"*60)
    
    for escenario in escenarios:
        print(f"\n▶️  ESCENARIO {escenario['id_escenario']}: {escenario['estado_emocional']}")
        texto_usuario = escenario['texto_usuario']
        print(f"🧑 Usuario Simulado: {texto_usuario}")
        
        # 1. AIMO responde (pasamos historial=None para aislar cada prueba)
        respuesta_aimo, _ = generar_respuesta_aimo(texto_usuario, historial=None)
        
        # 2. El Evaluador califica la respuesta
        evaluar_interaccion(texto_usuario, respuesta_aimo)
        
        input("\nPresiona ENTER para pasar al siguiente escenario o 'Ctrl+C' para cancelar...")

def menu_principal():
    """Menú interactivo en consola."""
    while True:
        print("\n" + "="*60)
        print("🤖 PROYECTO AIMO - ENTORNO DE PRUEBAS v1.0")
        print("="*60)
        print("1. Modo Chat Libre (Interacción Manual multi-turno)")
        print("2. Modo Pruebas (Ejecutar escenarios_prueba.json)")
        print("3. Salir")
        print("="*60)
        
        opcion = input("Elige una opción (1/2/3): ")
        
        if opcion == '1':
            modo_chat()
        elif opcion == '2':
            modo_pruebas()
        elif opcion == '3':
            print("\nAIMO: ¡Cerrando entorno de pruebas! Éxitos en el proyecto.")
            break
        else:
            print("\nOpción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    menu_principal()