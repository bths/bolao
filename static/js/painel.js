async function carregarLogs() {
    try {
        const response = await fetch('/api/logs_lista');
        const logs = await response.json();
        const corpo = document.getElementById('logs-corpo');
        
        if (logs.length === 0) {
            corpo.innerHTML = '<tr><td colspan="4" style="text-align:center;">Nenhum acesso registrado ainda.</td></tr>';
            return;
        }

        corpo.innerHTML = logs.map(l => `
            <tr>
                <td>${l.timestamp}</td>
                <td>${l.ip}</td>
                <td>${l.cidade}, ${l.estado} - ${l.pais}</td>
                <td>${l.evento === 'abertura' ? '🟢 Abertura' : '🔴 Fechamento'}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Erro ao carregar logs:", e);
    }
}

// Carrega os logs ao abrir o painel
carregarLogs();

// Opcional: Atualiza a tabela automaticamente a cada 10 segundos
setInterval(carregarLogs, 10000);

// Log de Abertura (para registrar a visita do admin também)
fetch('/api/log', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ evento: 'abertura' })
});