import requests
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """
    Obtém as condições climáticas e temperatura atual para uma determinada cidade.
    """
    try:
        # Step 1: Geocode the city name to latitude/longitude
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=pt"
        response = requests.get(geo_url).json()
        
        if not response.get("results"):
            return f"Não foi possível encontrar a cidade '{city}'."
            
        result = response["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        name = result["name"]
        country = result.get("country", "")
        region = result.get("admin1", "")
        
        # Step 2: Get current weather using coordinates
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_resp = requests.get(weather_url).json()
        
        if "current_weather" not in weather_resp:
            return f"Não foi possível obter informações de clima para a cidade '{name}'."
            
        cw = weather_resp["current_weather"]
        temp = cw["temperature"]
        windspeed = cw["windspeed"]
        weathercode = cw["weathercode"]
        
        # Weather code descriptions (WMO weather interpretation codes)
        weather_desc = {
            0: "Céu limpo",
            1: "Principalmente limpo",
            2: "Parcialmente nublado",
            3: "Encoberto",
            45: "Nevoeiro",
            48: "Nevoeiro com depósito de geada",
            51: "Chuvisco leve",
            53: "Chuvisco moderado",
            55: "Chuvisco denso",
            61: "Chuva fraca",
            63: "Chuva moderada",
            65: "Chuva forte",
            71: "Neve fraca",
            73: "Neve moderada",
            75: "Neve forte",
            80: "Pancadas de chuva fracas",
            81: "Pancadas de chuva moderadas",
            82: "Pancadas de chuva violentas",
            95: "Trovoada leve ou moderada",
            96: "Trovoada com granizo leve",
            99: "Trovoada com granizo forte"
        }
        
        desc = weather_desc.get(weathercode, "Condições climáticas desconhecidas")
        
        location = f"{name}"
        if region:
            location += f", {region}"
        if country:
            location += f" ({country})"
            
        return f"Clima atual em {location}: {desc}, com temperatura de {temp}°C e ventos a {windspeed} km/h."
    except Exception as e:
        return f"Erro ao obter informações climáticas: {e}"
