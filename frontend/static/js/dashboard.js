document.addEventListener('DOMContentLoaded', () => {
    let bandwidthChart = null;
    let priorityDonutChart = null;

    // Initialize Chart.js charts
    function initCharts() {
        // 1. Bandwidth Stream Line Chart
        const ctxBw = document.getElementById('bandwidthChart')?.getContext('2d');
        if (ctxBw) {
            bandwidthChart = new Chart(ctxBw, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Incoming (Mbps)',
                            borderColor: '#00E5FF',
                            backgroundColor: 'rgba(0, 229, 255, 0.12)',
                            fill: true,
                            tension: 0.35,
                            data: []
                        },
                        {
                            label: 'Outgoing (Mbps)',
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
                    animation: { duration: 400 },
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

        // 2. Priority Donut Chart
        const ctxDonut = document.getElementById('priorityDonutChart')?.getContext('2d');
        if (ctxDonut) {
            priorityDonutChart = new Chart(ctxDonut, {
                type: 'doughnut',
                data: {
                    labels: ['High Priority', 'Medium Priority', 'Low Priority'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#FF3366', '#FFB703', '#06D6A0'],
                        borderColor: '#162447',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '70%',
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }

    initCharts();

    // Fetch and update dashboard telemetry
    async function updateDashboard() {
        try {
            // 1. Fetch monitoring status & metrics
            const resMon = await fetch('/api/monitoring/status');
            const dataMon = await resMon.json();
            
            if (dataMon.success && dataMon.status) {
                const s = dataMon.status;
                const m = s.metrics;

                // Update KPIs
                document.getElementById('kpi-packets').textContent = m.total_packets.toLocaleString();
                document.getElementById('kpi-bw-in').innerHTML = `${m.bandwidth_in_mbps} <span style="font-size:1rem;">Mbps</span>`;
                document.getElementById('kpi-bw-out').innerHTML = `${m.bandwidth_out_mbps} <span style="font-size:1rem;">Mbps</span>`;
                document.getElementById('kpi-utilization').textContent = `${m.bandwidth_utilization_pct}%`;
                document.getElementById('kpi-high-pct').textContent = `${m.high_priority_pct}%`;

                // Update Nav Badge
                const modeBadge = document.getElementById('global-mode-badge');
                if (modeBadge) modeBadge.textContent = s.mode;

                // Update Line Chart
                if (bandwidthChart && m.time_series) {
                    bandwidthChart.data.labels = m.time_series.labels.slice(-20);
                    bandwidthChart.data.datasets[0].data = m.time_series.bandwidth_in.slice(-20);
                    bandwidthChart.data.datasets[1].data = m.time_series.bandwidth_out.slice(-20);
                    bandwidthChart.update('none');
                }

                // Update Donut Chart & Legends
                const high = m.priority_counts.HIGH || 0;
                const med = m.priority_counts.MEDIUM || 0;
                const low = m.priority_counts.LOW || 0;

                document.getElementById('dash-legend-high').textContent = high;
                document.getElementById('dash-legend-med').textContent = med;
                document.getElementById('dash-legend-low').textContent = low;

                if (priorityDonutChart) {
                    priorityDonutChart.data.datasets[0].data = [high, med, low];
                    priorityDonutChart.update('none');
                }
            }

            // 2. Fetch topology device totals
            const resTopo = await fetch('/api/topology');
            const dataTopo = await resTopo.json();
            if (dataTopo.success && dataTopo.data) {
                const devs = dataTopo.data.devices;
                const onlineCount = devs.filter(d => d.status === 'ONLINE').length;
                document.getElementById('kpi-devices').textContent = `${onlineCount} / ${devs.length}`;
            }

            // 3. Fetch QoS Policy state
            const resQoS = await fetch('/api/qos/policies');
            const dataQoS = await resQoS.json();
            if (dataQoS.success && dataQoS.data) {
                const enabled = dataQoS.data.qos_enabled;
                const elKpi = document.getElementById('kpi-qos-state');
                const elNav = document.getElementById('nav-qos-status');
                if (elKpi) elKpi.textContent = enabled ? 'ACTIVE' : 'DISABLED';
                if (elNav) {
                    elNav.textContent = enabled ? 'ACTIVE' : 'DISABLED';
                    elNav.className = enabled ? 'badge badge-low' : 'badge badge-high';
                }
            }

            // 4. Fetch recent packets preview
            const resPackets = await fetch('/api/monitoring/packets?limit=7');
            const dataPackets = await resPackets.json();
            if (dataPackets.success && dataPackets.packets) {
                renderPacketsTable(dataPackets.packets);
            }

        } catch (err) {
            console.error('Dashboard update error:', err);
        }
    }

    function renderPacketsTable(packets) {
        const tbody = document.getElementById('dash-packets-tbody');
        if (!tbody) return;
        if (packets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No recent packets. Monitoring feed is waiting for traffic.</td></tr>`;
            return;
        }

        tbody.innerHTML = packets.map(p => {
            const prioBadge = p.priority === 'HIGH' ? 'badge-high' : p.priority === 'LOW' ? 'badge-low' : 'badge-med';
            const protoColor = p.protocol === 'UDP' ? '#00E5FF' : p.protocol === 'TCP' ? '#3A86FF' : '#FFB703';
            return `
                <tr>
                    <td class="text-muted" style="font-size:0.75rem;">${p.timestamp ? p.timestamp.split(' ')[1] : ''}</td>
                    <td><code>${p.src_ip}${p.src_port ? ':' + p.src_port : ''}</code></td>
                    <td><code>${p.dst_ip}${p.dst_port ? ':' + p.dst_port : ''}</code></td>
                    <td><span class="badge" style="background-color: ${protoColor}; color:#070B14; font-weight:700;">${p.protocol}</span></td>
                    <td>${p.length} B</td>
                    <td><span class="badge ${prioBadge}">${p.priority}</span></td>
                    <td class="text-white fw-semibold">${p.application || '-'}</td>
                    <td class="text-muted" style="font-size:0.75rem;">${p.info || ''}</td>
                </tr>
            `;
        }).join('');
    }

    // Polling timer
    updateDashboard();
    setInterval(updateDashboard, 1500);
});
