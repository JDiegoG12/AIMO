# Proyecto AIMO - Entorno de Pruebas v1.0

AIMO es un prototipo académico de asistente conversacional basado en Inteligencia Artificial Generativa, diseñado para brindar acompañamiento emocional inicial a estudiantes universitarios.

Este repositorio contiene la **Primera Versión (Consola)**, construida bajo una arquitectura de **Dos Agentes (Generador + Evaluador)** utilizando la API de Groq y el modelo `qwen3-32b`.

### Equipo Desarrollador

- Ana Sofia Arango Yanza
- Juan David Vela Coronado
- Juan Diego Gomez Garces

**Profesor:** Nestor Milciades Diaz Marino  
**Universidad del Cauca** - Facultad de Ingeniería Electrónica y Telecomunicaciones

---

## Arquitectura del Sistema (LLM-as-a-Judge)

Para cumplir con la metodología de evaluación iterativa del proyecto, el sistema se divide en dos agentes que interactúan en tiempo real:

1. **Agente 1 (AIMO):** Genera la respuesta empática al usuario (con _streaming_) basándose en reglas estrictas: Validación + Reflexión + Sugerencia.
2. **Agente 2 (G-Eval):** Actúa como un juez estricto. Lee la conversación y califica la "Empatía Cognitiva" de AIMO del 1 al 5, entregando una justificación de por qué dio esa nota.

---

## Requisitos y Configuración Inicial

### 1. Clonar el repositorio y preparar el entorno

Asegúrate de tener Python 3.8+ instalado. Es altamente recomendable usar un entorno virtual.

```bash
# Crear entorno virtual (Opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar las librerías necesarias
pip install groq python-dotenv
```

### 2. Configurar la API Key (Archivo `.env`)

Para no tener que lidiar con variables de entorno en el sistema operativo, utilizamos la librería `dotenv`.
Crea un archivo llamado `.env` en la raíz del proyecto (al mismo nivel que `main_tester.py`) y pega tu API Key de Groq:

```env
GROQ_API_KEY=gsk_tu_api_key_aqui
```

_(Nota: El archivo `.env` ya está agregado al `.gitignore` para no exponer las credenciales)._

---

## ¿Cómo ejecutar el proyecto?

Para iniciar el orquestador, corre el siguiente comando en la raíz del proyecto:

```bash
python main_tester.py
```

Se desplegará un menú interactivo con dos opciones:

- **Opción 1 (Modo Chat Libre):** Permite tener una conversación multi-turno con AIMO. Al finalizar cada respuesta tuya, el Evaluador G-Eval analizará el turno y le pondrá una nota a AIMO. Ideal para pruebas de estrés.
- **Opción 2 (Modo Pruebas Automáticas):** Lee automáticamente los casos definidos en `data/escenarios_prueba.json`, genera las respuestas y las evalúa. Ideal para pruebas de regresión.

---

## Estructura del Repositorio

```text
aimo_project/
│
├── data/
│   └── escenarios_prueba.json  # Casos de prueba (Ansiedad, Tristeza, etc.)
│
├── prompts/
│   ├── aimo_v1.txt             # System Prompt principal de AIMO.
│   └── evaluador_v1.txt        # Rúbrica G-Eval de la página 21.
│
├── src/
│   ├── config_api.py           # Configuración centralizada de Groq y dotenv.
│   ├── agente_aimo.py          # Lógica de generación con Streaming.
│   └── agente_evaluador.py     # Lógica de evaluación sin streaming (juez).
│
├── .env                        # (No subir) Tus credenciales de API.
└── main_tester.py              # Script principal (Orquestador).
```

---

## Flujo de Trabajo para el Equipo (Iteración de Prompts)

El objetivo de esta fase es lograr que el **Agente 2 (Evaluador)** le dé consistentemente a AIMO puntuaciones de **4 o 5**.

Si al correr las pruebas ven que el evaluador le da una nota baja a AIMO:

1. Lean la justificación que da el Evaluador en la consola.
2. Abran el archivo `prompts/aimo_v1.txt`.
3. Ajusten las reglas, agreguen restricciones o mejoren el _Few-shot example_ basándose en el feedback.
4. Guarden el archivo y vuelvan a correr `python main_tester.py` (Opción 2).

¡No es necesario modificar el código en Python, toda la personalidad se controla desde los archivos `.txt`!
