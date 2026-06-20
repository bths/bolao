import io
import requests
import pandas as pd
import json
from banco import db
from historico import processar_historico_grafico

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
    """Faz o trabalho pesado: extrai da planilha, calcula a linha do tempo e salva."""
    
    arquivo_xls = obter_planilha()
    xls = pd.ExcelFile(arquivo_xls, engine='openpyxl')
    
    # --- 1. COLETA OS PONTOS ATUAIS E OS PRÊMIOS DA PLANILHA ---
    nome_aba_ranking = next((s for s in xls.sheet_names if "ranking" in s.lower()), None)
    if not nome_aba_ranking:
        raise ValueError(f"Aba 'Ranking' não encontrada. Abas disponíveis: {xls.sheet_names}")
        
    df_ranking = pd.read_excel(xls, sheet_name=nome_aba_ranking, engine='openpyxl')
    pontos_da_planilha = []
    premios_por_posicao = {} # Novo dicionário para travar o prêmio na posição!
    
    for _, row in df_ranking.iterrows():
        try:
            pos_val = row.iloc[0]
            if pd.isna(pos_val): continue
            
            nome = str(row.iloc[1]).strip()
            if nome.lower() == "nan" or not nome: continue
            
            # Salva o prêmio amarrado ao número da posição (ex: 1: '360')
            pos_int = int(pos_val)
            premio_str = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            if premio_str and premio_str.lower() != 'nan':
                premios_por_posicao[pos_int] = premio_str
            
            p = {
                "nome": nome,
                "pontos": int(row.iloc[2])
            }
            pontos_da_planilha.append(p)
        except:
            continue
        
    # --- 2. COLETA OS JOGOS ENCERRADOS (Busca dinâmica da aba Resultados) ---
    ultimo_id_valido = 0
    jogos_encerrados_planilha = []
    contador_jogo = 1
    
    nome_aba_res = next((s for s in xls.sheet_names if "resultado" in s.lower()), None)
    
    if nome_aba_res:
        try:
            df_res = pd.read_excel(xls, sheet_name=nome_aba_res, engine='openpyxl', header=2)
            for _, row in df_res.iterrows():
                id_jogo = row.iloc[0]
                time_a = str(row.get('Time A', '')).strip()
                time_b = str(row.get('Time B', '')).strip()
                
                gols_a = row.get('Gols A', row.get('Chute A'))
                gols_b = row.get('Gols B', row.get('Chute B'))
                
                if pd.notna(id_jogo) and time_a and time_a.lower() != 'nan' and time_b and time_b.lower() != 'nan' and pd.notna(gols_a) and pd.notna(gols_b):
                    try:
                        g_a = int(float(gols_a))
                        g_b = int(float(gols_b))
                        
                        id_num = int(id_jogo)
                        if id_num > ultimo_id_valido:
                            ultimo_id_valido = id_num

                        label = f"J{contador_jogo} · {time_a} {g_a}x{g_b}"
                        jogos_encerrados_planilha.append(label)
                        contador_jogo += 1
                    except ValueError:
                        pass
        except Exception as e:
            print(f"⚠️ Aviso ao ler aba Resultados: {e}")

    # --- 3. GERA A LINHA DO TEMPO (GRÁFICO) ---
    dados_labels_str = db.get("grafico_labels") if db else None
    dados_pts_str = db.get("grafico_dados") if db else None
    
    db_labels_antigos = json.loads(dados_labels_str) if dados_labels_str else []
    db_dados_antigos = json.loads(dados_pts_str) if dados_pts_str else []

    novos_labels, novos_dados = processar_historico_grafico(
        jogos_encerrados_planilha, 
        pontos_da_planilha, 
        db_labels_antigos, 
        db_dados_antigos
    )

    if db:
        db.set("grafico_labels", json.dumps(novos_labels))
        db.set("grafico_dados", json.dumps(novos_dados))

    # --- 4. O NOVO MOTOR MATEMÁTICO DE RANKING (Blindado contra falhas) ---
    def obter_pto_antigo(j):
        pts = j.get('pts')
        if not pts: pts = [] # Proteção contra dados corrompidos
        return pts[-2] if len(pts) >= 2 else (pts[0] if len(pts) == 1 else 0)

    def obter_pto_novo(j):
        pts = j.get('pts')
        if not pts: pts = []
        return pts[-1] if len(pts) >= 1 else 0

    ranking_ontem = sorted(novos_dados, key=lambda x: (-obter_pto_antigo(x), x['nome']))
    posicoes_ontem = {jogador['nome']: idx + 1 for idx, jogador in enumerate(ranking_ontem)}

    ranking_hoje = sorted(novos_dados, key=lambda x: (-obter_pto_novo(x), x['nome']))
    
    participantes_atual = []
    pontos_do_cara_de_cima = None

    for i, jogador in enumerate(ranking_hoje):
        nome = jogador['nome']
        pontos_agora = obter_pto_novo(jogador)
        
        posicao_agora = i + 1
        posicao_antes = posicoes_ontem.get(nome, posicao_agora)

        diferenca = 0 if pontos_do_cara_de_cima is None else (pontos_do_cara_de_cima - pontos_agora)
        pontos_do_cara_de_cima = pontos_agora

        if posicao_agora < posicao_antes:
            icone, num = '⬆️', f"+{posicao_antes - posicao_agora}"
        elif posicao_agora > posicao_antes:
            icone, num = '⬇️', f"-{posicao_agora - posicao_antes}"
        else:
            icone, num = '➖', ''
            
        participantes_atual.append({
            "posicao": posicao_agora,
            "nome": nome,
            "pontos": pontos_agora,
            "premio": premios_por_posicao.get(posicao_agora, ""),
            "diferenca_para_proximo": diferenca,
            "variacao_icone": icone,
            "variacao_num": num
        })

    # --- 5. CARGA TOTAL DE PALPITES NO BANCO (Busca dinâmica de participantes) ---
    try:
        # Filtra automaticamente qualquer aba que seja do sistema, deixando só os nomes
        abas_ignoradas = ['ranking', 'resultado', 'palpite', 'gabarito']
        abas_participantes = [aba for aba in xls.sheet_names if not any(ign in aba.lower() for ign in abas_ignoradas)]
        
        todos_palpites = {}
        
        for aba in abas_participantes:
            try:
                df_part = pd.read_excel(xls, sheet_name=aba, engine="openpyxl", header=2)
                for _, row_p in df_part.iterrows():
                    ta = str(row_p.get('Time A', '')).strip()
                    tb = str(row_p.get('Time B', '')).strip()
                    ca = row_p.get('Chute A')
                    cb = row_p.get('Chute B')
                    
                    if ta and ta.lower() != 'nan' and tb and tb.lower() != 'nan' and pd.notna(ca) and pd.notna(cb):
                        ta_limpo = ta.split(' ', 1)[-1].strip().lower() if ' ' in ta else ta.strip().lower()
                        tb_limpo = tb.split(' ', 1)[-1].strip().lower() if ' ' in tb else tb.strip().lower()
                        chave_jogo = f"{ta_limpo}_x_{tb_limpo}"
                        
                        if chave_jogo not in todos_palpites:
                            todos_palpites[chave_jogo] = []
                            
                        try:
                            g_a, g_b = int(float(ca)), int(float(cb))
                            todos_palpites[chave_jogo].append({
                                "nome": aba,
                                "placar": f"{g_a} x {g_b}"
                            })
                        except:
                            pass
            except Exception as e:
                pass
                
        if db:
            db.set("todos_os_palpites", json.dumps(todos_palpites))
            
    except Exception as e:
        print(f"⚠️ Aviso: Falha na carga total de palpites. Erro: {e}")

    # --- 6. SALVA O RANKING E O SNAPSHOT FINAL NO BANCO ---
    if db:
        db.set("ranking_completo", json.dumps(participantes_atual))
        if ultimo_id_valido > 0:
            db.set(f"ranking_jogo:{ultimo_id_valido}", json.dumps(participantes_atual))
            
        try:
            db.delete("memoria_posicoes")
        except:
            pass
        
    return participantes_atual