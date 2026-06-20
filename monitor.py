import requests
import json
from datetime import datetime
from banco import db

def obter_geolocalizacao(ip):
    """
    Consulta a geolocalização do IP utilizando a API ipapi.co.
    Detecta se o acesso é local para evitar consultas desnecessárias.
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
        # Verifica se a API retornou erro (ex: limite de requisições)
        if response.status_code != 200:
            return {"pais": "N/A", "cidade": "N/A", "estado": "N/A"}
            
        data = response.json()
        
        # Se a API retornar erro no JSON (ex: 'error': true)
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
    Registra o evento no Redis (Upstash) com os dados geográficos.
    """
    # Só buscamos geolocalização na abertura para economizar requisições à API
    geo = obter_geolocalizacao(ip) if evento == "abertura" else {"pais": "-", "cidade": "-", "estado": "-"}
    
    log_entry = {
        "ip": ip,
        "pais": geo["pais"],
        "cidade": geo["cidade"],
        "estado": geo["estado"],
        "evento": evento,
        "timestamp": datetime.now().strftime("%d/%m %H:%M:%S")
    }
    
    # Adiciona o registro no final da lista no Redis
    db.rpush("acessos_logs", json.dumps(log_entry))