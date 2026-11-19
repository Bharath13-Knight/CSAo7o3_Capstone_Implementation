document.addEventListener('DOMContentLoaded', () => {
    let latencyChart = null;
    let lossChart = null;
    let throughputChart = null;
    let timelineChart = null;
    let latestCsvFilename = null;

    function initCharts() {
        // 1. Latency Bar Chart
        const ctxLat = document.getElementById('latencyBarChart')?.getContext('2d');
        if (ctxLat) {
            latencyChart = new Chart(ctxLat, {
                type: 'bar',
                data: {
                    labels: ['High (VoIP/Video)', 'Medium (Web/DNS)', 'Low (FTP/Bulk)', 'Aggregate'],
                    datasets: [
                        {
                            label: 'Before QoS (ms)',
                            backgroundColor: 'rgba(255, 51, 102, 0.7)',
                            borderColor: '#FF3366',
                            borderWidth: 1,
                            data: [126.4, 140.2, 153.0, 139.8]
                        },
                        {
                            label: 'After QoS (ms)',
                            backgroundColor: 'rgba(6, 214, 160, 0.7)',
                            borderColor: '#06D6A0',
                            borderWidth: 1,
                            data: [13.2, 25.4, 98.0, 45.5]
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } },
                        y: { beginAtZero: true, grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#CAD5E2' } }
                    }
                }
            });
        }

        // 2. Packet Loss Bar Chart
        const ctxLoss = document.getElementById('lossBarChart')?.getContext('2d');
        if (ctxLoss) {
            lossChart = new Chart(ctxLoss, {
                type: 'bar',
                data: {
                    labels: ['High (VoIP/Video)', 'Medium (Web/DNS)', 'Low (FTP/Bulk)', 'Aggregate'],
                    datasets: [
                        {
                            label: 'Before QoS (%)',
                            backgroundColor: 'rgba(255, 183, 3, 0.7)',
                            borderColor: '#FFB703',
                            borderWidth: 1,
                            data: [13.8, 16.2, 19.5, 16.5]
                        },
                        {
                            label: 'After QoS (%)',
                            backgroundColor: 'rgba(0, 229, 255, 0.7)',
                            borderColor: '#00E5FF',
                            borderWidth: 1,
                            data: [0.0, 0.2, 4.8, 1.6]
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } },
                        y: { beginAtZero: true, grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#CAD5E2' } }
                    }
                }
            });
        }

        // 3. Throughput Bar Chart
        const ctxTp = document.getElementById('throughputBarChart')?.getContext('2d');
        if (ctxTp) {
            throughputChart = new Chart(ctxTp, {
                type: 'bar',
                data: {
                    labels: ['High Priority', 'Medium Priority', 'Low Priority (Bulk)'],
                    datasets: [
                        {
                            label: 'Before QoS (Mbps)',
                            backgroundColor: 'rgba(114, 9, 183, 0.7)',
                            borderColor: '#7209B7',
                            borderWidth: 1,
                            data: [7.8, 13.2, 73.5]
                        },
                        {
                            label: 'After QoS (Mbps)',
                            backgroundColor: 'rgba(58, 134, 255, 0.7)',
                            borderColor: '#3A86FF',
                            borderWidth: 1,
                            data: [25.5, 30.0, 15.0]
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } },
                        y: { beginAtZero: true, grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#CAD5E2' } }
                    }
                }
            });
        }

        // 4. Latency Timeline Line Chart
        const ctxTl = document.getElementById('latencyTimelineChart')?.getContext('2d');
        if (ctxTl) {
            timelineChart = new Chart(ctxTl, {
                type: 'line',
                data: {
                    labels: ['T+1s', 'T+2s', 'T+3s', 'T+4s', 'T+5s', 'T+6s', 'T+7s', 'T+8s', 'T+9s', 'T+10s'],
                    datasets: [
                        {
                            label: 'Before QoS (Contended)',
                            borderColor: '#FF3366',
                            backgroundColor: 'rgba(255, 51, 102, 0.1)',
                            fill: true,
                            tension: 0.35,
                            data: [15.2, 22.0, 95.4, 134.2, 148.0, 155.6, 142.1, 139.0, 145.2, 138.0]
                        },
                        {
                            label: 'After QoS (Prioritized)',
                            borderColor: '#06D6A0',
                            backgroundColor: 'rgba(6, 214, 160, 0.1)',
                            fill: true,
                            tension: 0.35,
                            data: [12.1, 13.0, 14.2, 13.8, 12.5, 13.2, 12.9, 13.4, 12.7, 12.8]
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } },
                        y: { beginAtZero: true, grid: { color: '#1B2A4A' }, ticks: { color: '#CAD5E2' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#CAD5E2' } }
                    }
                }
            });
        }
    }

    initCharts();

    // Run Benchmark Execution
    async function runBenchmark() {
        const mode = document.getElementById('bench-mode-select').value;
        const btn = document.getElementById('btn-run-benchmark');
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Benchmarking...`;

        showToast('Executing Before QoS and After QoS comparative scenarios...', 'info');

        try {
            const res = await fetch('/api/performance/benchmark', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ mode: mode })
            });
            const data = await res.json();

            if (data.success && data.benchmark) {
                const b = data.benchmark;
                latestCsvFilename = b.csv_filename;

                // Update CSV Download Button
                const btnDownload = document.getElementById('btn-download-latest-csv');
                btnDownload.href = `/api/reports/download/${latestCsvFilename}`;

                // Update Charts with fresh benchmark data
                updateChartsWithResults(b);

                // Update Comparison Summary Table
                renderSummaryTable(b.comparison);

                // Update KPI Cards
                if (b.comparison && b.comparison.length > 0) {
                    const voice = b.comparison[0];
                    document.getElementById('perf-kpi-latency').textContent = `-${voice.latency_improvement_pct}%`;
                    document.getElementById('perf-kpi-latency-sub').textContent = `${voice.before_latency} ms \u2192 ${voice.after_latency} ms`;

                    document.getElementById('perf-kpi-loss').textContent = `${voice.after_loss}%`;
                    document.getElementById('perf-kpi-loss-sub').textContent = `Reduced from ${voice.before_loss}% (Zero Loss)`;

                    document.getElementById('perf-kpi-jitter').textContent = `-${voice.jitter_improvement_pct}%`;
                    document.getElementById('perf-kpi-jitter-sub').textContent = `${voice.before_jitter} ms \u2192 ${voice.after_jitter} ms`;
                }

                showToast(`Benchmark completed successfully! Report generated: ${latestCsvFilename}`, 'success');
            }

        } catch (err) {
            showToast('Benchmark execution error: ' + err, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" class="me-1"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Run QoS Evaluation Benchmark`;
        }
    }

    function updateChartsWithResults(b) {
        if (!b.before_qos || !b.after_qos) return;

        const before = b.before_qos;
        const after = b.after_qos;

        // 1. Latency Bar
        if (latencyChart) {
            latencyChart.data.datasets[0].data = before.map(x => x.latency_ms);
            latencyChart.data.datasets[1].data = after.map(x => x.latency_ms);
            latencyChart.update();
        }

        // 2. Loss Bar
        if (lossChart) {
            lossChart.data.datasets[0].data = before.map(x => x.packet_loss_percent);
            lossChart.data.datasets[1].data = after.map(x => x.packet_loss_percent);
            lossChart.update();
        }

        // 3. Throughput Bar (first 3 classes)
        if (throughputChart) {
            throughputChart.data.datasets[0].data = before.slice(0, 3).map(x => x.throughput_mbps);
            throughputChart.data.datasets[1].data = after.slice(0, 3).map(x => x.throughput_mbps);
            throughputChart.update();
        }

        // 4. Timeline Line
        if (timelineChart && b.time_series_simulation) {
            timelineChart.data.datasets[0].data = b.time_series_simulation.before_qos_latency;
            timelineChart.data.datasets[1].data = b.time_series_simulation.after_qos_latency;
            timelineChart.update();
        }
    }

    function renderSummaryTable(comparison) {
        const tbody = document.getElementById('perf-summary-tbody');
        if (!tbody || !comparison) return;

        tbody.innerHTML = comparison.map(c => {
            const isHigh = c.traffic_type.includes('High');
            const rowClass = isHigh ? 'table-active' : '';

            return `
                <tr class="${rowClass}">
                    <td class="fw-bold text-white">${c.traffic_type}</td>
                    <td>${c.before_throughput} Mbps</td>
                    <td class="text-info fw-semibold">${c.after_throughput} Mbps</td>
                    <td class="text-danger">${c.before_latency} ms</td>
                    <td class="text-success fw-bold">${c.after_latency} ms</td>
                    <td><span class="badge badge-low">-${c.latency_improvement_pct}%</span></td>
                    <td class="text-danger">${c.before_loss}%</td>
                    <td class="text-success fw-bold">${c.after_loss}%</td>
                    <td><span class="badge badge-sim">-${c.jitter_improvement_pct}%</span></td>
                </tr>
            `;
        }).join('');
    }

    document.getElementById('btn-run-benchmark')?.addEventListener('click', runBenchmark);

    // Initial run on page load
    runBenchmark();
});
