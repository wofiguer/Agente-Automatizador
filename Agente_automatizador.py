# -*- coding: utf-8 -*-
"""
Agente de Automatización para Consultorios Médicos (Core MVP)
Versión de Simulación Gratuita - Con Buscador Tolerante a Errores Ortográficos
"""

import unicodedata
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Core Agente Médico - Producción Local")

class MensajeEntrada(BaseModel):
    id_whatsapp: str
    nombre_paciente: str
    mensaje: str
    historial_contexto: str = ""

# Base de datos extraída idéntica a tu tabla de Excel
BASE_DATOS_MEDICOS = [
    {"nombre": "Rúben Amor", "especialidad": "Internista", "dias": "Lunes", "horario": "8:00 - 17:00", "tarifa": 150},
    {"nombre": "Ramón Esparza", "especialidad": "Cardiologo", "dias": "Lunes a Martes", "horario": "8:00 - 17:00", "tarifa": 200},
    {"nombre": "Lilia Torino", "especialidad": "Dentista (Exodoncia)", "dias": "Lunes a Viernes", "horario": "8:00 - 12:00", "tarifa": 150},
    {"nombre": "Patricia Soberón", "especialidad": "Dentista (Endodoncia)", "dias": "Martes", "horario": "15:00 - 16:00", "tarifa": 300},
    {"nombre": "Karla Montero", "especialidad": "Veterinaria", "dias": "Viernes a Sábado", "horario": "8:00 - 10:00", "tarifa": 100},
    {"nombre": "René Ambrosio", "especialidad": "Nutricionista", "dias": "Lunes y Miércoles", "horario": "10:00 - 11:00, 8:00 - 15:00, 15:00 - 17:00", "tarifa": 250},
    {"nombre": "Erasto López", "especialidad": "Nutricionista", "dias": "Lunes a Viernes", "horario": "8:00 - 12:00", "tarifa": 250},
    {"nombre": "Erasto Castañeda", "especialidad": "Psicologo", "dias": "Martes", "horario": "15:00 - 16:00", "tarifa": 500},
    {"nombre": "Carlos Meléndez", "especialidad": "Psiquiatra", "dias": "Viernes a Sábado", "horario": "8:00 - 10:00", "tarifa": 600}
]

def normalizar_texto(texto: str) -> str:
    texto_limpio = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto_limpio.lower()

# =====================================================================
# 2. LOGICA DEL BUSCADOR INTELIGENTE TOLERANTE A ERRORES (FUZZY SIMULATION)
# =====================================================================
def consultar_agenda_disponible(mensaje_paciente: str) -> tuple:
    msg = normalizar_texto(mensaje_paciente)
    coincidencias = []
    tipo = "general"

    # Diccionario de raíces y variaciones ortográficas comunes
    es_dental = any(x in msg for x in ["dent", "odont", "muel", "dient", "endo", "exod", "limpiez", "resina"])
    es_cardio = any(x in msg for x in ["card", "coraz", "presion", "tension"])
    es_interna = any(x in msg for x in ["intern", "gener", "medicin", "chequeo", "doctor"])
    es_vet = any(x in msg for x in ["vet", "perr", "gat", "mascot", "animal", "cachorr"])
    es_nutri = any(x in msg for x in ["nutr", "diet", "peso", "calori", "gord", "flac"])
    es_psico = any(x in msg for x in ["psico", "terap", "ansied", "depre", "psicolo"])
    es_psiquia = any(x in msg for x in ["psiquia", "esquiz", "medicam"])

    # Ruteo basado en proximidad de términos
    if es_dental:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "dentista" in normalizar_texto(m["especialidad"])]
        tipo = "Dentista / Endodoncia"
    elif es_cardio:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "cardiologo" in normalizar_texto(m["especialidad"])]
        tipo = "Cardiólogo"
    elif es_interna:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "internista" in normalizar_texto(m["especialidad"])]
        tipo = "Médico Internista"
    elif es_vet:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "veterinaria" in normalizar_texto(m["especialidad"])]
        tipo = "Veterinaria"
    elif es_nutri:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "nutricionista" in normalizar_texto(m["especialidad"])]
        tipo = "Nutricionista"
    elif es_psico:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "psicologo" in normalizar_texto(m["especialidad"])]
        tipo = "Psicólogo"
    elif es_psiquia:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "psiquiatra" in normalizar_texto(m["especialidad"])]
        tipo = "Psiquiatra"

    if not coincidencias:
        return "Por favor indícame la especialidad que buscas para darte los horarios de nuestros especialistas.", False

    resultado_texto = f" Con mucho gusto te comparto las opciones para la especialidad de {tipo}:\n"
    for med in coincidencias:
        resultado_texto += f"- {med['nombre']} ({med['especialidad']}): {med['dias']} en horario {med['horario']}. Tarifa: ${med['tarifa']}\n"
    
    return resultado_texto, True

# =====================================================================
# 3. ENDPOINT WEBHOOK
# =====================================================================
@app.post("/webhook/whatsapp")
async def procesar_mensaje_whatsapp(datos: MensajeEntrada):
    try:
        msg = normalizar_texto(datos.mensaje)
        
        if "infarto" in msg or "pecho" in msg or "sangrando" in msg or "urgencia" in msg or "accidente" in msg:
            respuesta_agente = (
                f"¡Hola {datos.nombre_paciente}! Detectamos síntomas de alerta crítica en tu mensaje. "
                "Por tu seguridad, te recomendamos acudir de inmediato a la sala de emergencias más cercana. "
                "Un asesor humano de la clínica se comunicará contigo de urgencia a este número."
            )
            return {"status": "success", "responder_a": datos.id_whatsapp, "mensaje_salida": respuesta_agente}
        
        horarios, encontrado = consultar_agenda_disponible(datos.mensaje)
        
        if encontrado:
            respuesta_agente = f"¡Hola {datos.nombre_paciente}!{horarios}\n¿Te interesa que reservemos alguno de estos espacios?"
        else:
            respuesta_agente = f"¡Hola {datos.nombre_paciente}! {horarios}"
            
        return {
            "status": "success",
            "responder_a": datos.id_whatsapp,
            "mensaje_salida": respuesta_agente
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
