function addNodeRow() {
    const container = document.getElementById('nodes-container');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'node-row';
    row.style = 'display: flex; gap: 10px; margin-bottom: 10px; align-items: center;';
    row.innerHTML = `
        <input type="text" name="node_id[]" placeholder="Node ID (e.g. !0123abcd)" required>
        <input type="text" name="node_device_id[]" placeholder="Device ID (e.g. ICP-Heltec)" required>
        <input type="text" name="node_group[]" placeholder="Specific Group (Optional)">
        <button type="button" onclick="this.parentElement.remove()" style="background: #dc3545; color: white; border: none; cursor: pointer; padding: 10px; border-radius: 4px;">Remove</button>
    `;
    container.appendChild(row);
}

function restartService() {
    if (!confirm("Are you sure you want to restart the background service? This will disconnect momentarily.")) return;
    
    // We can extract csrf token from the meta tag on all pages
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (!csrfMeta) return;
    const csrfToken = csrfMeta.getAttribute('content');
    
    fetch('/api/restart', { 
        method: 'POST',
        headers: { 'X-CSRF-Token': csrfToken }
    })
    .then(response => response.json())
    .then(data => {
        alert("Service is restarting. The page will reload in 5 seconds.");
        setTimeout(() => window.location.reload(), 5000);
    })
    .catch(err => alert("Failed to trigger restart."));
}

let refreshIntervalId = null;

function updateRefreshInterval() {
    const autoRefreshEl = document.getElementById('autoRefresh');
    if (!autoRefreshEl) return;
    
    if (refreshIntervalId) {
        clearInterval(refreshIntervalId);
        refreshIntervalId = null;
    }

    const interval = parseInt(autoRefreshEl.value);
    if (interval > 0) {
        refreshIntervalId = setInterval(fetchLogs, interval);
    }
}

function fetchLogs() {
    fetch('/api/logs')
        .then(response => response.text())
        .then(data => {
            const logsBoxEl = document.getElementById('logsBox');
            if (!logsBoxEl) return;

            // Only autoscroll if user was already at the bottom (or very close)
            const isAtBottom = logsBoxEl.scrollHeight - logsBoxEl.scrollTop <= logsBoxEl.clientHeight + 20;

            logsBoxEl.innerText = data;

            if (isAtBottom) {
                logsBoxEl.scrollTop = logsBoxEl.scrollHeight;
            }
        })
        .catch(err => console.error("Failed to fetch logs.", err));
}

// Initialization that runs on page load
document.addEventListener("DOMContentLoaded", function() {
    const logsBox = document.getElementById('logsBox');
    if (logsBox) {
        logsBox.scrollTop = logsBox.scrollHeight;
        updateRefreshInterval();
    }
    
    const successMsg = document.getElementById('successMsg');
    if (successMsg) {
        setTimeout(() => {
            successMsg.innerText = "Refresh applied.";
        }, 3000);
    }
});
