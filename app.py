import requests
import pandas as pd
import urllib.parse
import json

from flask import Flask, jsonify, render_template, request
from datetime import datetime, timedelta, timezone


# Importando os nossos módulos especialistas!
from ranking import obter_planilha, obter_ranking_publico, processar_e_sincronizar_ranking
from estatisticas import analisar_palpites_jogo
from dicionarios import paises_traduzidos, status_traduzido
from regras_bolao import gerar_previa_whatsapp
from monitor import registrar_acesso

# Importação nova: para ler os dados do gráfico direto do banco
from banco import ler_do_banco 

app = Flask(__name__)

API_FUTEBOL_KEY = "9a10f987ae224619b823b476f326b376"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/ranking")
def ranking_route():
    try:
        # ROTA PÚBLICA: Agora consome os dados mastigados do Redis na nuvem
        participantes = obter_ranking_publico()
        return jsonify({"participantes": participantes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- NOVA ROTA: A PONTE DO GRÁFICO (Corrigida e no lugar certo) ---
@app.route("/api/grafico")
def api_grafico():
    try:
        # Lê os dados brutos (Strings) do banco
        labels_raw = ler_do_banco("grafico_labels")
        dados_raw = ler_do_banco("grafico_dados")
        
        # Converte de String de volta para Listas/Dicionários do Python
        labels = json.loads(labels_raw) if isinstance(labels_raw, str) else (labels_raw or [])
        dados = json.loads(dados_raw) if isinstance(dados_raw, str) else (dados_raw or [])
        
        return jsonify({"labels": labels, "dados": dados})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# --------------------------------------

@app.route("/admin/sincronizar")
def sincronizar_route():
    try:
        # ROTA ADMINISTRATIVA: Baixa o Excel, calcula e atualiza a nuvem do Upstash
        participantes = processar_e_sincronizar_ranking()
        return jsonify({
            "status": "sucesso",
            "mensagem": "Planilha processada e banco de dados atualizado com sucesso!",
            "total_participantes": len(participantes)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ROTA DO PAINEL DE MONITORAMENTO
@app.route("/painel")
def painel():
    return render_template("painel.html")

@app.route("/api/log", methods=["POST", "OPTIONS"])
def log_acesso():
    # Isso resolve o 415 garantindo que pegamos o JSON mesmo se o header oscilar
    data = request.get_json(force=True) 
    ip = request.remote_addr
    registrar_acesso(ip, data.get("evento"))
    return jsonify({"status": "sucesso"})

@app.route("/api/logs_lista")
def logs_lista():
    # Busca os logs salvos no Redis
    from banco import db
    logs = [json.loads(l) for l in db.lrange("acessos_logs", 0, -1)]
    return jsonify(logs)


@app.route("/jogos")
def jogos():
    try:
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br)
        # Ampliando a busca: de ontem até 3 dias no futuro
        ontem = (agora - timedelta(days=1)).strftime('%Y-%m-%d')
        futuro = (agora + timedelta(days=3)).strftime('%Y-%m-%d')

        url = f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={ontem}&dateTo={futuro}"
        headers = {"X-Auth-Token": API_FUTEBOL_KEY}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        partidas = resp.json().get('matches', [])

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

        ultimo_jogo, jogo_atual, proximo_jogo = None, None, None
        partidas.sort(key=lambda x: x['utcDate'])

        def buscar_palpites_jogo(time_a, time_b):
            palpites = []
            ta_limpo = str(time_a).split(' ', 1)[-1].strip().lower() if ' ' in str(time_a) else str(time_a).strip().lower()
            tb_limpo = str(time_b).split(' ', 1)[-1].strip().lower() if ' ' in str(time_b) else str(time_b).strip().lower()

            for nome_participante, df_participante in dfs_participantes.items():
                if 'Time A' not in df_participante.columns or 'Time B' not in df_participante.columns:
                    continue
                df_ta = df_participante['Time A'].str.lower()
                df_tb = df_participante['Time B'].str.lower()
                linha_normal = df_participante[(df_ta == ta_limpo) & (df_tb == tb_limpo)]
                linha_invertida = df_participante[(df_ta == tb_limpo) & (df_tb == ta_limpo)]
                ca, cb = None, None
                
                # Voltou para a forma original e correta
                if not linha_normal.empty:
                    ca = linha_normal.iloc[0].get('Chute A')
                    cb = linha_normal.iloc[0].get('Chute B')
                elif not linha_invertida.empty:
                    ca = linha_invertida.iloc[0].get('Chute B')
                    cb = linha_invertida.iloc[0].get('Chute A')
                
                if pd.notna(ca) and pd.notna(cb):
                    try:
                        gols_a, gols_b = int(float(ca)), int(float(cb))
                        palpites.append({"nome": nome_participante, "placar": f"{gols_a} x {gols_b}"})
                    except: pass 
            return palpites

        for p in partidas:
            dt_utc = datetime.strptime(p['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(fuso_br)
            data_jogo = dt_local.strftime('%d/%m')

            status = p['status']
            
            nome_casa_api = p.get('homeTeam', {}).get('name', 'A definir')
            nome_fora_api = p.get('awayTeam', {}).get('name', 'A definir')
            
            casa = paises_traduzidos.get(nome_casa_api.lower().strip(), nome_casa_api)
            fora = paises_traduzidos.get(nome_fora_api.lower().strip(), nome_fora_api)

            palpites_processados = buscar_palpites_jogo(casa, fora)
            analise = analisar_palpites_jogo(palpites_processados)
            
            score = p.get('score', {})
            full_time = score.get('fullTime', {}) if isinstance(score, dict) else {}
            
            placar_casa = full_time.get('home') if isinstance(full_time, dict) else None
            placar_fora = full_time.get('away') if isinstance(full_time, dict) else None
            
            if placar_casa is None: placar_casa = '-'
            if placar_fora is None: placar_fora = '-'

            link_whatsapp = ""
            if status in ['IN_PLAY', 'PAUSED', 'FINISHED']:
                texto_previa = gerar_previa_whatsapp(casa, fora, placar_casa, placar_fora, palpites_processados)
                if texto_previa:
                    aviso = "\n\n⚠️ AVISO: O portal pode ter atraso em relação ao jogo real. Se o placar não atualizou, aguarde um instante."
                    mensagem = f"{texto_previa}\n\n🕒 Consulta: {datetime.now(fuso_br).strftime('%d/%m às %H:%M')}{aviso}"
                    link_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(mensagem)}"

            obj_jogo = {
                "timeCasa": casa, "timeFora": fora,
                "horario": f"{data_jogo} às {dt_local.strftime('%H:%M')}",
                "statusPT": status_traduzido.get(status, status),
                "placarCasa": placar_casa, "placarFora": placar_fora,
                "palpites": palpites_processados,
                "termometro": analise["termometro"], "destaque": analise["destaque"],
                "linkWhatsapp": link_whatsapp
            }

            if status == 'FINISHED': ultimo_jogo = obj_jogo
            elif status in ['IN_PLAY', 'PAUSED']: jogo_atual = obj_jogo
            elif status in ['TIMED', 'SCHEDULED'] and proximo_jogo is None: proximo_jogo = obj_jogo

        return jsonify({"ultimoJogo": ultimo_jogo, "jogoAtual": jogo_atual, "proximoJogo": proximo_jogo})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)