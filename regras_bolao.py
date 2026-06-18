# regras_bolao.py
import random
from dicionarios import frases_0x0, frases_goleada, frases_comuns

def calcular_pontos_palpite(oficial_a, oficial_b, palpite_a, palpite_b):
    """Calcula os pontos ganhos em um palpite específico."""
    try:
        oa, ob = int(oficial_a), int(oficial_b)
        pa, pb = int(palpite_a), int(palpite_b)
    except (ValueError, TypeError):
        return 0
        
    acertou_a = (oa == pa)
    acertou_b = (ob == pb)
    
    # Determina quem venceu ou se foi empate
    vencedor_oficial = "A" if oa > ob else "B" if oa < ob else "E"
    vencedor_palpite = "A" if pa > pb else "B" if pa < pb else "E"
    acertou_vencedor = (vencedor_oficial == vencedor_palpite)
    
    # Regras do Bolão
    if acertou_a and acertou_b:
        return 25 # Cravação exata
    elif acertou_vencedor and (acertou_a or acertou_b):
        return 15 # Acertou vencedor/empate + gols de 1 time
    elif acertou_vencedor:
        return 10 # Acertou só quem ganhou ou o empate
    elif acertou_a or acertou_b:
        return 3  # Errou o vencedor, mas acertou os gols de um time
    else:
        return 0  # Errou tudo

def gerar_previa_whatsapp(time_a, time_b, placar_a, placar_b, palpites):
    """Gera o texto formatado para compartilhamento no grupo."""
    if placar_a == '-' or placar_b == '-':
        return ""
        
    cravadas = []
    na_trave = []
    resultado = []
    consolacao = []
    
    # Varre todos os palpites e distribui a galera nas categorias
    for p in palpites:
        try:
            pa, pb = map(int, p['placar'].split(' x '))
            pontos = calcular_pontos_palpite(placar_a, placar_b, pa, pb)
            
            if pontos == 25:
                cravadas.append(p['nome'].split()[0]) # Pega só o primeiro nome pra não ficar gigante
            elif pontos == 15:
                na_trave.append(p['nome'].split()[0])
            elif pontos == 10:
                resultado.append(p['nome'].split()[0])
            elif pontos == 3:
                consolacao.append(p['nome'].split()[0])
        except Exception:
            continue
            
    # Sorteio da frase com base no contexto do placar
    try:
        oa, ob = int(placar_a), int(placar_b)
        diff = abs(oa - ob)
        if oa == 0 and ob == 0:
            frase = random.choice(frases_0x0)
        elif diff >= 3:
            frase = random.choice(frases_goleada)
        else:
            frase = random.choice(frases_comuns)
    except:
        frase = random.choice(frases_comuns)
        
    # Montagem do texto final
    texto = f"⚽ {time_a} {placar_a}x{placar_b} {time_b}\n\n"
    
    if cravadas:
        texto += f"🎯 CRAVANDO O PLACAR (25 pts) — {len(cravadas)} PESSOAS!!\n"
        texto += ", ".join(cravadas) + " 🎉🔥\n\n"
        
    if na_trave:
        texto += f"🥈 Resultado + gols de um lado (15 pts) — {len(na_trave)} pessoas:\n"
        texto += ", ".join(na_trave) + "\n\n"
        
    if resultado:
        texto += f"✅ Resultado correto (10 pts):\n"
        texto += ", ".join(resultado) + "\n\n"
        
    if consolacao:
        texto += f"⚽ Acertou um placar (3 pts):\n"
        texto += ", ".join(consolacao) + "\n\n"
        
    texto += frase
    return texto