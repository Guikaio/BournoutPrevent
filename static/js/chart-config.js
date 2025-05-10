/**
 * Configuração do Chart.js para o Sistema de Prevenção de Burnout
 * Este arquivo contém configurações para todos os gráficos usados no dashboard
 */

// Configura o comportamento responsivo para todos os gráficos

Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

/**
 /**
 * Cria um gráfico do tipo doughnut para exibir o nível de burnout
 * @param {string} canvasId - O ID do elemento canvas
 * @param {number} burnoutScore - A porcentagem do nível de burnout
 */
function createBurnoutScoreChart(canvasId, burnoutScore) {
  // Obtém o elemento canvas
  const ctx = document.getElementById(canvasId).getContext('2d');
  
  // Define as cores do gráfico com base na pontuação
  let color;
  if (burnoutScore < 40) {
    color = '#28a745'; // Verde para burnout baixo
  } else if (burnoutScore < 70) {
    color = '#ffc107'; // Amarelo para burnout moderado
  } else {
    color = '#dc3545'; // Vermelho para burnout alto
  }
  
  // Cria o gráfico
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [burnoutScore, 100 - burnoutScore],
        backgroundColor: [color, '#e9ecef'],
        borderWidth: 0
      }]
    },
    options: {
      cutout: '75%',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      },
      animation: {
        animateRotate: true,
        animateScale: true
      }
    }
  });
  
  // Adiciona o texto da pontuação no centro do gráfico
  const centerText = document.createElement('div');
  centerText.style.position = 'absolute';
  centerText.style.top = '50%';
  centerText.style.left = '50%';
  centerText.style.transform = 'translate(-50%, -50%)';
  centerText.style.fontSize = '2rem';
  centerText.style.fontWeight = 'bold';
  centerText.style.color = color;
  centerText.textContent = `${burnoutScore}%`;
  
  const chartContainer = document.getElementById(canvasId).parentNode;
  chartContainer.style.position = 'relative';
  chartContainer.appendChild(centerText);
}

/**
 * Cria um gráfico de linha para exibir o histórico de burnout
 * @param {string} canvasId - O ID do elemento canvas
 * @param {Array} historyData - Array de objetos com timestamp e score
 */
function createBurnoutHistoryChart(canvasId, historyData) {
  // Lida com dados vazios
  if (!historyData || historyData.length === 0) {
    const container = document.getElementById(canvasId).parentNode;
    const message = document.createElement('div');
    message.className = 'text-center text-muted p-4';
    message.textContent = 'Nenhum histórico disponível';
    container.replaceChild(message, document.getElementById(canvasId));
    return;
  }
  
  // Obtém o elemento canvas
  const ctx = document.getElementById(canvasId).getContext('2d');
  
  // Extrai datas e pontuações
  const labels = historyData.map(item => item.timestamp);
  const scores = historyData.map(item => item.score);
  
  // Cria o gradiente
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(63, 99, 180, 0.6)');
  gradient.addColorStop(1, 'rgba(63, 99, 180, 0.1)');
  
  // Cria o gráfico
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Nível de Burnout',
        data: scores,
        borderColor: '#3f63b4',
        backgroundColor: gradient,
        borderWidth: 2,
        pointBackgroundColor: '#3f63b4',
        pointBorderColor: '#fff',
        pointRadius: 5,
        pointHoverRadius: 7,
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Nível de Burnout (%)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Data'
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              return `Nível: ${context.raw}%`;
            }
          }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      },
      responsive: true,
      maintainAspectRatio: false
    }
  });
}

// Ajusta os gráficos automaticamente ao redimensionar a janela
window.addEventListener('resize', function() {
  if (Chart.instances) {
    for (let chart of Object.values(Chart.instances)) {
      chart.resize();
    }
  }
});
