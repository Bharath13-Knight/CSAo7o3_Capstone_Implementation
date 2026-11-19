document.addEventListener('DOMContentLoaded', () => {
    let monChart = null;
    let isPaused = false;
    let pollInterval = null;

    // Initialize Chart.js Line Chart
    function initMonChart() {
        const ctx = document.getElementById('monBandwidthChart')?.getContext('2d');
        if (!ctx) return;

        monChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Inbound Throughput (Mbps)',
                        borderColor: '#00E5FF',
                        backgroundColor: 'rgba(0, 229, 255, 0.1)',
                        fill: true,
                        tension: 0.35,
                        data: []
                    },
                    {
                        label: 'Outbound Throughput (Mbps)',
                        borderColor: '#3A86FF',
                        backgroundColor: 'rgba(58, 134, 255, 0.08)',
                        fill: true,
                        tension: 0.35,
                        data: []
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 300 },
                scales: {
                    x: {
                        grid: { color: '#1B2A4A' },
                        ticks: { color: '#8A99AD', font: { size: 10 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#1B2A4A' },
                        ticks: { color: '#8A99AD', font: { size: 10 } }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#CAD5E2', font: { size: 11 } }
                    }
                }
            }
        });
    }

    initMonChart();

    // Fetch and render live monitoring feed
    async function fetchMonitoringFeed() {
        if (isPaused) return;

        try {
            // 1. Fetch live metrics
            const resStatus = await fetch('/api/monitoring/status');
            const dataStatus = await resStatus.json();

            if (dataStatus.success && dataStatus.status) {
                const s = dataStatus.status;
                const m = s.metrics;

                // Update summary bar
                document.getElementById('mon-total-packets').textContent = m.total_packets.toLocaleString();
                document.getElementById('mon-total-bw').innerHTML = `${m.total_bandwidth_mbps} <span style="font-size:0.9rem;">Mbps</span>`;
                document.getElementById('mon-bw-in').innerHTML = `${m.bandwidth_in_mbps} <span style="font-size:0.9rem;">Mbps</span>`;
                document.getElementById('mon-utilization').textContent = `${m.bandwidth_utilization_pct}%`;

                // Update Chart
                if (monChart && m.time_series) {
                    monChart.data.labels = m.time_series.labels.slice(-30);
                    monChart.data.datasets[0].data = m.time_series.bandwidth_in.slice(-30);
                    monChart.data.datasets[1].data = m.time_series.bandwidth_out.slice(-30);
                    monChart.update('none');
                }
            }

            // 2. Fetch filtered packets
            const proto = document.getElementById('filter-protocol').value;
            const prio = document.getElementById('filter-priority').value;
            const srcIp = document.getElementById('filter-src-ip').value.trim();
            const dstIp = document.getElementById('filter-dst-ip').value.trim();

            let url = `/api/monitoring/packets?limit=40&protocol=${proto}&priority=${prio}`;
            if (srcIp) url += `&src_ip=${encodeURIComponent(srcIp)}`;
            if (dstIp) url += `&dst_ip=${encodeURIComponent(dstIp)}`;

            const resPackets = await fetch(url);
            const dataPackets = await resPackets.json();

            if (dataPackets.success && dataPackets.packets) {
                renderPacketTable(dataPackets.packets);
                document.getElementById('mon-packet-count-badge').textContent = `Showing ${dataPackets.packets.length} packets`;
            }

        } catch (err) {
            console.error('Monitoring feed fetch error:', err);
        }
    }

    function renderPacketTable(packets) {
        const tbody = document.getElementById('mon-packets-tbody');
        if (!tbody) return;

        if (packets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No matching packets found for active filters.</td></tr>`;
            return;
        }

        tbody.innerHTML = packets.map((p, idx) => {
            const prioBadge = p.priority === 'HIGH' ? 'badge-high' : p.priority === 'LOW' ? 'badge-low' : 'badge-med';
            const protoColor = p.protocol === 'UDP' ? '#00E5FF' : p.protocol === 'TCP' ? '#3A86FF' : p.protocol === 'ICMP' ? '#FFD166' : '#A78BFA';

            return `
                <tr>
                    <td class="text-muted" style="font-size:0.75rem;">${idx + 1}</td>
                    <td class="text-muted" style="font-size:0.75rem;">${p.timestamp || ''}</td>
                    <td><code>${p.src_ip}${p.src_port ? ':' + p.src_port : ''}</code></td>
                    <td><code>${p.dst_ip}${p.dst_port ? ':' + p.dst_port : ''}</code></td>
                    <td><span class="badge" style="background-color: ${protoColor}; color:#070B14; font-weight:700;">${p.protocol}</span></td>
                    <td>${p.length} B</td>
                    <td><span class="badge ${prioBadge}">${p.priority}</span></td>
                    <td class="fw-semibold text-white">${p.application || '-'}</td>
                    <td class="text-muted" style="font-size:0.78rem;">${p.info || ''}</td>
                </tr>
            `;
        }).join('');
    }

    // Controls Event Listeners
    document.getElementById('btn-start-mon')?.addEventListener('click', async () => {
        const mode = document.getElementById('mon-mode-select').value;
        const rate = parseInt(document.getElementById('rate-slider').value) || 10;
        try {
            const res = await fetch('/api/monitoring/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ mode: mode, rate: rate })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Traffic monitoring started in ${data.result.mode} mode`, 'success');
                fetchMonitoringFeed();
            }
        } catch (err) {
            showToast('Start monitoring failed: ' + err, 'error');
        }
    });

    document.getElementById('btn-stop-mon')?.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/monitoring/stop', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Monitoring stopped.', 'info');
            }
        } catch (err) {
            showToast('Stop monitoring failed: ' + err, 'error');
        }
    });

    document.getElementById('btn-clear-traffic')?.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/monitoring/clear', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Captured traffic cleared.', 'info');
                fetchMonitoringFeed();
            }
        } catch (err) {
            showToast('Clear traffic failed: ' + err, 'error');
        }
    });

    // Pause / Resume Feed
    document.getElementById('btn-pause-refresh')?.addEventListener('click', () => {
        isPaused = !isPaused;
        const btn = document.getElementById('btn-pause-refresh');
        const txt = document.getElementById('pause-text');
        if (isPaused) {
            txt.textContent = 'Resume Feed';
            btn.className = 'btn btn-outline-warning btn-sm';
            showToast('Feed paused for packet inspection.', 'info');
        } else {
            txt.textContent = 'Pause Feed';
            btn.className = 'btn btn-outline-info btn-sm';
            showToast('Feed resumed.', 'info');
            fetchMonitoringFeed();
        }
    });

    // Rate Slider Listener
    const rateSlider = document.getElementById('rate-slider');
    rateSlider?.addEventListener('input', (e) => {
        document.getElementById('rate-val').textContent = e.target.value;
    });

    // Filters Change Listeners
    ['filter-protocol', 'filter-priority'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', fetchMonitoringFeed);
    });
    ['filter-src-ip', 'filter-dst-ip'].forEach(id => {
        document.getElementById(id)?.addEventListener('keyup', fetchMonitoringFeed);
    });

    // Polling Loop
    fetchMonitoringFeed();
    pollInterval = setInterval(fetchMonitoringFeed, 1200);
});
