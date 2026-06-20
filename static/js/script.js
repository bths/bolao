// === VARIÁVEIS GLOBAIS DO GRÁFICO ===
let chartInstance = null;
let currentFilter = 'all';
let jogosLabels = [];
let dadosGrafico = [];

async function carregarTudo() {
  const btn = document.getElementById('btn-atualizar');
  const status = document.getElementById('status');
  if (btn) btn.disabled = true;
  if (status) status.innerText = 'Buscando resultados e atualizando ranking...';

  // Adicionado o carregarGrafico() para rodar junto com jogos e ranking
  await Promise.all([atualizarJogos(), atualizarRanking(status), carregarGrafico()]);

  if (status) status.innerText = 'Tudo atualizado com sucesso!';
  setTimeout(() => { if (status) status.innerText = ''; }, 3000);
  if (btn) btn.disabled = false;
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
  if (!painel) return;
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

        // 1. Lógica do Termômetro
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

        // 3. Botão do WhatsApp
        /*
        let botaoZapHtml = '';
        if (jogo.linkWhatsapp) {
            botaoZapHtml = `<a href="${jogo.linkWhatsapp}" target="_blank" class="btn-zap">📲 Resumo pro Zap</a>`;
        }
         */
        let palpitesHtml = '';
        if (jogo.palpites && jogo.palpites.length > 0) {
            jogo.palpites.forEach(p => {
                let isCravado = false;
                
                // Pega o placar oficial e tira TUDO que não for número (ex: "-" vira "")
                const casaOf = String(jogo.placarCasa).replace(/[^0-9]/g, '');
                const foraOf = String(jogo.placarFora).replace(/[^0-9]/g, '');

                // Se tiver número nos dois lados, o jogo já começou ou acabou
                if (casaOf !== '' && foraOf !== '') {
                    
                    // Junta os números. Ex: Casa "1" e Fora "3" vira "13"
                    const oficialLimpo = casaOf + foraOf;
                    
                    // Pega o palpite do usuário e tira tudo que não for número. Ex: "1 x 3" vira "13"
                    const palpiteLimpo = String(p.placar).replace(/[^0-9]/g, '');
                    
                    // Bate os números secos
                    if (oficialLimpo === palpiteLimpo) {
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
          <!-- botaoZapHtml desativado temporariamente -->
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
    
    if (!tbody) return;

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
    if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="erro">Erro ao carregar o ranking.</td></tr>`;
  }
}

// === NOVA LÓGICA DO GRÁFICO DINÂMICO ===
async function carregarGrafico() {
    try {
        const response = await fetch('/api/grafico');
        const json = await response.json();

        if (json.error) throw new Error(json.error);

        jogosLabels = json.labels || [];
        dadosGrafico = json.dados || [];

        // Só desenha se houver dados
        if (jogosLabels.length > 0 && dadosGrafico.length > 0) {
            buildChart('all');
            gerarLegenda();
        }
    } catch (e) {
        console.error("Erro ao carregar o gráfico:", e);
    }
}

function getDatasets(filter) {
    let sorted = [...dadosGrafico].sort((a,b) => b.pts[b.pts.length-1] - a.pts[a.pts.length-1]);
    let visible;
    if (filter === 'top5') visible = sorted.slice(0,5).map(d=>d.nome);
    else if (filter === 'top10') visible = sorted.slice(0,10).map(d=>d.nome);
    else if (filter === 'bottom') visible = sorted.slice(-7).map(d=>d.nome);
    else visible = dadosGrafico.map(d=>d.nome);

    return dadosGrafico.map(d => ({
        label: d.nome,
        data: d.pts,
        borderColor: d.cor,
        backgroundColor: d.cor + '22',
        borderWidth: visible.includes(d.nome) ? 2.5 : 0.4,
        pointRadius: visible.includes(d.nome) ? 4 : 1,
        pointHoverRadius: 7,
        tension: 0.3,
        hidden: false,
        opacity: visible.includes(d.nome) ? 1 : 0.15,
    }));
}

function buildChart(filter) {
    const ctxEl = document.getElementById('chart');
    if(!ctxEl) return;
    const ctx = ctxEl.getContext('2d');
    
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: jogosLabels,
            datasets: getDatasets(filter),
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1a1a1a', borderColor: '#333', borderWidth: 1,
                    titleColor: '#F5C518', titleFont: { family: 'Barlow Condensed', size: 13, weight: '700' },
                    bodyColor: '#ccc', bodyFont: { family: 'Barlow', size: 12 }, padding: 12,
                    callbacks: {
                        title: (items) => items[0].label,
                        label: (item) => ` ${item.dataset.label}: ${item.raw} pts`,
                        afterBody: (items) => {
                            const sorted = [...items].sort((a,b) => b.raw - a.raw);
                            return ['', '🏆 Ranking neste jogo:', ...sorted.slice(0,5).map((it,i) => `  ${i+1}º ${it.dataset.label} — ${it.raw}pts`)];
                        }
                    }
                }
            },
            scales: {
                x: { grid: { color: '#1a1a1a' }, ticks: { color: '#666', font: { family: 'Barlow Condensed', size: 11 } } },
                y: { grid: { color: '#1a1a1a' }, ticks: { color: '#888', font: { family: 'Barlow Condensed', size: 12 } }, title: { display: true, text: 'Pontos Acumulados', color: '#555', font: { family: 'Barlow Condensed', size: 12 } } }
            }
        }
    });
}

function filterGroup(filter, event) {
    currentFilter = filter;
    document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
    if(event) event.target.classList.add('active');
    buildChart(filter);
}

function gerarLegenda() {
    const legendEl = document.getElementById('legend');
    if(!legendEl) return;
    legendEl.innerHTML = '';
    
    const sorted = [...dadosGrafico].sort((a,b) => b.pts[b.pts.length-1] - a.pts[a.pts.length-1]);
    
    sorted.forEach((d) => {
        const el = document.createElement('div');
        el.className = 'legend-item';
        el.innerHTML = `<div class="legend-dot" style="background:${d.cor}"></div><span class="legend-name">${d.nome}</span><span class="legend-pts">${d.pts[d.pts.length-1]}pts</span>`;
        el.onclick = () => {
            const ds = chartInstance.data.datasets.find(x => x.label === d.nome);
            if (ds) {
                ds.borderWidth = ds.borderWidth < 2 ? 2.5 : 0.4;
                ds.pointRadius = ds.pointRadius < 3 ? 4 : 1;
                chartInstance.update();
            }
        };
        legendEl.appendChild(el);
    });
}

// === NOVA LÓGICA DO GRÁFICO DINÂMICO ===
async function carregarGrafico() {
    try {
        const response = await fetch('/api/grafico');
        const json = await response.json();

        if (json.error) throw new Error(json.error);

        // A MÁGICA ESTÁ AQUI: Transforma o texto em Array (se vier como texto)
        jogosLabels = typeof json.labels === 'string' ? JSON.parse(json.labels) : (json.labels || []);
        dadosGrafico = typeof json.dados === 'string' ? JSON.parse(json.dados) : (json.dados || []);

        // Só desenha se houver dados
        if (jogosLabels.length > 0 && dadosGrafico.length > 0) {
            buildChart('all');
            gerarLegenda();
        }
    } catch (e) {
        console.error("Erro ao carregar o gráfico:", e);
    }
}

window.onload = carregarTudo;