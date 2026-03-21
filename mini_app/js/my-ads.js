const tg = window.Telegram.WebApp;
tg.expand();

let user = null;
let myAds = [];

document.addEventListener('DOMContentLoaded', async () => {
    await initUser();
    await loadMyAds();
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

async function loadMyAds() {
    const listContainer = document.getElementById('myAdsList');
    listContainer.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        myAds = await api.ads.getUserAds(user.id);
        renderMyAds();
    } catch (error) {
        console.error('Error loading ads:', error);
        listContainer.innerHTML = '<div class="error">❌ Ошибка загрузки</div>';
    }
}

function renderMyAds() {
    const listContainer = document.getElementById('myAdsList');
    
    if (!myAds || myAds.length === 0) {
        listContainer.innerHTML = `
            <div class="no-ads">
                😕 У вас нет объявлений<br>
                <button class="create-btn" onclick="location.href='add-ad.html'">
                    ➕ Создать объявление
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    myAds.forEach(ad => {
        const price = formatPrice(ad.price);
        const statusClass = ad.is_active ? 'status-active' : 'status-inactive';
        const statusText = ad.is_active ? 'Активно' : 'Скрыто';
        const photo = ad.photos && ad.photos.length > 0 ? ad.photos[0] : 'assets/no-image.jpg';
        
        html += `
            <div class="my-ad-card" data-id="${ad.id}">
                <div class="my-ad-content">
                    <img src="${photo}" class="my-ad-image" alt="${ad.brand} ${ad.model}">
                    <div class="my-ad-info">
                        <div class="my-ad-title">${escapeHtml(ad.brand)} ${escapeHtml(ad.model)}</div>
                        <div class="my-ad-price">${price}</div>
                        <div class="my-ad-year">${ad.year} · ${formatMileage(ad.mileage)}</div>
                        <div class="my-ad-status ${statusClass}">${statusText}</div>
                    </div>
                </div>
                <div class="my-ad-actions">
                    <button class="edit-btn" data-id="${ad.id}">✏️ Редактировать</button>
                    <button class="delete-btn" data-id="${ad.id}">🗑 Удалить</button>
                </div>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
    
    // Добавляем обработчики кнопок
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const adId = btn.dataset.id;
            // Здесь можно открыть страницу редактирования
            tg.showPopup({
                title: 'Редактирование',
                message: 'Эта функция будет доступна в следующей версии',
                buttons: [{type: 'close'}]
            });
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const adId = parseInt(btn.dataset.id);
            
            tg.showPopup({
                title: 'Удаление',
                message: 'Вы уверены, что хотите удалить это объявление?',
                buttons: [
                    {id: 'confirm', text: '✅ Да, удалить'},
                    {id: 'cancel', type: 'cancel', text: '❌ Отмена'}
                ]
            }, async (buttonId) => {
                if (buttonId === 'confirm') {
                    await deleteAd(adId);
                }
            });
        });
    });
}

async function deleteAd(adId) {
    try {
        await api.ads.delete(adId);
        tg.showPopup({
            title: 'Успешно',
            message: 'Объявление удалено',
            buttons: [{type: 'close'}]
        });
        await loadMyAds();
    } catch (error) {
        console.error('Error deleting ad:', error);
        tg.showPopup({
            title: 'Ошибка',
            message: 'Не удалось удалить объявление',
            buttons: [{type: 'close'}]
        });
    }
}

function setupEventListeners() {
    document.getElementById('addBtn').addEventListener('click', () => {
        window.location.href = 'add-ad.html';
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