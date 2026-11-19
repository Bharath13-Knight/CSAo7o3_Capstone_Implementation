document.addEventListener('DOMContentLoaded', () => {
    let network = null;
    let topologyData = null;

    // Load and render topology
    async function loadTopology() {
        try {
            const res = await fetch('/api/topology');
            const data = await res.json();
            if (!data.success || !data.data) return;

            topologyData = data.data;

            // Update host environment info banner
            if (topologyData.host_environment) {
                const host = topologyData.host_environment;
                document.getElementById('topo-host-os').textContent = host.host_os || 'Host OS';
                document.getElementById('topo-host-ip').textContent = host.host_ip || '127.0.0.1';
            }

            renderNetworkGraph(topologyData);
            renderDevicesTable(topologyData.devices);

        } catch (err) {
            console.error('Topology loading error:', err);
        }
    }

    function renderNetworkGraph(data) {
        const container = document.getElementById('topology-canvas');
        if (!container) return;

        // Process Vis.js nodes styling
        const visNodes = data.nodes.map(n => {
            let font = { color: '#FFFFFF', size: 12, face: 'Segoe UI' };
            let size = 22;
            if (n.group === 'router') {
                size = 32;
                font = { color: '#00E5FF', size: 13, face: 'Segoe UI', bold: true };
            } else if (n.group === 'wan') {
                size = 28;
                font = { color: '#00E5FF', size: 12, face: 'Segoe UI' };
            } else if (n.group === 'switch') {
                size = 24;
            }
            return {
                id: n.id,
                label: n.label,
                shape: n.shape || 'dot',
                size: size,
                color: n.color,
                font: font,
                shadow: true,
                raw: n
            };
        });

        // Process Vis.js edges styling
        const visEdges = data.edges.map((e, idx) => ({
            id: `e-${idx}`,
            from: e.from,
            to: e.to,
            label: e.label || '',
            font: { color: '#8A99AD', size: 9, align: 'top' },
            color: { color: e.color || '#4895EF', highlight: '#00E5FF' },
            width: e.width || 2,
            dashes: e.dashes || false,
            smooth: { type: 'continuous' }
        }));

        const graphData = {
            nodes: new vis.DataSet(visNodes),
            edges: new vis.DataSet(visEdges)
        };

        const options = {
            physics: {
                stabilization: { iterations: 150 },
                barnesHut: {
                    gravitationalConstant: -3500,
                    centralGravity: 0.25,
                    springLength: 110,
                    springConstant: 0.04
                }
            },
            interaction: {
                hover: true,
                zoomView: true,
                dragView: true
            }
        };

        network = new vis.Network(container, graphData, options);

        // Click on node listener
        network.on('click', params => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const selected = visNodes.find(n => n.id === nodeId);
                if (selected && selected.raw) {
                    inspectNode(selected.raw);
                }
            }
        });
    }

    function inspectNode(node) {
        const inspector = document.getElementById('node-inspector-content');
        if (!inspector) return;

        let statusBadge = node.status === 'ONLINE' || node.status === 'UP' ? 
            '<span class="badge badge-online">ONLINE</span>' : '<span class="badge badge-offline">OFFLINE</span>';

        let html = `
            <div class="p-2 mb-2 rounded bg-dark border border-secondary">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong class="text-cyan">${node.label.replace('\\n', ' ')}</strong>
                    ${statusBadge}
                </div>
                <div class="text-muted" style="font-size:0.78rem;">Role: <span class="text-white">${node.type}</span></div>
                <div class="text-muted" style="font-size:0.78rem;">IP Address: <span class="text-white"><code>${node.ip || '-'}</code></span></div>
                <div class="text-muted" style="font-size:0.78rem;">MAC Address: <span class="text-white"><code>${node.mac || '-'}</code></span></div>
                <div class="text-muted" style="font-size:0.78rem;">Subnet: <span class="text-white">${node.subnet_id || 'Inter-Subnet Core'}</span></div>
            </div>
        `;

        if (node.interfaces) {
            html += `<h6 class="text-info mt-2" style="font-size:0.8rem;">Router Interface Table:</h6>`;
            html += `<ul class="list-unstyled mb-0" style="font-size:0.76rem;">`;
            node.interfaces.forEach(i => {
                html += `<li class="d-flex justify-content-between text-secondary py-1 border-bottom border-dark">
                    <span>${i.name} (${i.subnet})</span>
                    <code>${i.ip}</code>
                </li>`;
            });
            html += `</ul>`;
        }

        inspector.innerHTML = html;
    }

    function renderDevicesTable(devices) {
        const tbody = document.getElementById('topo-devices-tbody');
        if (!tbody || !devices) return;

        tbody.innerHTML = devices.map(d => {
            const isOnline = d.status === 'ONLINE';
            const badge = isOnline ? '<span class="badge badge-online">ONLINE</span>' : '<span class="badge badge-offline">OFFLINE</span>';
            const btnText = isOnline ? 'Set Offline' : 'Set Online';
            const btnClass = isOnline ? 'btn-outline-danger' : 'btn-outline-success';

            // Find gateway
            let gw = d.subnet_id === 'subnet-a' ? '192.168.1.1' : d.subnet_id === 'subnet-b' ? '192.168.2.1' : '192.168.3.1';
            let subnetLabel = d.subnet_id === 'subnet-a' ? 'Subnet A (192.168.1.0/24)' : d.subnet_id === 'subnet-b' ? 'Subnet B (192.168.2.0/24)' : 'Subnet C (192.168.3.0/24)';

            return `
                <tr>
                    <td class="fw-semibold text-white">${d.name}</td>
                    <td><span class="text-cyan">${subnetLabel}</span></td>
                    <td><code>${d.ip}</code></td>
                    <td><code class="text-muted">${d.mac}</code></td>
                    <td><code>${gw}</code></td>
                    <td>${d.type}</td>
                    <td>${badge}</td>
                    <td>
                        <button class="btn ${btnClass} btn-sm py-0 px-2 toggle-device-btn" data-id="${d.id}" data-status="${isOnline ? 'OFFLINE' : 'ONLINE'}" style="font-size:0.75rem;">
                            ${btnText}
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        // Attach toggle listeners
        document.querySelectorAll('.toggle-device-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const devId = e.target.getAttribute('data-id');
                const targetStatus = e.target.getAttribute('data-status');
                try {
                    const res = await fetch('/api/topology/device/toggle', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ device_id: devId, status: targetStatus })
                    });
                    const resData = await res.json();
                    if (resData.success) {
                        showToast(`Device ${devId} is now ${targetStatus}`, 'info');
                        loadTopology();
                    }
                } catch (err) {
                    showToast('Failed to toggle device: ' + err, 'error');
                }
            });
        });
    }

    // Ping Utility Listener
    document.getElementById('btn-run-ping')?.addEventListener('click', async () => {
        const srcIp = document.getElementById('ping-src-select').value;
        const dstIp = document.getElementById('ping-dst-select').value;
        const outBox = document.getElementById('ping-output-box');

        outBox.style.display = 'block';
        outBox.innerHTML = `<span class="text-muted">Pinging ${dstIp} from ${srcIp} across subnets...</span>`;

        try {
            const res = await fetch('/api/topology/ping', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ source_ip: srcIp, target_ip: dstIp, count: 4 })
            });
            const data = await res.json();
            if (!data.success || !data.result) {
                outBox.innerHTML = `<span class="text-danger">Ping failed to execute.</span>`;
                return;
            }

            const r = data.result;
            let logHtml = `<div class="text-cyan mb-1">=== ICMP DIAGNOSTIC PING RESULTS ===</div>`;
            logHtml += `<div>Source: <strong>${r.source}</strong> &rarr; Target: <strong>${r.target}</strong></div>`;
            logHtml += `<div class="text-muted mb-2">Routed via: ${r.hop_path.join(' &rarr; ')}</div>`;

            if (r.details) {
                r.details.forEach(p => {
                    if (p.rtt_ms !== null) {
                        logHtml += `<div>Reply from ${dstIp}: bytes=${p.bytes} time=${p.rtt_ms}ms TTL=${p.ttl}</div>`;
                    } else {
                        logHtml += `<div class="text-danger">${p.status}</div>`;
                    }
                });
            }

            logHtml += `<div class="mt-2 text-warning">--- Statistics ---</div>`;
            logHtml += `<div>Packets: Sent = ${r.packets_sent}, Received = ${r.packets_received}, Loss = ${r.packet_loss_pct}%</div>`;
            if (r.avg_rtt_ms) {
                logHtml += `<div>RTT: Min = ${r.min_rtt_ms}ms, Max = ${r.max_rtt_ms}ms, Avg = ${r.avg_rtt_ms}ms</div>`;
            }

            outBox.innerHTML = logHtml;

        } catch (err) {
            outBox.innerHTML = `<span class="text-danger">Ping exception: ${err}</span>`;
        }
    });

    // Recenter Graph Listener
    document.getElementById('btn-fit-topology')?.addEventListener('click', () => {
        if (network) network.fit({ animation: { duration: 600 } });
    });

    loadTopology();
});
