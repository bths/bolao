import io
import requests
import pandas as pd
import json
from banco import db
from historico import processar_historico_grafico # <-- Puxando a nossa nova inteligência do gráfico

# O novo link de compartilhamento ativo atualizado!
URL_ONEDRIVE = "https://1drv.ms/x/c/8ad946cbf2f6dc55/IQAdm9N8Bx_mQKjtj5t-ijfGAQeXAj05aTkDqyzDlFkZd3k?e=Pyt8Es"

def obter_ranking_publico():
    """Apenas lê o ranking mastigado do banco de dados (0 ms de processamento)."""
    if db:
        try:
            dados = db.get("ranking_completo")
            if dados:
                return json.loads(dados) if isinstance(dados, str) else dados
        except Exception as e:
            print(f"Erro ao ler ranking_completo: {e}")
    return []

def carregar_memoria_posicoes():
    """Busca a memória de posições da rodada anterior para calcular as setinhas."""
    if db:
        try:
            dados = db.get("memoria_posicoes")
            if dados:
                return json.loads(dados) if isinstance(dados, str) else dados
        except Exception as e:
            print(f"Erro ao carregar memória: {e}")
    return {}

def obter_planilha():
    """Faz o download simulando um navegador real para evitar erro 403."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://onedrive.live.com/"
    }
    
    url_base = URL_ONEDRIVE.split("?")[0]
    url_direta = f"{url_base}?download=1"
    
    session = requests.Session()
    resposta = session.get(url_direta, headers=headers, timeout=20)
    resposta.raise_for_status()
    return io.BytesIO(resposta.content)

def processar_e_sincronizar_ranking():
    """Faz o trabalho pesado: baixa Excel, roda Pandas e salva no banco."""
    memoria_anterior = carregar_memoria_posicoes()
    
    arquivo_xls = obter_planilha()
    xls = pd.ExcelFile(arquivo_xls, engine='openpyxl')
    
    nome_aba = next((s for s in xls.sheet_names if "ranking" in s.lower()), None)
    if not nome_aba:
        raise ValueError(f"Aba 'Ranking' não encontrada. Abas disponíveis: {xls.sheet_names}")
        
    df = pd.read_excel(xls, sheet_name=nome_aba, engine='openpyxl')
    participantes_atual = []
    
    # --- 1. PROCESSA O RANKING ---
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

    # --- 2. PROCESSA O HISTÓRICO DO GRÁFICO ---
    try:
        # Lê a aba Resultados. Se der erro de coluna não encontrada, verifique se o header=2 está certo
        df_res = pd.read_excel(xls, sheet_name='Resultados', engine='openpyxl', header=2)
        
        jogos_encerrados_planilha = []
        contador_jogo = 1
        
        for _, row in df_res.iterrows():
            # Tenta pegar as colunas de acordo com o padrão que você usa
            time_a = str(row.get('Time A', '')).strip()
            gols_a = row.get('Chute A')
            gols_b = row.get('Chute B')
            
            # Se os placares estiverem preenchidos, o jogo acabou!
            if time_a and time_a.lower() != 'nan' and pd.notna(gols_a) and pd.notna(gols_b):
                try:
                    g_a = int(float(gols_a))
                    g_b = int(float(gols_b))
                    # Monta o título exato: "J20 · Brasil 2x0"
                    label = f"J{contador_jogo} · {time_a} {g_a}x{g_b}"
                    jogos_encerrados_planilha.append(label)
                    contador_jogo += 1
                except ValueError:
                    pass # Se tiver um "X" ou texto no placar, ignora

        # Puxa os dados antigos do banco para comparar
        dados_labels_str = db.get("grafico_labels")
        dados_pts_str = db.get("grafico_dados")
        
        db_labels_antigos = json.loads(dados_labels_str) if dados_labels_str else []
        db_dados_antigos = json.loads(dados_pts_str) if dados_pts_str else []

        # Passa pelo nosso cérebro do historico.py
        novos_labels, novos_dados = processar_historico_grafico(
            jogos_encerrados_planilha, 
            participantes_atual, 
            db_labels_antigos, 
            db_dados_antigos
        )

        # Salva o gráfico atualizado na nuvem!
        if db:
            db.set("grafico_labels", json.dumps(novos_labels))
            db.set("grafico_dados", json.dumps(novos_dados))
            
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível sincronizar o gráfico. Erro: {e}")

    # --- 3. SALVA O RANKING NO BANCO ---
    if db:
        db.set("memoria_posicoes", json.dumps({p['nome']: p['posicao'] for p in participantes_atual}))
        db.set("ranking_completo", json.dumps(participantes_atual))
        
    return participantes_atual