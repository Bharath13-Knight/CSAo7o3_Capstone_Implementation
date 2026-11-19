document.addEventListener('DOMContentLoaded', () => {
    async function loadReports() {
        try {
            // 1. Fetch CSV reports list
            const resReports = await fetch('/api/reports');
            const dataReports = await resReports.json();

            if (dataReports.success && dataReports.reports) {
                renderReportsTable(dataReports.reports);
                document.getElementById('rep-total-files').textContent = dataReports.reports.length;
            }

            // 2. Fetch summary & historical logs
            const resSummary = await fetch('/api/reports/summary');
            const dataSummary = await resSummary.json();

            if (dataSummary.success && dataSummary.summary) {
                const s = dataSummary.summary;
                if (s.recent_tests) {
                    renderHistoryTable(s.recent_tests);
                    document.getElementById('rep-total-tests').textContent = s.recent_tests.length;
                }
            }

        } catch (err) {
            console.error('Reports load error:', err);
        }
    }

    function renderReportsTable(reports) {
        const tbody = document.getElementById('reports-file-tbody');
        if (!tbody) return;

        if (reports.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No CSV reports generated yet. Go to Performance Analysis to execute a benchmark.</td></tr>`;
            return;
        }

        tbody.innerHTML = reports.map(r => {
            const dateStr = new Date(r.created_at * 1000).toLocaleString();
            return `
                <tr>
                    <td class="fw-semibold text-white">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-cyan me-1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                        ${r.filename}
                    </td>
                    <td>${r.size_kb} KB</td>
                    <td><span class="badge bg-dark border border-secondary">CSV Spreadsheet</span></td>
                    <td class="text-muted" style="font-size:0.8rem;">${dateStr}</td>
                    <td>
                        <a href="/api/reports/download/${r.filename}" class="btn btn-outline-cyan btn-sm py-0 px-2" style="font-size:0.75rem;">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                            Download CSV
                        </a>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function renderHistoryTable(tests) {
        const tbody = document.getElementById('reports-history-tbody');
        if (!tbody) return;

        if (tests.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center text-muted py-4">No historical tests found in SQLite database.</td></tr>`;
            return;
        }

        tbody.innerHTML = tests.map(t => {
            const isBefore = t.scenario === 'BEFORE_QOS';
            const scenBadge = isBefore ? '<span class="badge badge-high">BEFORE QoS</span>' : '<span class="badge badge-low">AFTER QoS</span>';

            return `
                <tr>
                    <td class="text-muted" style="font-size:0.75rem;">#${t.id}</td>
                    <td><code>${t.test_id}</code></td>
                    <td class="text-muted" style="font-size:0.75rem;">${t.timestamp}</td>
                    <td>${scenBadge}</td>
                    <td class="fw-semibold text-white">${t.traffic_type}</td>
                    <td>${t.throughput_mbps} Mbps</td>
                    <td class="${isBefore ? 'text-danger' : 'text-success fw-bold'}">${t.latency_ms} ms</td>
                    <td class="${isBefore ? 'text-warning' : 'text-success'}">${t.packet_loss_percent}%</td>
                    <td>${t.jitter_ms} ms</td>
                    <td class="text-muted" style="font-size:0.75rem;">${t.notes || ''}</td>
                </tr>
            `;
        }).join('');
    }

    document.getElementById('btn-refresh-reports')?.addEventListener('click', loadReports);

    loadReports();
});
