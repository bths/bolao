from flask import Flask, jsonify, render_template
import requests
import pandas as pd
import io
import time
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

SHAREPOINT_URL = "https://onedrive.live.com/:x:/g/personal/8ad946cbf2f6dc55/IQCxFLQmY8LSQK17bwDqGB3iAUsrVXT0R6h_s9DyFfVWx5g?rtime=0G7d8TvL3kg&redeem=aHR0cHM6Ly8xZHJ2Lm1zL3gvYy84YWQ5NDZjYmYyZjZkYzU1L0lRQ3hGTFFtWThMU1FLMTdid0RxR0IzaUFVc3JWWFQwUjZoX3M5RHlGZlZXeDVnP2U9S1FCMTd1&download=1"
API_FUTEBOL_KEY = "9a10f987ae224619b823b476f326b376" # Dica: Cuidado ao expor sua chave na internet!

def baixar_planilha():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    url = f"{SHAREPOINT_URL}&nocache={int(time.time())}"
    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "html" in content_type:
        raise Exception("O link retornou HTML. O arquivo pode ser privado ou o link está incorreto.")

    return io.BytesIO(response.content)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ranking")
def ranking():
    try:
        arquivo = baixar_planilha()
        xls = pd.ExcelFile(arquivo, engine="openpyxl")
        aba_ranking = next((s for s in xls.sheet_names if "Ranking" in s), None)

        if not aba_ranking:
            return jsonify({"error": f"Aba de ranking não encontrada. Abas: {xls.sheet_names}"}), 404

        arquivo.seek(0)
        df = pd.read_excel(arquivo, sheet_name=aba_ranking, engine="openpyxl", header=1).dropna(how="all")
        df = df[df.iloc[:, 0].apply(lambda x: str(x).strip().isdigit())]

        participantes = []
        for _, row in df.iterrows():
            participantes.append({
                "posicao": int(row.iloc[0]),
                "nome": str(row.iloc[1]).strip(),
                "pontos": int(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                "premio": str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) and str(row.iloc[3]).strip() not in ["-", "nan", ""] else None
            })

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

        url = f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={hoje}&dateTo={futuro}"
        headers = {"X-Auth-Token": API_FUTEBOL_KEY}
        
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        dados = resp.json()
        partidas = dados.get('matches', [])

        status_traduzido = {
            'TIMED': 'Agendado', 'SCHEDULED': 'Agendado', 'IN_PLAY': 'Em andamento',
            'PAUSED': 'Intervalo', 'FINISHED': 'Encerrado', 'SUSPENDED': 'Suspenso',
            'POSTPONED': 'Adiado', 'CANCELLED': 'Cancelado'
        }

        paises_traduzidos = {
            'Brazil': 'Brasil', 'Argentina': 'Argentina', 'France': 'França',
            'Germany': 'Alemanha', 'Spain': 'Espanha', 'Portugal': 'Portugal',
            'England': 'Inglaterra', 'Netherlands': 'Holanda', 'Italy': 'Itália',
            'Uruguay': 'Uruguai', 'Croatia': 'Croácia', 'Belgium': 'Bélgica',
            'Switzerland': 'Suíça', 'USA': 'EUA', 'Mexico': 'México',
            'Senegal': 'Senegal', 'Japan': 'Japão', 'South Korea': 'Coreia',
            'Iran': 'Irã', 'New Zealand': 'N. Zelândia', 'Iraq': 'Iraque',
            'Norway': 'Noruega', 'Sweden': 'Suécia', 'Tunisia': 'Tunísia',
            'Cape Verde Islands': 'Cabo Verde', 'Egypt': 'Egito', 'Saudi Arabia': 'Arábia Saudita'
        }

        ultimo_jogo, jogo_atual, proximo_jogo = None, None, None

        partidas.sort(key=lambda x: x['utcDate'])

        for p in partidas:
            dt_utc = datetime.strptime(p['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(fuso_br)
            data_jogo = dt_local.strftime('%Y-%m-%d')

            if dt_local.timestamp() < inicio_do_dia:
                continue

            if data_jogo == hoje:
                texto_data = "Hoje"
            elif data_jogo == (agora + timedelta(days=1)).strftime('%Y-%m-%d'):
                texto_data = "Amanhã"
            else:
                texto_data = dt_local.strftime('%d/%m')

            texto_horario = f"{texto_data} às {dt_local.strftime('%H:%M')}"
            status = p['status']

            if dt_local > agora and status in ['FINISHED', 'IN_PLAY']:
                status = 'TIMED'

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
                "horario": texto_horario,
                "statusPT": status_traduzido.get(status, status),
                "statusOriginal": status,
                "placarCasa": placar_casa,
                "placarFora": placar_fora
            }

            if status == 'FINISHED':
                ultimo_jogo = obj_jogo
            elif status in ['IN_PLAY', 'PAUSED']:
                jogo_atual = obj_jogo
            elif status in ['TIMED', 'SCHEDULED'] and proximo_jogo is None:
                proximo_jogo = obj_jogo

        return jsonify({
            "ultimoJogo": ultimo_jogo,
            "jogoAtual": jogo_atual,
            "proximoJogo": proximo_jogo
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)