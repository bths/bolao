async function carregarTudo() {
  const btn = document.getElementById('btn-atualizar');
  const status = document.getElementById('status');
  btn.disabled = true;
  status.innerText = 'Buscando resultados e atualizando ranking...';

  await Promise.all([atualizarJogos(), atualizarRanking(status)]);

  status.innerText = 'Tudo atualizado com sucesso!';
  setTimeout(() => { status.innerText = ''; }, 3000);
  btn.disabled = false;
}

function togglePalpites(id) {
  const container = document.getElementById(id);
  if (container.style.display === 'block') {
    container.style.display = 'none';
  } else {
    container.style.display = 'block';
  }
}

async function atualizarJogos() {
  const painel = document.getElementById('painel-copa');
  painel.innerHTML = ''; 

  try {
    const response = await fetch('/jogos');
    const data = await response.json();

    if(data.error) {
        painel.innerHTML = `<span class="erro">Erro nos jogos: ${data.error}</span>`;
        return;
    }

    const criarCard = (titulo, jogo, idContainer) => {
        if(!jogo) return '';
        
        let classeCor = 'status-agendado';
        if(jogo.statusOriginal === 'FINISHED') classeCor = 'status-encerrado';
        if(jogo.statusOriginal === 'IN_PLAY' || jogo.statusOriginal === 'PAUSED') classeCor = 'status-andamento';

        // 1. Lógica do Termômetro (Aparece sempre, e usa o nome dos times)
        let termometroHtml = '';
        if (jogo.termometro) {
            termometroHtml = `
            <div class="termometro-wrap">
                <div class="termometro-text">📊 ${jogo.termometro.casa}% ${jogo.timeCasa.toUpperCase()} | ${jogo.termometro.empate}% EMPATE | ${jogo.termometro.fora}% ${jogo.timeFora.toUpperCase()}</div>
                <div class="termometro-bar">
                    <div class="bar-casa" style="width: ${jogo.termometro.casa}%;"></div>
                    <div class="bar-empate" style="width: ${jogo.termometro.empate}%;"></div>
                    <div class="bar-fora" style="width: ${jogo.termometro.fora}%;"></div>
                </div>
            </div>`;
        }

        // 2. Lógica do Destaque da Partida (Maior Ousadia)
        let destaqueHtml = '';
        if (jogo.destaque) {
            destaqueHtml = `<div style="font-size: 0.85rem; color: #aaa; margin-top: 10px; text-align: center; font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.5px;">🏆 MAIOR OUSADIA: <span style="color: #fff; font-weight: bold;">${jogo.destaque.nome}</span> (Apostou ${jogo.destaque.placar})</div>`;
        }

        // 3. Botão do WhatsApp (Para jogos em andamento ou encerrados)
        let botaoZapHtml = '';
        if (jogo.linkWhatsapp) {
            botaoZapHtml = `<a href="${jogo.linkWhatsapp}" target="_blank" class="btn-zap">📲 Resumo pro Zap</a>`;
        }

        let palpitesHtml = '';
        if (jogo.palpites && jogo.palpites.length > 0) {
            jogo.palpites.forEach(p => {
                let isCravado = false;
                if ((jogo.statusOriginal === 'FINISHED' || jogo.statusOriginal === 'IN_PLAY' || jogo.statusOriginal === 'PAUSED') && jogo.placarCasa !== '-' && jogo.placarFora !== '-') {
                    const placarOficial = `${jogo.placarCasa} x ${jogo.placarFora}`;
                    if (p.placar === placarOficial) {
                        isCravado = true;
                    }
                }
                
                const classeCravado = isCravado ? 'palpite-cravado' : '';
                const iconeCravado = isCravado ? ' 🎯' : '';

                palpitesHtml += `<div class="palpite-item ${classeCravado}"><span class="palpite-nome">${p.nome}</span><span class="palpite-placar">${p.placar}${iconeCravado}</span></div>`;
            });
        } else {
            palpitesHtml = '<div class="palpite-item"><span class="palpite-nome" style="color: #666;">Nenhum palpite computado.</span></div>';
        }

        return `
        <div class="card-jogo">
          <div class="titulo-card">${titulo}</div>
          <span class="horario-card">🕒 ${jogo.horario}</span>
          <div class="placar-container">
            <div class="time">${jogo.timeCasa}</div>
            <div class="placar">${jogo.placarCasa} x ${jogo.placarFora}</div>
            <div class="time">${jogo.timeFora}</div>
          </div>
          <div class="status-rodape ${classeCor}">${jogo.statusPT}</div>
          
          ${termometroHtml}
          ${destaqueHtml}

          <button class="btn-palpites" onclick="togglePalpites('${idContainer}')">Ver Palpites</button>
          ${botaoZapHtml}
          <div id="${idContainer}" class="palpites-container">
            ${palpitesHtml}
          </div>
        </div>`;
    };

    let html = '';
    html += criarCard('Último Jogo', data.ultimoJogo, 'palpites-ultimo');
    html += criarCard('Ao Vivo', data.jogoAtual, 'palpites-atual');
    html += criarCard('Próximo Jogo', data.proximoJogo, 'palpites-proximo');

    if(html === '') {
        html = `<div class="card-jogo" style="color:#aaa;">Nenhum jogo rolando ou agendado no momento.</div>`;
    }
    painel.innerHTML = html;
  } catch (e) {
    painel.innerHTML = `<span class="erro">Erro ao carregar placares.</span>`;
  }
}

async function atualizarRanking(status) {
  try {
    const response = await fetch('/ranking');
    const data = await response.json();
    const tbody = document.querySelector('.tabela-ranking tbody');
    
    if(data.error) {
        tbody.innerHTML = `<tr><td colspan="4" class="erro">Erro no ranking: ${data.error}</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    
    const participantes = data.participantes;
    if (!participantes || participantes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#aaa;">Nenhum dado encontrado no ranking.</td></tr>`;
        return;
    }

    participantes.forEach(p => {
      // Classes das setinhas do ranking
      let varClass = 'var-neutral';
      if (p.variacao_icone === '⬆️') varClass = 'var-up';
      if (p.variacao_icone === '⬇️') varClass = 'var-down';

      let numeroVariacao = p.variacao_num || '';

      tbody.innerHTML += `
        <tr>
          <td class="pos">${p.posicao}º <span class="${varClass}" style="margin-left: 5px;">${p.variacao_icone} ${numeroVariacao}</span></td>
          <td class="nome-tb">${p.nome}</td>
          <td class="pontos-tb">${p.pontos}</td>
          <td class="premio-tb">${p.premio || '-'}</td>
        </tr>`;
    });
  } catch (e) {
    const tbody = document.querySelector('.tabela-ranking tbody');
    tbody.innerHTML = `<tr><td colspan="4" class="erro">Erro ao carregar o ranking.</td></tr>`;
  }
}

window.onload = carregarTudo;