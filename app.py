from flask import Flask, jsonify, render_template
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

# Importa as ferramentas que criamos no novo arquivo ranking.py
from ranking import obter_planilha, processar_ranking

app = Flask(__name__)

API_FUTEBOL_KEY = "9a10f987ae224619b823b476f326b376"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ranking")
def ranking_route():
    try:
        # Usa a função do ranking.py
        participantes = processar_ranking()
        return jsonify({"participantes": participantes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/jogos")
def jogos():
    try:
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br)
        hoje = agora.strftime('%Y-%m-%d')
        futuro = (agora + timedelta(days=2)).strftime('%Y-%m-%d')
        inicio_do_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

        # 1. BUSCA OS JOGOS NA API
        url = f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={hoje}&dateTo={futuro}"
        headers = {"X-Auth-Token": API_FUTEBOL_KEY}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        partidas = resp.json().get('matches', [])

        # 2. CARREGA AS ABAS DE PALPITES DA PLANILHA (Reaproveitando a função do ranking.py)
        arquivo_xls = obter_planilha()
        xls = pd.ExcelFile(arquivo_xls, engine="openpyxl")
        abas_ignoradas = ['Ranking', 'Resultados', 'Palpites Especiais', 'Gabarito']
        abas_participantes = [aba for aba in xls.sheet_names if aba not in abas_ignoradas]

        dfs_participantes = {}
        for aba in abas_participantes:
            try:
                df = pd.read_excel(xls, sheet_name=aba, engine="openpyxl", header=2)
                df['Time A'] = df.get('Time A', '').astype(str).str.strip()
                df['Time B'] = df.get('Time B', '').astype(str).str.strip()
                dfs_participantes[aba] = df
            except:
                continue

        # 3. TRADUÇÃO DE NOMES ATUALIZADA
        status_traduzido = {
            'TIMED': 'Agendado', 'SCHEDULED': 'Agendado', 'IN_PLAY': 'Em andamento',
            'PAUSED': 'Intervalo', 'FINISHED': 'Encerrado'
        }

        # Dicionário expandido para garantir que todos os países sejam encontrados
        paises_traduzidos = {
            'Brazil': 'Brasil', 'France': 'França', 'Germany': 'Alemanha', 
            'Spain': 'Espanha', 'Netherlands': 'Holanda', 'Italy': 'Itália',
            'Croatia': 'Croácia', 'Belgium': 'Bélgica', 'Switzerland': 'Suíça', 
            'USA': 'Estados Unidos', 'Mexico': 'México', 'Japan': 'Japão', 
            'South Korea': 'Coreia do Sul', 'New Zealand': 'Nova Zelândia', 
            'Norway': 'Noruega', 'Sweden': 'Suécia', 'Tunisia': 'Tunísia',
            'Cape Verde Islands': 'Cabo Verde', 'Egypt': 'Egito', 
            'Saudi Arabia': 'Arábia Saudita', 'Ivory Coast': 'Costa do Marfim',
            'Czech Republic': 'República Tcheca', 'Iraq': 'Iraque', 'Senegal': 'Senegal',
            'Argentina': 'Argentina', 'Uruguay': 'Uruguai', 'Portugal': 'Portugal',
            'England': 'Inglaterra', 'Iran': 'Irã',
            'Algeria': 'Argélia', 'Austria': 'Áustria', 'Jordan': 'Jordânia',
            'Ghana': 'Gana', 'Panama': 'Panamá', 'Colombia': 'Colômbia',
            'South Africa': 'África do Sul', 'Bosnia and Herzegovina': 'Bósnia e Herzegovina',
            'Canada': 'Canadá', 'Qatar': 'Catar', 'Morocco': 'Marrocos', 'Scotland': 'Escócia',
            'Uzbekistan': 'Uzbequistão', 'DR Congo': 'Rep. Dem. do Congo', 'Congo DR': 'Rep. Dem. do Congo'
        }

        ultimo_jogo, jogo_atual, proximo_jogo = None, None, None
        partidas.sort(key=lambda x: x['utcDate'])

        # 4. NOVA FUNÇÃO DE BUSCA INTELIGENTE (Ignora ordem e letras maiúsculas/minúsculas)
        def buscar_palpites_jogo(time_a, time_b):
            palpites = []
            
            # Converte os nomes para letras minúsculas para ignorar erros de digitação
            ta = str(time_a).strip().lower()
            tb = str(time_b).strip().lower()

            for nome_participante, df_participante in dfs_participantes.items():
                if 'Time A' not in df_participante.columns or 'Time B' not in df_participante.columns:
                    continue
                    
                df_ta = df_participante['Time A'].str.lower()
                df_tb = df_participante['Time B'].str.lower()

                # Tenta achar na ordem normal (A x B)
                linha_normal = df_participante[(df_ta == ta) & (df_tb == tb)]
                # Tenta achar na ordem invertida (B x A)
                linha_invertida = df_participante[(df_ta == tb) & (df_tb == ta)]

                ca, cb = None, None
                
                if not linha_normal.empty:
                    ca = linha_normal.iloc[0].get('Chute A')
                    cb = linha_normal.iloc[0].get('Chute B')
                elif not linha_invertida.empty:
                    # Inverte os chutes, pois os times estão invertidos na planilha!
                    ca = linha_invertida.iloc[0].get('Chute B')
                    cb = linha_invertida.iloc[0].get('Chute A')

                # Verifica se é um número válido (ignora espaços em branco ou '-')
                if pd.notna(ca) and pd.notna(cb):
                    try:
                        gols_a = int(float(ca))
                        gols_b = int(float(cb))
                        palpites.append({"nome": nome_participante, "placar": f"{gols_a} x {gols_b}"})
                    except ValueError:
                        pass 
            
            return palpites

        for p in partidas:
            dt_utc = datetime.strptime(p['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(fuso_br)
            data_jogo = dt_local.strftime('%Y-%m-%d')

            if dt_local.timestamp() < inicio_do_dia: continue

            if data_jogo == hoje: texto_data = "Hoje"
            elif data_jogo == (agora + timedelta(days=1)).strftime('%Y-%m-%d'): texto_data = "Amanhã"
            else: texto_data = dt_local.strftime('%d/%m')

            status = p['status']
            if dt_local > agora and status in ['FINISHED', 'IN_PLAY']: status = 'TIMED'

            casa = paises_traduzidos.get(p.get('homeTeam', {}).get('name', 'A definir'), p.get('homeTeam', {}).get('name', 'A definir'))
            fora = paises_traduzidos.get(p.get('awayTeam', {}).get('name', 'A definir'), p.get('awayTeam', {}).get('name', 'A definir'))
            placar_casa = p.get('score', {}).get('fullTime', {}).get('home')
            placar_fora = p.get('score', {}).get('fullTime', {}).get('away')

            if status in ['TIMED', 'SCHEDULED'] or placar_casa is None:
                placar_casa = '-'
                placar_fora = '-'

            obj_jogo = {
                "timeCasa": casa,
                "timeFora": fora,
                "horario": f"{texto_data} às {dt_local.strftime('%H:%M')}",
                "statusPT": status_traduzido.get(status, status),
                "statusOriginal": status,
                "placarCasa": placar_casa,
                "placarFora": placar_fora,
                "palpites": buscar_palpites_jogo(casa, fora)
            }

            if status == 'FINISHED': ultimo_jogo = obj_jogo
            elif status in ['IN_PLAY', 'PAUSED']: jogo_atual = obj_jogo
            elif status in ['TIMED', 'SCHEDULED'] and proximo_jogo is None: proximo_jogo = obj_jogo

        return jsonify({"ultimoJogo": ultimo_jogo, "jogoAtual": jogo_atual, "proximoJogo": proximo_jogo})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)