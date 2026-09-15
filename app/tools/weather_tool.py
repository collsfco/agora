import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Mapeo oficial WMO Weather interpretation codes (Open-Meteo)
WMO_CODE_MAP = {
    0: "Despejado",
    1: "Mayormente despejado",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Niebla",
    48: "Niebla con escarcha",
    51: "Llovizna ligera",
    53: "Llovizna moderada",
    55: "Llovizna densa",
    61: "Lluvia ligera",
    63: "Lluvia moderada",
    65: "Lluvia fuerte",
    71: "Nieve ligera",
    73: "Nieve moderada",
    75: "Nieve fuerte",
    80: "Chubascos ligeros",
    81: "Chubascos moderados",
    82: "Chubascos violentos",
    95: "Tormenta eléctrica",
    96: "Tormenta con granizo ligero",
    99: "Tormenta con granizo fuerte"
}

async def get_current_weather(city_or_region: str = "Santander") -> Dict[str, Any]:
    """
    Obtiene datos meteorológicos en tiempo real utilizando la API pública de Open-Meteo (sin API key requerida y 100% fiable).
    """
    clean_city = city_or_region.strip()
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # 1. Geocodificación directa de la localidad/región
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean_city}&count=1&language=es&format=json"
            geo_res = await client.get(geo_url)
            
            if geo_res.status_code != 200:
                return {"error": f"Error localizando '{city_or_region}' (código {geo_res.status_code})"}
            
            geo_data = geo_res.json()
            results = geo_data.get("results")
            if not results:
                return {"error": f"No se encontró la ubicación geográfica para '{city_or_region}'."}
            
            location_info = results[0]
            lat = location_info["latitude"]
            lon = location_info["longitude"]
            resolved_name = location_info.get("name", clean_city)
            admin_region = location_info.get("admin1", "")
            
            # 2. Consulta meteorológica precisa
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
                f"apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto"
            )
            w_res = await client.get(weather_url)
            if w_res.status_code != 200:
                return {"error": f"Error al obtener meteorología de Open-Meteo (código {w_res.status_code})"}
            
            w_data = w_res.json()
            current = w_data.get("current", {})
            
            temp_c = current.get("temperature_2m", "N/A")
            feels_like = current.get("apparent_temperature", "N/A")
            humidity = current.get("relative_humidity_2m", "N/A")
            wind_kmh = current.get("wind_speed_10m", "N/A")
            weather_code = current.get("weather_code", 0)
            condition = WMO_CODE_MAP.get(weather_code, "Condición variable")
            
            display_name = f"{resolved_name} ({admin_region})" if admin_region else resolved_name
            
            return {
                "location": display_name,
                "temperature": f"{temp_c}°C",
                "feels_like": f"{feels_like}°C",
                "condition": condition,
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind_kmh} km/h"
            }
            
    except Exception as e:
        logger.error(f"Error consultando el clima para {city_or_region}: {e}")
        return {"error": f"No se pudo obtener el clima para '{city_or_region}': {e}"}
