let lastLogTime = "";
async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();

        const esp32Status = document.getElementById('esp32-status');
        esp32Status.innerText = data.esp32_status;
        esp32Status.className = data.esp32_status === 'Online'
            ? 'value online'
            : 'value offline';

        const doorStatus = document.getElementById('door-status');
        doorStatus.innerText = data.door_status;
        doorStatus.className = data.door_status === 'UNLOCKED'
            ? 'value unlocked'
            : 'value locked';

        const doorStatusText = document.getElementById('door-status-text');
        doorStatusText.innerText = data.door_status;
        doorStatusText.className = data.door_status === 'UNLOCKED'
            ? 'unlocked'
            : 'locked';

        document.getElementById('total-access').innerText = data.total_access;
        document.getElementById('total-granted').innerText = data.total_granted;
        document.getElementById('total-denied').innerText = data.total_denied;
        document.getElementById('last-face').innerText = data.last_face;
        document.getElementById('last-access-time').innerText = data.last_access_time;

        const lastFaceImg = document.getElementById("last-face-img");

        if (lastFaceImg) {
            lastFaceImg.src = "/static/last_face.jpg?t=" + new Date().getTime();
        }

        if (data.logs.length > 0) {
            if (lastLogTime !== "" && lastLogTime !== data.logs[0].time) {

                const toast = document.getElementById("toast");
                toast.innerText = "🔓 " + data.logs[0].action;
                toast.classList.add("show");

                setTimeout(() => {
                    toast.classList.remove("show");
                }, 3000);
            }

            lastLogTime = data.logs[0].time;
        }

        const table = document.getElementById('log-table');
        table.innerHTML = '';

        data.logs.forEach(log => {
            let statusClass = 'warning';

            if (log.status === 'Success' || log.status === 'Granted') {
                statusClass = 'success';
            } else if (log.status === 'Denied' || log.status === 'Failed') {
                statusClass = 'denied';
            }

            table.innerHTML += `
                <tr>
                    <td>${log.time}</td>
                    <td>${log.action}</td>
                    <td class="${statusClass}">${log.status}</td>
                </tr>
            `;
        });

    } catch (error) {
        console.log('Gagal load dashboard data:', error);
    }
}

loadLogs();
setInterval(loadLogs, 2000);