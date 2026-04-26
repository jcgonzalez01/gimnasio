"""
Redirección al nuevo paquete estructurado de Hikvision.
Mantiene compatibilidad con importaciones existentes.
"""
from .hikvision import HikvisionISAPI, parse_event_payload, get_event_description
from .hikvision.client import HikvisionClient

# Si hay funciones auxiliares que no están en el paquete, se pueden dejar aquí.
import base64

def image_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")
