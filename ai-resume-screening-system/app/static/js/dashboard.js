// Dashboard & Analytics Chart.js Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Check if chart elements exist on page
    const matchDonutEl = document.getElementById('matchDonutChart');
    const trendLineEl = document.getElementById('candidateTrendChart');
    const statusChartEl = document.getElementById('statusDonutChart');

    if (!matchDonutEl && !trendLineEl && !statusChartEl) {
        return;
    }

    // Set Chart.js dark theme defaults
    if (window.Chart) {
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.font.family = "'Outfit', 'Inter', sans-serif";
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 14, 23, 0.95)';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
    }

    // Fetch dynamic analytics data from backend
    fetch('/api/analytics/data')
        .then(response => response.json())
        .then(data => {
            // 1. Match Distribution Donut Chart
            if (matchDonutEl) {
                new Chart(matchDonutEl, {
                    type: 'doughnut',
                    data: {
                        labels: data.match_distribution.labels,
                        datasets: [{
                            data: data.match_distribution.data,
                            backgroundColor: [
                                '#10b981', // 90-100%
                                '#3b82f6', // 70-89%
                                '#f59e0b', // 50-69%
                                '#ef4444'  // <50%
                            ],
                            borderColor: '#121a2b',
                            borderWidth: 3,
                            hoverOffset: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '72%',
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    boxWidth: 12,
                                    padding: 15,
                                    color: '#cbd5e1',
                                    font: { size: 12 }
                                }
                            }
                        }
                    }
                });
            }

            // 2. Candidate Trend Line Chart
            if (trendLineEl) {
                new Chart(trendLineEl, {
                    type: 'line',
                    data: {
                        labels: data.candidate_trend.labels,
                        datasets: [{
                            label: 'Candidates Screened',
                            data: data.candidate_trend.data,
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139, 92, 246, 0.12)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.35,
                            pointBackgroundColor: '#6366f1',
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 2,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: {
                                grid: { color: 'rgba(255, 255, 255, 0.04)' },
                                ticks: { color: '#9ca3af' }
                            },
                            y: {
                                beginAtZero: true,
                                grid: { color: 'rgba(255, 255, 255, 0.04)' },
                                ticks: {
                                    color: '#9ca3af',
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            }

            // 3. Status Donut Chart (for dedicated analytics page)
            if (statusChartEl && data.status_counts) {
                const statusLabels = Object.keys(data.status_counts);
                const statusValues = Object.values(data.status_counts);
                
                new Chart(statusChartEl, {
                    type: 'doughnut',
                    data: {
                        labels: statusLabels,
                        datasets: [{
                            data: statusValues,
                            backgroundColor: ['#60a5fa', '#34d399', '#fbbf24', '#f87171'],
                            borderColor: '#121a2b',
                            borderWidth: 3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '65%',
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { boxWidth: 12, padding: 12, color: '#cbd5e1' }
                            }
                        }
                    }
                });
            }
        })
        .catch(err => console.error('Failed to load chart analytics:', err));
});
