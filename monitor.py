import requests
import json
from datetime import datetime, timedelta, timezone
from banco import db

def obter_geolocalizacao(ip):
    """
    Consulta a geolocalização do IP utilizando a API ipapi.co.
    """
    # 1. Filtro para ambiente de desenvolvimento local
    if ip == '127.0.0.1' or ip == '::1':
        return {
            "pais": "Local",
            "cidade": "Desenvolvimento",
            "estado": "WSL"
        }
    
    # 2. Consulta de geolocalização real para IP público
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        
        if response.status_code != 200:
            return {"pais": "N/A", "cidade": "N/A", "estado": "N/A"}
            
        data = response.json()
        
        if "error" in data:
            return {"pais": "Privado/Proxy", "cidade": "N/A", "estado": "N/A"}

        return {
            "pais": data.get("country_name", "Desconhecido"),
            "cidade": data.get("city", "Desconhecido"),
            "estado": data.get("region", "Desconhecido")
        }
    except Exception as e:
        print(f"Erro na geolocalização: {e}")
        return {"pais": "Erro", "cidade": "Erro", "estado": "Erro"}

def registrar_acesso(ip, evento):
    """
    Registra o evento no Redis com fuso horário de Brasília.
    """
    # Define fuso de Brasília (UTC-3)
    fuso_br = timezone(timedelta(hours=-3))
    
    # Geolocalização apenas na abertura
    geo = obter_geolocalizacao(ip) if evento == "abertura" else {"pais": "-", "cidade": "-", "estado": "-"}
    
    log_entry = {
        "ip": ip,
        "pais": geo["pais"],
        "cidade": geo["cidade"],
        "estado": geo["estado"],
        "evento": evento,
        # Timestamp forçado no fuso de Brasília
        "timestamp": datetime.now(fuso_br).strftime("%d/%m %H:%M:%S")
    }
    
    db.rpush("acessos_logs", json.dumps(log_entry))