# estatisticas.py

def analisar_palpites_jogo(palpites):
    """Calcula o termômetro e a maior goleada ESPECÍFICA de uma partida."""
    if not palpites:
        return {"termometro": None, "destaque": None}

    vitoria_casa = 0
    empate = 0
    vitoria_fora = 0
    
    maior_dif = -1
    max_gols = -1
    destaque_nome = None
    destaque_placar = None

    for p in palpites:
        try:
            gols_casa, gols_fora = map(int, p['placar'].split(' x '))
            
            # 1. Conta para o Termômetro
            if gols_casa > gols_fora:
                vitoria_casa += 1
            elif gols_casa < gols_fora:
                vitoria_fora += 1
            else:
                empate += 1
                
            # 2. Caça a Maior Ousadia/Goleada do jogo
            dif = abs(gols_casa - gols_fora)
            total_gols = gols_casa + gols_fora
            
            if dif > maior_dif or (dif == maior_dif and total_gols > max_gols):
                maior_dif = dif
                max_gols = total_gols
                destaque_nome = p['nome']
                destaque_placar = p['placar']
                
        except Exception:
            pass

    total = len(palpites)
    termometro = None
    if total > 0:
        termometro = {
            "casa": int(round((vitoria_casa / total) * 100)),
            "empate": int(round((empate / total) * 100)),
            "fora": int(round((vitoria_fora / total) * 100))
        }
        
    destaque = None
    # Só dá o troféu se o participante apostou uma diferença de 2 gols ou mais (pra não premiar um 1x0 comum)
    if destaque_nome and maior_dif >= 2:
        destaque = {
            "nome": destaque_nome,
            "placar": destaque_placar
        }

    return {"termometro": termometro, "destaque": destaque}