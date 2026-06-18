import io
import requests
import pandas as pd
import json
import os

# O link de compartilhamento original (certifique-se de que é o link de "Compartilhar")
URL_ONEDRIVE = "https://1drv.ms/x/c/8ad946cbf2f6dc55/IQCxFLQmY8LSQK17bwDqGB3iAUsrVXT0R6h_s9DyFfVWx5g?download=1"
CACHE_FILE = "ranking_cache.json"

def carregar_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def obter_planilha():
    """Faz o download simulando um navegador real para evitar erro 403."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://onedrive.live.com/"
    }
    
    # Força a URL a pedir o download direto
    url_base = URL_ONEDRIVE.split("?")[0]
    url_direta = f"{url_base}?download=1"
    
    session = requests.Session()
    resposta = session.get(url_direta, headers=headers, timeout=20)
    resposta.raise_for_status()
    
    return io.BytesIO(resposta.content)

def processar_ranking():
    memoria_anterior = carregar_cache()
    arquivo_xls = obter_planilha()
    xls = pd.ExcelFile(arquivo_xls, engine='openpyxl')
    
    # Busca a aba ignorando maiúsculas/minúsculas e espaços
    #nome_aba = next((s for s in xls.sheet_names if s.strip().lower() == "ranking"), None)
    # Procura a aba procurando por "ranking" em qualquer parte do nome
    nome_aba = next((s for s in xls.sheet_names if "ranking" in s.lower()), None)
    
    if not nome_aba:
        raise ValueError(f"Aba 'Ranking' não encontrada. Abas disponíveis: {xls.sheet_names}")
        
    df = pd.read_excel(xls, sheet_name=nome_aba, engine='openpyxl')
    participantes_atual = []
    
    for _, row in df.iterrows():
        try:
            pos_val = row.iloc[0]
            if pd.isna(pos_val): continue
            
            nome = str(row.iloc[1]).strip()
            if nome.lower() == "nan" or not nome: continue
            
            p = {
                "posicao": int(pos_val),
                "nome": nome,
                "pontos": int(row.iloc[2]),
                "premio": str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            }
            
            # Lógica das setinhas (usando o cache persistente)
            pos_antiga = memoria_anterior.get(p['nome'], p['posicao'])
            
            if not memoria_anterior:
                p['variacao_icone'], p['variacao_num'] = '➖', ''
            elif p['posicao'] < pos_antiga:
                p['variacao_icone'], p['variacao_num'] = '⬆️', f"+{pos_antiga - p['posicao']}"
            elif p['posicao'] > pos_antiga:
                p['variacao_icone'], p['variacao_num'] = '⬇️', f"-{p['posicao'] - pos_antiga}"
            else:
                p['variacao_icone'], p['variacao_num'] = '➖', ''

            participantes_atual.append(p)
        except:
            continue

    # Atualiza o cache no disco
    salvar_cache({p['nome']: p['posicao'] for p in participantes_atual})
    return participantes_atual