document.addEventListener('DOMContentLoaded', () => {
    const sliderTotalBw = document.getElementById('slider-total-bw');
    const sliderHigh = document.getElementById('slider-high-pct');
    const sliderMed = document.getElementById('slider-med-pct');
    const sliderLow = document.getElementById('slider-low-pct');

    const lblTotalBw = document.getElementById('lbl-total-bw');
    const lblHighPct = document.getElementById('lbl-high-pct');
    const lblMedPct = document.getElementById('lbl-med-pct');
    const lblLowPct = document.getElementById('lbl-low-pct');

    const lblHighMbps = document.getElementById('lbl-high-mbps');
    const lblMedMbps = document.getElementById('lbl-med-mbps');
    const lblLowMbps = document.getElementById('lbl-low-mbps');

    const lblSum = document.getElementById('lbl-allocation-sum');
    const switchEnableQoS = document.getElementById('switch-enable-qos');

    // Update Slider Labels & Calculations
    function syncSliders() {
        const totalBw = parseFloat(sliderTotalBw.value);
        const high = parseFloat(sliderHigh.value);
        const med = parseFloat(sliderMed.value);
        const low = parseFloat(sliderLow.value);

        lblTotalBw.textContent = totalBw;
        lblHighPct.textContent = high;
        lblMedPct.textContent = med;
        lblLowPct.textContent = low;

        lblHighMbps.textContent = ((high / 100.0) * totalBw).toFixed(1);
        lblMedMbps.textContent = ((med / 100.0) * totalBw).toFixed(1);
        lblLowMbps.textContent = ((low / 100.0) * totalBw).toFixed(1);

        const sum = Math.round(high + med + low);
        lblSum.textContent = `${sum}%`;
        if (sum === 100) {
            lblSum.className = 'text-success fw-bold';
        } else {
            lblSum.className = 'text-danger fw-bold';
        }
    }

    [sliderTotalBw, sliderHigh, sliderMed, sliderLow].forEach(s => {
        s?.addEventListener('input', syncSliders);
    });

    // Fetch and populate QoS status
    async function loadQoSStatus() {
        try {
            const res = await fetch('/api/qos/policies');
            const data = await res.json();
            if (!data.success || !data.data) return;

            const d = data.data;

            // Global Toggle
            if (switchEnableQoS) {
                switchEnableQoS.checked = d.qos_enabled;
            }
            document.getElementById('qos-status-heading').textContent = d.qos_enabled ? 
                'Quality of Service: ENABLED' : 'Quality of Service: DISABLED';

            // Enforcement Badge
            const badge = document.getElementById('qos-enforcement-badge');
            if (d.kernel_enforced) {
                badge.textContent = 'KERNEL HARDWARE ENFORCED (Linux tc active)';
                badge.className = 'badge badge-online px-3 py-2';
            } else {
                badge.textContent = 'SIMULATION ENGINE (Linux tc Script Ready)';
                badge.className = 'badge badge-sim px-3 py-2';
            }

            // Sync policies into sliders if available
            if (d.policies && d.policies.length >= 3) {
                const polMap = {};
                d.policies.forEach(p => polMap[p.priority_level] = p);

                if (polMap.HIGH && polMap.MEDIUM && polMap.LOW) {
                    sliderHigh.value = polMap.HIGH.guaranteed_bandwidth_percent;
                    sliderMed.value = polMap.MEDIUM.guaranteed_bandwidth_percent;
                    sliderLow.value = polMap.LOW.guaranteed_bandwidth_percent;
                    sliderTotalBw.value = d.total_bandwidth_mbps;
                    syncSliders();
                }
            }

            // Update queue dynamics cards
            if (d.simulated_queues) {
                const q = d.simulated_queues;
                // High Queue
                document.getElementById('q1-status').textContent = q.HIGH.status;
                document.getElementById('q1-latency').textContent = `${q.HIGH.simulated_latency_ms} ms`;
                document.getElementById('q1-jitter').textContent = `${q.HIGH.simulated_jitter_ms} ms`;
                document.getElementById('q1-drop').textContent = `${q.HIGH.drop_rate_pct}%`;

                // Medium Queue
                document.getElementById('q2-status').textContent = q.MEDIUM.status;
                document.getElementById('q2-latency').textContent = `${q.MEDIUM.simulated_latency_ms} ms`;
                document.getElementById('q2-jitter').textContent = `${q.MEDIUM.simulated_jitter_ms} ms`;
                document.getElementById('q2-drop').textContent = `${q.MEDIUM.drop_rate_pct}%`;

                // Low Queue
                document.getElementById('q3-status').textContent = q.LOW.status;
                document.getElementById('q3-latency').textContent = `${q.LOW.simulated_latency_ms} ms`;
                document.getElementById('q3-jitter').textContent = `${q.LOW.simulated_jitter_ms} ms`;
                document.getElementById('q3-drop').textContent = `${q.LOW.drop_rate_pct}%`;
            }

        } catch (err) {
            console.error('QoS load error:', err);
        }
    }

    // Load Linux tc script preview
    async function loadTcScript() {
        try {
            const res = await fetch('/api/qos/tc-script');
            const data = await res.json();
            if (data.success && data.commands) {
                document.getElementById('tc-script-box').textContent = data.commands.join('\n');
            }
        } catch (err) {
            console.error('tc script load error:', err);
        }
    }

    // Apply Policies Button Listener
    document.getElementById('btn-apply-qos')?.addEventListener('click', async () => {
        const totalBw = parseFloat(sliderTotalBw.value);
        const high = parseFloat(sliderHigh.value);
        const med = parseFloat(sliderMed.value);
        const low = parseFloat(sliderLow.value);

        if (Math.round(high + med + low) !== 100) {
            alert('Allocated percentages must sum exactly to 100%!');
            return;
        }

        try {
            const res = await fetch('/api/qos/policies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    high_pct: high,
                    med_pct: med,
                    low_pct: low,
                    total_bandwidth_mbps: totalBw
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast('QoS Policies updated and recalculated successfully.', 'success');
                loadQoSStatus();
                loadTcScript();
            } else {
                showToast('Error: ' + data.error, 'error');
            }
        } catch (err) {
            showToast('Failed to apply QoS policy: ' + err, 'error');
        }
    });

    // Reset Defaults Listener
    document.getElementById('btn-reset-qos-defaults')?.addEventListener('click', () => {
        sliderTotalBw.value = 100;
        sliderHigh.value = 55;
        sliderMed.value = 30;
        sliderLow.value = 15;
        syncSliders();
        document.getElementById('btn-apply-qos').click();
    });

    // Toggle QoS Global Switch
    switchEnableQoS?.addEventListener('change', async (e) => {
        const enable = e.target.checked;
        try {
            const res = await fetch('/api/qos/toggle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ enable: enable })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`QoS has been ${enable ? 'ENABLED' : 'DISABLED'}.`, 'info');
                loadQoSStatus();
                loadTcScript();
            }
        } catch (err) {
            showToast('Toggle failed: ' + err, 'error');
        }
    });

    // Copy Script to Clipboard Listener
    document.getElementById('btn-copy-tc')?.addEventListener('click', () => {
        const text = document.getElementById('tc-script-box').textContent;
        navigator.clipboard.writeText(text).then(() => {
            showToast('Linux tc commands copied to clipboard!', 'success');
        });
    });

    syncSliders();
    loadQoSStatus();
    loadTcScript();
});
