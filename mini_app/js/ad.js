const tg = window.Telegram.WebApp;
tg.expand();

let ad = null;
let currentPhotoIndex = 0;

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const adId = urlParams.get('id');
    
    if (!adId) {
        showError('ID объявления не указан');
        return;
    }
    
    await loadAd(adId);
    setupEventListeners();
});

async function loadAd(adId) {
    const adDetail = document.getElementById('adDetail');
    adDetail.innerHTML = '<div class="loading">Загрузка объявления...</div>';
    
    try {
        ad = await api.ads.getById(adId);
        renderAd();
    } catch (error) {
        console.error('Error loading ad:', error);
        adDetail.innerHTML = '<div class="error">❌ Ошибка загрузки объявления</div>';
    }
}

function renderAd() {
    const adDetail = document.getElementById('adDetail');
    const price = formatPrice(ad.price);
    const mileage = formatMileage(ad.mileage);
    const date = formatDate(ad.created_at);
    
    let photosHtml = '';
    if (ad.photos && ad.photos.length > 0) {
        photosHtml = `
            <div class="ad-gallery" id="gallery">
                ${ad.photos.map((photo, index) => `
                    <img src="${photo}" alt="Фото ${index + 1}" 
                         onclick="showFullscreen(${index})"
                         style="cursor: pointer;">
                `).join('')}
            </div>
        `;
    } else {
        photosHtml = '<div class="no-photo">📷 Нет фотографий</div>';
    }
    
    const html = `
        ${photosHtml}
        
        <div class="ad-detail-info">
            <div class="detail-row">
                <span class="detail-label">💰 Цена</span>
                <span class="detail-value">${price}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">📅 Год выпуска</span>
                <span class="detail-value">${ad.year}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">📊 Пробег</span>
                <span class="detail-value">${mileage}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">⚙️ Двигатель</span>
                <span class="detail-value">${ad.engine_capacity}л ${ad.engine_type}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">🔄 Коробка передач</span>
                <span class="detail-value">${ad.transmission}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">🔧 Привод</span>
                <span class="detail-value">${ad.drive}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">🎨 Цвет</span>
                <span class="detail-value">${ad.color || 'Не указан'}</span>
            </div>
            ${ad.description ? `
                <div class="description-text">
                    <strong>📝 Описание:</strong><br>
                    ${escapeHtml(ad.description)}
                </div>
            ` : ''}
            <div class="detail-row">
                <span class="detail-label">👁 Просмотров</span>
                <span class="detail-value">${ad.views_count}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">📅 Размещено</span>
                <span class="detail-value">${date}</span>
            </div>
        </div>
        
        <div class="seller-info">
            <div class="detail-row">
                <span class="detail-label">👤 Продавец</span>
                <span class="detail-value">@${ad.owner.username || ad.owner.first_name || 'Не указан'}</span>
            </div>
        </div>
    `;
    
    adDetail.innerHTML = html;
    
    // Обновляем заголовок
    document.title = `${ad.brand} ${ad.model} - Auto Ads`;
}

function setupEventListeners() {
    document.getElementById('contactBtn').addEventListener('click', () => {
        if (ad && ad.owner) {
            const username = ad.owner.username;
            if (username) {
                tg.openTelegramLink(`https://t.me/${username}`);
            } else {
                tg.showPopup({
                    title: 'Нет контакта',
                    message: 'У продавца не указан Telegram username',
                    buttons: [{type: 'close'}]
                });
            }
        }
    });
}

function showFullscreen(index) {
    if (!ad.photos || !ad.photos[index]) return;
    
    currentPhotoIndex = index;
    tg.showPopup({
        title: 'Фото',
        message: 'Просмотр фото',
        buttons: [
            {id: 'prev', text: '◀️ Предыдущее'},
            {id: 'next', text: 'Следующее ▶️'},
            {id: 'close', type: 'cancel', text: 'Закрыть'}
        ]
    }, (buttonId) => {
        if (buttonId === 'prev' && currentPhotoIndex > 0) {
            currentPhotoIndex--;
            showFullscreen(currentPhotoIndex);
        } else if (buttonId === 'next' && currentPhotoIndex < ad.photos.length - 1) {
            currentPhotoIndex++;
            showFullscreen(currentPhotoIndex);
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}