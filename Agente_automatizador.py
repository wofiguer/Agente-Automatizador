# -*- coding: utf-8 -*-
"""
Agente de Automatización para Consultorios Médicos (Core MVP)
Versión de Simulación Gratuita - Ejecutor In-Memory 100% Estable para Colab
"""

import unicodedata
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

# =====================================================================
# 1. CONFIGURACIÓN DEL ENGINE Y ESQUEMAS
# =====================================================================
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
# 2. LOGICA DEL BUSCADOR INTELIGENTE (EXCEL)
# =====================================================================
def consultar_agenda_disponible(mensaje_paciente: str) -> tuple:
    msg = normalizar_texto(mensaje_paciente)
    coincidencias = []
    tipo = "general"

    if "dentista" in msg or "odontologia" in msg or "muela" in msg or "diente" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "dentista" in normalizar_texto(m["especialidad"])]
        tipo = "Dentista"
    elif "cardio" in msg or "corazon" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "cardiologo" in normalizar_texto(m["especialidad"])]
        tipo = "Cardiólogo"
    elif "internista" in msg or "general" in msg or "medico" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "internista" in normalizar_texto(m["especialidad"])]
        tipo = "Médico Internista"
    elif "veterinaria" in msg or "perro" in msg or "gato" in msg or "mascota" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "veterinaria" in normalizar_texto(m["especialidad"])]
        tipo = "Veterinaria"
    elif "nutri" in msg or "dieta" in msg or "peso" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "nutricionista" in normalizar_texto(m["especialidad"])]
        tipo = "Nutricionista"
    elif "psicologo" in msg or "terapia" in msg or "psicologia" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "psicologo" in normalizar_texto(m["especialidad"])]
        tipo = "Psicólogo"
    elif "psiquiatra" in msg or "ansiedad" in msg:
        coincidencias = [m for m in BASE_DATOS_MEDICOS if "psiquiatra" in normalizar_texto(m["especialidad"])]
        tipo = "Psiquiatra"

    if not coincidencias:
        return "Por favor indícame la especialidad que buscas para darte los horarios de nuestros especialistas.", False

    resultado_texto = f" Con mucho gusto te comparto las opciones para la especialidad de {tipo}:\n"
    for med in coincidencias:
        resultado_texto += f"- {med['nombre']}: {med['dias']} en horario {med['horario']}. Tarifa: ${med['tarifa']}\n"
    
    return resultado_texto, True

# =====================================================================
# 3. ENDPOINT WEBHOOK
# =====================================================================
@app.post("/webhook/whatsapp")
async def procesar_mensaje_whatsapp(datos: MensajeEntrada):
    try:
        msg = normalizar_texto(datos.mensaje)
        
        # Validación prioritaria de Triage de Emergencias Médicas
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
    # Arranca el servidor local o de producción en el puerto por defecto
    uvicorn.run(app, host="0.0.0.0", port=8000)
