from google import genai

# Crear cliente con tu API key
client = genai.Client(api_key="AQ.Ab8RN6IvSWuUnRGF0zUXes54vAb6ERWt3nVaeyVG8hLE8BkgLw")


for m in genai.list_models():
    print(m.name, m.supported_generation_methods)

model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Respuestas preestablecidas (clave: respuesta)
respuestas_predefinidas = {
    "que es el habeas data": "El habeas data es el derecho constitucional que permite a toda persona conocer, actualizar y rectificar la información que se haya recogido sobre ella en bancos de datos.",
    "que es un contrato": "Un contrato es un acuerdo de voluntades entre dos o más partes que genera obligaciones jurídicamente exigibles.",
    "que es la estabilidad laboral reforzada": "Es la protección especial que tienen ciertos trabajadores (ej. en situación de discapacidad o embarazo) frente al despido sin autorización previa.",
}

# Palabras clave -> intención (para coincidencia más flexible)
palabras_clave = {
    "habeas data": "que es el habeas data",
    "contrato": "que es un contrato",
    "estabilidad laboral": "que es la estabilidad laboral reforzada",
}

print("El chatbot está listo! escribe 'salir' para detenerlo")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "salir":
        print("Chatbot: ¡Adiós!")
        break

    user_input_lower = user_input.lower()

    # 1. Buscar coincidencia exacta
    if user_input_lower in respuestas_predefinidas:
        print("Chatbot:", respuestas_predefinidas[user_input_lower])
        continue

    # 2. Buscar coincidencia por palabra clave
    respuesta_encontrada = None
    for clave, pregunta_match in palabras_clave.items():
        if clave in user_input_lower:
            respuesta_encontrada = respuestas_predefinidas[pregunta_match]
            break

    if respuesta_encontrada:
        print("Chatbot:", respuesta_encontrada)
        continue

    # 3. Si no hay coincidencia, usar el modelo de IA
    try:
        response = model.generate_content(user_input)
        print("Chatbot:", response.text)
    except Exception as e:
        print("Chatbot: Hubo un error al procesar tu pregunta:", e)