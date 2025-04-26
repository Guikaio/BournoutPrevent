/**
 * Chart.js configuration for the Burnout Prevention System
 * This file contains configurations for all charts used in the dashboard
 */

// Configure responsive behavior for all charts
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

/**
 * Creates a doughnut chart to display burnout score
 * @param {string} canvasId - The ID of the canvas element
 * @param {number} burnoutScore - The burnout score percentage
 */
function createBurnoutScoreChart(canvasId, burnoutScore) {
  // Get the canvas element
  const ctx = document.getElementById(canvasId).getContext('2d');
  
  // Define chart colors based on score
  let color;
  if (burnoutScore < 40) {
    color = '#28a745'; // Green for low burnout
  } else if (burnoutScore < 70) {
    color = '#ffc107'; // Yellow for medium burnout
  } else {
    color = '#dc3545'; // Red for high burnout
  }
  
  // Create the chart
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
  
  // Add score text in the center of doughnut
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
 * Creates a line chart to display burnout history
 * @param {string} canvasId - The ID of the canvas element
 * @param {Array} historyData - Array of objects with timestamp and score properties
 */
function createBurnoutHistoryChart(canvasId, historyData) {
  // Handle empty data
  if (!historyData || historyData.length === 0) {
    const container = document.getElementById(canvasId).parentNode;
    const message = document.createElement('div');
    message.className = 'text-center text-muted p-4';
    message.textContent = 'Nenhum histórico disponível';
    container.replaceChild(message, document.getElementById(canvasId));
    return;
  }
  
  // Get the canvas element
  const ctx = document.getElementById(canvasId).getContext('2d');
  
  // Extract dates and scores
  const labels = historyData.map(item => item.timestamp);
  const scores = historyData.map(item => item.score);
  
  // Create gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(63, 99, 180, 0.6)');
  gradient.addColorStop(1, 'rgba(63, 99, 180, 0.1)');
  
  // Create the chart
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

// Automatically adjust charts on window resize
window.addEventListener('resize', function() {
  if (Chart.instances) {
    for (let chart of Object.values(Chart.instances)) {
      chart.resize();
    }
  }
});
