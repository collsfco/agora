import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def get_current_weather(city_or_region: str = "Santander") -> Dict[str, Any]:
    """Obtiene datos meteorológicos precisos y directos (temperatura exacta, estado del cielo, viento y humedad)."""
    clean_city = city_or_region.strip().replace(" ", "+")
    url = f"https://wttr.in/{clean_city}?format=j1"
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                return {"error": f"El servicio meteorológico respondió con código {res.status_code}"}
            
            data = res.json()
            curr = data.get("current_condition", [{}])[0]
            temp_c = curr.get("temp_C", "N/A")
            feels_like = curr.get("FeelsLikeC", "N/A")
            desc_en = curr.get("weatherDesc", [{}])[0].get("value", "")
            humidity = curr.get("humidity", "N/A")
            wind_kmh = curr.get("windspeedKmph", "N/A")
            
            # Traducción rápida de estados habituales
            desc_map = {
                "Clear": "Despejado",
                "Sunny": "Soleado",
                "Partly cloudy": "Parcialmente nublado",
                "Cloudy": "Nublado",
                "Overcast": "Cubierto",
                "Light rain": "Lluvia ligera",
                "Moderate rain": "Lluvia moderada",
                "Heavy rain": "Lluvia intensa",
                "Patchy rain possible": "Posibilidad de lluvias dispersas",
                "Mist": "Neblina",
                "Fog": "Niebla"
            }
            desc_es = desc_map.get(desc_en.strip(), desc_en)
            
            return {
                "location": city_or_region,
                "temperature": f"{temp_c}°C",
                "feels_like": f"{feels_like}°C",
                "condition": desc_es,
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind_kmh} km/h"
            }
    except Exception as e:
        logger.error(f"Error consultando el clima para {city_or_region}: {e}")
        return {"error": f"No se pudo obtener el clima para '{city_or_region}': {e}"}
