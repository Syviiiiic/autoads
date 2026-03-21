const tg = window.Telegram.WebApp;
tg.expand();

let favorites = [];

document.addEventListener('DOMContentLoaded', async () => {
    await initUser();
    await loadFavorites();
    setupEventListeners();
});

async function initUser() {
    try {
        const verifyResult = await api.auth.verify(tg.initData);
    } catch (error) {
        console.error('Auth error:', error);
    }
}

async function loadFavorites() {
    const listContainer = document.getElementById('favoritesList');
    listContainer.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        favorites = await api.favorites.getAll();
        renderFavorites();
    } catch (error) {
        console.error('Error loading favorites:', error);
        listContainer.innerHTML = '<div class="error">❌ Ошибка загрузки</div>';
    }
}

function renderFavorites() {
    const listContainer = document.getElementById('favoritesList');
    
    if (!favorites || favorites.length === 0) {
        listContainer.innerHTML = `
            <div class="no-ads">
                ❤️ У вас нет избранных объявлений<br>
                <button class="browse-btn" onclick="location.href='index.html'">
                    🔍 Посмотреть каталог
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    favorites.forEach(ad => {
        const price = formatPrice(ad.price);
        const photo = ad.photos && ad.photos.length > 0 ? ad.photos[0] : 'assets/no-image.jpg';
        
        html += `
            <div class="ad-card" data-id="${ad.id}">
                <img src="${photo}" alt="${ad.brand} ${ad.model}" 
                     onerror="this.src='assets/no-image.jpg'">
                <div class="ad-info">
                    <h3>${escapeHtml(ad.brand)} ${escapeHtml(ad.model)}</h3>
                    <div class="ad-year">${ad.year} · ${formatMileage(ad.mileage)}</div>
                    <div class="ad-price">${price}</div>
                    <div class="ad-meta">
                        <span>👁 ${ad.views_count}</span>
                        <button class="remove-favorite" data-id="${ad.id}">❤️ Удалить</button>
                    </div>
                </div>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
    
    document.querySelectorAll('.ad-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('remove-favorite')) {
                window.location.href = `ad.html?id=${card.dataset.id}`;
            }
        });
    });
    
    document.querySelectorAll('.remove-favorite').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const adId = parseInt(btn.dataset.id);
            await removeFavorite(adId);
        });
    });
}

async function removeFavorite(adId) {
    try {
        await api.favorites.remove(adId);
        await loadFavorites();
        tg.showPopup({
            title: 'Удалено',
            message: 'Объявление удалено из избранного',
            buttons: [{type: 'close'}]
        });
    } catch (error) {
        console.error('Error removing favorite:', error);
        tg.showPopup({
            title: 'Ошибка',
            message: 'Не удалось удалить',
            buttons: [{type: 'close'}]
        });
    }
}

function setupEventListeners() {
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