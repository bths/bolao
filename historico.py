# historico.py

def obter_dados_semente():
    """
    Retorna a matriz inicial cravada para popular o banco de dados
    pela primeira vez, do Jogo 1 ao Jogo 30.
    """
    labels_iniciais = [
        "J1 · México 2x0", "J2 · Coreia 2x1", "J3 · Canadá 1x1", "J4 · EUA 4x1", 
        "J5 · Catar 1x1", "J6 · Brasil 1x1", "J7 · Haiti 0x1", "J8 · Austrália 2x0", 
        "J9 · Alemanha 7x1", "J10 · Holanda 2x2", "J11 · C.Marfim 1x0", "J12 · Suécia 5x1", 
        "J13 · Espanha 0x0", "J14 · Bélgica 1x1", "J15 · Arábia 1x1", "J16 · Irã 2x2", 
        "J17 · França 3x1", "J18 · Iraque 1x4", "J19 · Argentina 3x0", "J20 · Áustria 3x1", 
        "J21 · Portugal 1x1", "J22 · Inglaterra 4x2", "J23 · Gana 1x0", "J24 · Uzbequistão 1x3", 
        "J25 · Á.do Sul 1x1", "J26 · Bósnia 1x4", "J27 · Canadá 6x0", "J28 · México 1x0", "J30 · EUA 2x0"
    ]

    cores = [
      "#F5C518","#00C48C","#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7",
      "#DDA0DD","#98D8C8","#F7DC6F","#BB8FCE","#85C1E9","#F1948A","#82E0AA",
      "#F8C471","#AED6F1","#A9DFBF","#FAD7A0","#D2B4DE","#A3E4D7","#F9E79F",
      "#D5D8DC","#ABB2B9"
    ]

    dados_brutos = [
      { "nome": "Pedro Damique",      "pts": [25,28,31,34,37,40,65,65,75,85,88,91,94,97,100,100,125,140,155,165,165,175,200,210,235,250,265,280,290] },
      { "nome": "Pedro Bottany",      "pts": [25,25,28,43,46,49,64,64,74,77,87,102,105,108,133,136,161,176,186,196,199,209,224,249,252,267,277,280,283] },
      { "nome": "Daniel Amaral",      "pts": [25,28,53,68,68,71,96,96,106,109,112,122,125,125,128,128,138,153,178,188,188,198,213,228,228,243,253,256,281] },
      { "nome": "Igor Chiappetta",    "pts": [25,28,31,41,41,44,59,59,69,72,75,90,93,96,96,96,121,131,146,171,174,184,209,219,219,234,249,259,269] },
      { "nome": "João Spido",         "pts": [25,28,53,68,68,68,83,83,93,96,99,109,112,112,115,118,133,143,168,178,178,188,198,213,216,226,241,251,266] },
      { "nome": "Paulo Sérgio",       "pts": [15,18,43,46,46,46,61,61,76,76,76,91,94,94,97,107,122,137,152,162,162,172,187,202,205,215,230,240,265] },
      { "nome": "João Otávio",        "pts": [25,35,38,48,51,76,86,86,101,104,107,110,113,116,119,119,144,154,169,179,182,192,207,222,232,232,247,247,262] },
      { "nome": "Daniel Mourão",      "pts": [15,25,28,38,38,38,53,53,63,73,76,86,89,92,95,105,120,130,145,155,155,165,190,205,208,223,233,243,258] },
      { "nome": "Pedro Longo",        "pts": [15,18,21,24,24,27,52,52,62,65,65,68,71,74,77,80,95,105,120,130,130,140,165,175,175,185,200,215,240] },
      { "nome": "Bernard Haus",       "pts": [0,0,3,3,6,16,31,31,41,66,66,81,84,84,87,87,112,122,147,157,160,185,200,215,215,218,228,238,238] },
      { "nome": "Jefferson Raphael",  "pts": [15,18,21,24,24,27,42,42,52,55,58,68,71,71,71,81,91,101,126,136,136,136,161,176,201,216,216,226,236] },
      { "nome": "Bernardo Bastos",    "pts": [25,40,43,46,46,49,64,64,74,99,99,109,112,115,118,118,128,138,153,168,168,168,178,188,191,206,216,216,231] },
      { "nome": "Rafael Licurgo",     "pts": [15,15,15,18,18,21,36,36,46,49,49,59,62,65,68,71,81,96,106,116,116,131,146,161,164,179,194,204,229] },
      { "nome": "Yuri Alkmim",        "pts": [25,40,43,43,46,46,61,61,71,96,96,106,109,119,122,125,128,138,138,148,148,148,173,176,176,179,194,204,229] },
      { "nome": "Bruno Mourão",       "pts": [15,25,28,31,41,41,56,56,81,84,84,94,97,97,97,97,107,117,132,147,147,147,162,172,175,185,200,210,225] },
      { "nome": "Pablo Andres",       "pts": [15,18,21,24,24,24,24,24,34,37,40,50,53,56,59,62,87,97,112,122,122,132,157,167,192,195,210,225,225] },
      { "nome": "Danilo Belinguinho", "pts": [15,15,18,18,18,21,24,24,39,39,49,64,64,67,70,73,76,91,106,121,121,131,141,156,181,181,181,191,216] },
      { "nome": "João Dabul",         "pts": [0,3,6,6,6,9,12,12,22,25,35,50,50,53,56,59,84,84,99,109,112,122,137,147,147,162,177,187,202] },
      { "nome": "João Pedro",         "pts": [25,28,31,46,46,49,64,64,74,77,80,90,93,93,93,96,111,121,136,146,146,146,156,171,171,186,186,186,201] },
      { "nome": "Matheus Roro",       "pts": [25,35,35,35,35,38,48,48,58,61,64,67,70,73,73,83,93,103,118,118,118,121,146,161,164,164,179,182,197] },
      { "nome": "Lucas Santos",       "pts": [0,0,0,0,0,0,0,0,0,3,28,43,46,56,59,62,72,82,97,107,107,117,132,135,138,138,138,163,173] },
      { "nome": "Pedro Gonçalves",    "pts": [0,0,0,0,0,0,0,0,15,18,18,28,31,31,31,34,49,64,74,84,84,94,97,122,122,137,147,157,167] },
      { "nome": "Cicero Demetrio",    "pts": [0,0,0,0,0,0,0,0,10,10,10,20,20,23,48,48,58,68,83,86,86,101,111,121,131,146,156,156,159] }
    ]

    for i, d in enumerate(dados_brutos):
        d["cor"] = cores[i % len(cores)]

    return labels_iniciais, dados_brutos

def processar_historico_grafico(jogos_encerrados_planilha, ranking_atualizado, db_labels_antigos, db_dados_antigos):
    """
    Analisa os jogos fechados na planilha e compara com a memória do banco.
    """
    if not db_labels_antigos or not db_dados_antigos:
        db_labels_antigos, db_dados_antigos = obter_dados_semente()

    pontos_agora = { p["nome"]: p["pontos"] for p in ranking_atualizado }
    
    novos_labels = db_labels_antigos.copy()
    novos_dados = db_dados_antigos.copy()

    qtd_antigos = len(db_labels_antigos)
    jogos_novos = jogos_encerrados_planilha[qtd_antigos:]

    if not jogos_novos:
        return novos_labels, novos_dados

    for jogo in jogos_novos:
        novos_labels.append(jogo)
        
        for jogador in novos_dados:
            nome = jogador["nome"]
            historico = jogador["pts"]
            
            pontos_hoje = pontos_agora.get(nome, historico[-1] if historico else 0)
            historico.append(pontos_hoje)

    return novos_labels, novos_dados