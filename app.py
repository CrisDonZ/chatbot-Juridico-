import csv
import os
from flask import Flask, request, jsonify, render_template
from google import genai
import fitz  # pymupdf


client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
app = Flask(__name__)

# Respuestas preestablecidas (clave: respuesta)
respuestas_predefinidas = {
    "que es el habeas data": "El habeas data es el derecho constitucional que permite a toda persona conocer, actualizar y rectificar la información que se haya recogido sobre ella en bancos de datos.",
    "que es un contrato": "Un contrato es un acuerdo de voluntades entre dos o más partes que genera obligaciones jurídicamente exigibles.",
    "que es la estabilidad laboral reforzada": "Es la protección especial que tienen ciertos trabajadores (ej. en situación de discapacidad o embarazo) frente al despido sin autorización previa.",
}

# Palabras clave -> intención
palabras_clave = {
    "habeas data": "que es el habeas data",
    "contrato": "que es un contrato",
    "estabilidad laboral": "que es la estabilidad laboral reforzada",
}

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "sentencias.csv")

# Palabras que indican que la pregunta es de tema jurídico/jurisprudencial
PALABRAS_JURIDICAS = [
    "ley", "leyes", "derecho", "jurídic", "juridic", "sentencia", "fallo",
    "corte", "constitucional", "tutela", "habeas", "contrato", "demanda",
    "norma", "código", "codigo", "decreto", "resolución", "resolucion",
    "jurisprudencia", "tribunal", "juez", "juzgado", "proceso", "abogado",
    "delito", "pena", "indemnización", "indemnizacion", "violencia",
    "víctima", "victima", "comisaría", "comisaria", "estabilidad laboral",
    "derechos", "obligación", "obligacion", "responsabilidad civil",
    "penal", "civil", "laboral", "administrativo", "trabajo", "despido",
    "protección", "proteccion", "debida diligencia", "estado","hola",
]


def es_pregunta_juridica(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(palabra in texto_lower for palabra in PALABRAS_JURIDICAS)


MENSAJE_FUERA_DE_TEMA = (
    "Lo siento, solo puedo responder preguntas relacionadas con derecho y "
    "jurisprudencia. Por favor reformula tu pregunta dentro de ese contexto."
)


def cargar_contexto_csv(path: str) -> str:
    """Lee el CSV y lo convierte en texto plano para usar como contexto del modelo."""
    bloques = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            bloque = "\n".join(f"{clave}: {valor}" for clave, valor in fila.items())
            bloques.append(bloque)
    return "\n\n---\n\n".join(bloques)


def cargar_contexto_pdf(path: str) -> str:
    doc = fitz.open(path)
    return "\n\n".join(page.get_text() for page in doc)

def cargar_todo_contexto(carpeta: str) -> str:
    bloques = []
    for archivo in os.listdir(carpeta):
        ruta = os.path.join(carpeta, archivo)
        if archivo.endswith(".csv"):
            bloques.append(f"[FUENTE: {archivo}]\n{cargar_contexto_csv(ruta)}")
        elif archivo.endswith(".pdf"):
            bloques.append(f"[FUENTE: {archivo}]\n{cargar_contexto_pdf(ruta)}")
    return "\n\n===\n\n".join(bloques)


# Se carga una sola vez al arrancar el servidor
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONTEXTO_SENTENCIAS = cargar_todo_contexto(DATA_DIR)

SYSTEM_PROMPT = (
    "Eres un asistente jurídico especializado en derecho jurisprudencial colombiano sobre "
    "violencia intrafamiliar y debida diligencia estatal. SOLO respondes preguntas "
    "relacionadas con derecho, leyes, jurisprudencia o temas jurídicos en general. "
    "Si la pregunta del usuario NO tiene relación con derecho o jurisprudencia, "
    "responde EXACTAMENTE: "
    f"\"{MENSAJE_FUERA_DE_TEMA}\" y no agregues nada más.\n\n"
    "Si la pregunta SÍ es jurídica, responde ÚNICAMENTE con base en las sentencias "
    "proporcionadas a continuación. Si la pregunta jurídica no puede responderse "
    "con esa información, dilo claramente y no inventes datos. Si la respuesta son mensajes de saludos, despedidas, agradecimientos o charla amistosa responde amablemente y educadamente, además usa lenguaje tuteando al usuario siempre\n\n"
    "SENTENCIAS DISPONIBLES:\n\n"
    f"{CONTEXTO_SENTENCIAS}"
)


def obtener_respuesta(user_input: str) -> str:
    user_input_lower = user_input.strip().lower()

    # 1. Coincidencia exacta
    if user_input_lower in respuestas_predefinidas:
        return respuestas_predefinidas[user_input_lower]

    # 2. Coincidencia por palabra clave
    for clave, pregunta_match in palabras_clave.items():
        if clave in user_input_lower:
            return respuestas_predefinidas[pregunta_match]

    # 3. Filtro de tema: si claramente no es jurídico, rechazar sin gastar tokens
    if not es_pregunta_juridica(user_input_lower):
        return MENSAJE_FUERA_DE_TEMA

    # 4. Modelo de IA con contexto del CSV (RAG simple)
    try:
        prompt_completo = (
            f"{SYSTEM_PROMPT}\n\n"
            f"PREGUNTA DEL USUARIO:\n{user_input}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt_completo,
        )
        return response.text
    except Exception as e:
        return f"Hubo un error al procesar tu pregunta: {e}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    if not user_input.strip():
        return jsonify({"reply": "Por favor escribe una pregunta."})

    reply = obtener_respuesta(user_input)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)