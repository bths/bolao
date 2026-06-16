import requests
import pandas as pd
import io
import time

SHAREPOINT_URL = "https://onedrive.live.com/:x:/g/personal/8ad946cbf2f6dc55/IQCxFLQmY8LSQK17bwDqGB3iAUsrVXT0R6h_s9DyFfVWx5g?rtime=0G7d8TvL3kg&redeem=aHR0cHM6Ly8xZHJ2Lm1zL3gvYy84YWQ5NDZjYmYyZjZkYzU1L0lRQ3hGTFFtWThMU1FLMTdid0RxR0IzaUFVc3JWWFQwUjZoX3M5RHlGZlZXeDVnP2U9S1FCMTd1&download=1"

# Sistema de Cache
cache_planilha = {"tempo": 0, "dados": None}

def obter_planilha():
    agora = time.time()
    # Se baixou a planilha há menos de 30 segundos, reaproveita!
    if cache_planilha["dados"] and (agora - cache_planilha["tempo"] < 30):
        return io.BytesIO(cache_planilha["dados"])
    
    # O DISFARCE COMPLETO VOLTOU AQUI!
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    url = f"{SHAREPOINT_URL}&nocache={int(agora)}"
    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    
    cache_planilha["dados"] = response.content
    cache_planilha["tempo"] = agora
    return io.BytesIO(cache_planilha["dados"])

def processar_ranking():
    arquivo = obter_planilha()
    xls = pd.ExcelFile(arquivo, engine="openpyxl")
    aba_ranking = next((s for s in xls.sheet_names if "Ranking" in s), None)

    if not aba_ranking:
        raise Exception("Aba de ranking não encontrada.")

    df = pd.read_excel(xls, sheet_name=aba_ranking, engine="openpyxl", header=1).dropna(how="all")
    df = df[df.iloc[:, 0].apply(lambda x: str(x).strip().isdigit())]

    participantes = []
    for _, row in df.iterrows():
        participantes.append({
            "posicao": int(row.iloc[0]),
            "nome": str(row.iloc[1]).strip(),
            "pontos": int(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
            "premio": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) and str(row.iloc[3]).strip() not in ["-", "nan", ""] else None
        })

    return participantes