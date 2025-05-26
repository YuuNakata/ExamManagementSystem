document.addEventListener('DOMContentLoaded', () => {
    const badge   = document.getElementById('notif-badge');
    const panel   = document.getElementById('notif-panel');
    const list    = document.getElementById('notif-list');
    const toggle  = document.getElementById('notif-toggle');


    const urls = window.Notification;
    async function updateCount() {
    const resp = await fetch(urls.count);
    const { count } = await resp.json();
    if (count > 0) {
    badge.textContent = count;
    badge.style.display = 'inline-block';
    } else {
    badge.style.display = 'none';
    }
}

async function loadNotifications() {
    const resp = await fetch(urls.list);
    const { notifications } = await resp.json();
    list.innerHTML = '';
    notifications.forEach(n => {
    const li = document.createElement('li');
    li.style.padding = '8px';
    li.style.borderBottom = '1px solid #eee';
    if (n.is_read) li.style.opacity = '0.6';
    li.innerHTML = `
        <div>${n.message}</div>
        <small style="color:#666;">${n.timestamp}</small>
    `;
    li.addEventListener('click', async () => {
        if (!n.is_read) {
        await fetch(urls.read.replace('/0/', `/${n.id}/`));
        li.style.opacity = '0.6';
        updateCount();
        }
    });
    list.appendChild(li);
    });
}

toggle.addEventListener('click', async () => {
    if (panel.style.display === 'none') {
    panel.style.display = 'block';
    await loadNotifications();
    } else {
    panel.style.display = 'none';
    }
});

updateCount();
setInterval(updateCount, 15000);
});
