const tg = window.Telegram.WebApp;
tg.expand();

let user = null;
let stats = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initUser();
    await loadStats();
    renderProfile();
    setupEventListeners();
});

async function initUser() {
    try {
        const verifyResult = await api.auth.verify(tg.initData);
        if (verifyResult.status === 'ok') {
            user = await api.auth.me();
        }
    } catch (error) {
        console.error('Auth error:', error);
    }
}

async function loadStats() {
    try {
        stats = await api.user.getStats();
    } catch (error) {
        console.error('Error loading stats:', error);
        stats = { total_ads: 0, active_ads: 0, total_views: 0 };
    }
}

function renderProfile() {
    const container = document.getElementById('profileContainer');
    
    if (!user) {
        container.innerHTML = '<div class="error">Ошибка загрузки профиля</div>';
        return;
    }
    
    const initials = user.first_name ? user.first_name.charAt(0).toUpperCase() : 'U';
    
    const html = `
        <div class="profile-header">
            <div class="profile-avatar">${initials}</div>
            <div class="profile-name">${escapeHtml(user.first_name || '')} ${escapeHtml(user.last_name || '')}</div>
            <div class="profile-username">@${user.username || 'username'}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${stats.total_ads || 0}</div>
                <div class="stat-label">Объявлений</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.active_ads || 0}</div>
                <div class="stat-label">Активных</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.total_views || 0}</div>
                <div class="stat-label">Просмотров</div>
            </div>
        </div>
        
        <div class="profile-menu">
            <div class="menu-item" data-action="my_ads">
                <span>📋 Мои объявления</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="favorites">
                <span>❤️ Избранное</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="settings">
                <span>⚙️ Настройки</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="help">
                <span>❓ Помощь</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="contact">
                <span>📞 Связаться с поддержкой</span>
                <span>→</span>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function setupEventListeners() {
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;
            handleAction(action);
        });
    });
    
    // Навигация
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const pages = {
                catalog: 'index.html',
                add: 'add-ad.html',
                favorites: 'favorites.html',
                profile: 'profile.html'
            };
            window.location.href = pages[btn.dataset.page];
        });
    });
}

function handleAction(action) {
    switch (action) {
        case 'my_ads':
            window.location.href = 'my-ads.html';
            break;
        case 'favorites':
            window.location.href = 'favorites.html';
            break;
        case 'settings':
            tg.showPopup({
                title: 'Настройки',
                message: 'Настройки будут доступны в следующей версии',
                buttons: [{type: 'close'}]
            });
            break;
        case 'help':
            window.location.href = 'help.html';
            break;
        case 'contact':
            tg.openTelegramLink('https://t.me/autoads_support');
            break;
    }
}