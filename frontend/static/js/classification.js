document.addEventListener('DOMContentLoaded', () => {
    let priorityChart = null;
    let protocolChart = null;

    function initCharts() {
        // Priority Ratio Doughnut Chart
        const ctxPrio = document.getElementById('clsPriorityChart')?.getContext('2d');
        if (ctxPrio) {
            priorityChart = new Chart(ctxPrio, {
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
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#CAD5E2', font: { size: 11 } }
                        }
                    }
                }
            });
        }

        // Protocol Breakdown Bar Chart
        const ctxProto = document.getElementById('clsProtocolChart')?.getContext('2d');
        if (ctxProto) {
            protocolChart = new Chart(ctxProto, {
                type: 'bar',
                data: {
                    labels: ['UDP', 'TCP', 'ICMP', 'DNS', 'HTTP'],
                    datasets: [{
                        label: 'Packet Count',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: ['#00E5FF', '#3A86FF', '#FFD166', '#A78BFA', '#F72585'],
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: { color: '#1B2A4A' },
                            ticks: { color: '#CAD5E2' }
                        },
                        y: {
                            beginAtZero: true,
                            grid: { color: '#1B2A4A' },
                            ticks: { color: '#CAD5E2' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }

    initCharts();

    // Fetch and render classification statistics
    async function loadStats() {
        try {
            const res = await fetch('/api/classification/stats');
            const data = await res.json();
            if (!data.success || !data.stats) return;

            const s = data.stats;
            document.getElementById('cls-high-count').textContent = s.high_priority_count.toLocaleString();
            document.getElementById('cls-med-count').textContent = s.medium_priority_count.toLocaleString();
            document.getElementById('cls-low-count').textContent = s.low_priority_count.toLocaleString();

            document.getElementById('cls-high-pct').textContent = `${s.high_priority_pct}%`;
            document.getElementById('cls-med-pct').textContent = `${s.medium_priority_pct}%`;
            document.getElementById('cls-low-pct').textContent = `${s.low_priority_pct}%`;

            // Update Doughnut Chart
            if (priorityChart) {
                priorityChart.data.datasets[0].data = [
                    s.high_priority_count,
                    s.medium_priority_count,
                    s.low_priority_count
                ];
                priorityChart.update('none');
            }

            // Update Protocol Bar Chart
            if (protocolChart && s.protocols) {
                const protos = s.protocols;
                protocolChart.data.datasets[0].data = [
                    protos.UDP || 0,
                    protos.TCP || 0,
                    protos.ICMP || 0,
                    protos.DNS || 0,
                    protos.HTTP || 0
                ];
                protocolChart.update('none');
            }

        } catch (err) {
            console.error('Classification stats error:', err);
        }
    }

    // Fetch and render classification rules table
    async function loadRules() {
        try {
            const res = await fetch('/api/classification/rules');
            const data = await res.json();
            if (!data.success || !data.rules) return;

            const tbody = document.getElementById('rules-tbody');
            if (!tbody) return;

            tbody.innerHTML = data.rules.map(r => {
                const prioBadge = r.priority === 'HIGH' ? 'badge-high' : r.priority === 'LOW' ? 'badge-low' : 'badge-med';
                const isActive = r.is_active === 1;

                return `
                    <tr>
                        <td class="text-muted" style="font-size:0.75rem;">#${r.id}</td>
                        <td class="fw-semibold text-white">${r.name}</td>
                        <td><span class="badge bg-dark border border-secondary">${r.protocol}</span></td>
                        <td><code>${r.port_range || 'ANY'}</code></td>
                        <td><span class="badge ${prioBadge}">${r.priority}</span></td>
                        <td class="text-cyan">${r.app_name}</td>
                        <td class="text-muted" style="font-size:0.78rem;">${r.description || '-'}</td>
                        <td>
                            <div class="form-check form-switch mb-0">
                                <input class="form-check-input rule-toggle" type="checkbox" data-id="${r.id}" ${isActive ? 'checked' : ''}>
                            </div>
                        </td>
                        <td>
                            <button class="btn btn-outline-danger btn-sm py-0 px-2 rule-delete-btn" data-id="${r.id}" style="font-size:0.75rem;">
                                Delete
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            // Rule Toggle Listeners
            document.querySelectorAll('.rule-toggle').forEach(sw => {
                sw.addEventListener('change', async (e) => {
                    const ruleId = e.target.getAttribute('data-id');
                    const activeVal = e.target.checked ? 1 : 0;
                    try {
                        await fetch(`/api/classification/rules/${ruleId}/toggle`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ is_active: activeVal })
                        });
                        showToast(`Rule #${ruleId} ${activeVal ? 'activated' : 'deactivated'}`, 'info');
                    } catch (err) {
                        showToast('Toggle failed: ' + err, 'error');
                    }
                });
            });

            // Rule Delete Listeners
            document.querySelectorAll('.rule-delete-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const ruleId = e.target.getAttribute('data-id');
                    if (!confirm(`Delete rule #${ruleId}?`)) return;
                    try {
                        await fetch(`/api/classification/rules/${ruleId}`, { method: 'DELETE' });
                        showToast(`Rule #${ruleId} deleted`, 'info');
                        loadRules();
                    } catch (err) {
                        showToast('Delete failed: ' + err, 'error');
                    }
                });
            });

        } catch (err) {
            console.error('Classification rules load error:', err);
        }
    }

    // Save Custom Rule Modal Listener
    document.getElementById('btn-save-rule')?.addEventListener('click', async () => {
        const name = document.getElementById('modal-rule-name').value.trim();
        const proto = document.getElementById('modal-rule-proto').value;
        const prio = document.getElementById('modal-rule-prio').value;
        const ports = document.getElementById('modal-rule-ports').value.trim();
        const app = document.getElementById('modal-rule-app').value.trim();
        const desc = document.getElementById('modal-rule-desc').value.trim();

        if (!name || !app) {
            alert('Rule Name and Application Label are required.');
            return;
        }

        try {
            const res = await fetch('/api/classification/rules', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    protocol: proto,
                    priority: prio,
                    port_range: ports,
                    app_name: app,
                    description: desc
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Rule "${name}" added successfully.`, 'success');
                // Dismiss modal
                const modalEl = document.getElementById('addRuleModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                // Reset form
                document.getElementById('form-add-rule').reset();
                loadRules();
                loadStats();
            }
        } catch (err) {
            showToast('Save rule failed: ' + err, 'error');
        }
    });

    loadStats();
    loadRules();
    setInterval(loadStats, 2000);
});
