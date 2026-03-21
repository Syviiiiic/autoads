const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

let currentPage = 1;
let totalPages = 1;
let currentFilters = {};
let user = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initUser();
    await loadAds();
    await loadFilters();
    setupEventListeners();
});

async function initUser() {
    try {
        const verifyResult = await api.auth.verify(tg.initData);
        if (verifyResult.status === 'ok') {
            user = await api.auth.me();
            console.log('User:', user);
            
            // Устанавливаем тему Telegram
            tg.setHeaderColor('bg_color');
        }
    } catch (error) {
        console.error('Auth error:', error);
    }
}

async function loadAds() {
    const adsGrid = document.getElementById('adsGrid');
    adsGrid.innerHTML = '<div class="loading">Загрузка объявлений...</div>';
    
    try {
        const response = await api.ads.getAll({
            page: currentPage,
            limit: 10,
            ...currentFilters
        });
        
        renderAds(response.items || []);
        totalPages = response.pages || 1;
        updatePagination();
    } catch (error) {
        console.error('Error loading ads:', error);
        adsGrid.innerHTML = '<div class="error">❌ Ошибка загрузки. Попробуйте позже.</div>';
    }
}

function renderAds(ads) {
    const adsGrid = document.getElementById('adsGrid');
    
    if (!ads || ads.length === 0) {
        adsGrid.innerHTML = '<div class="no-ads">😕 Объявлений не найдено</div>';
        return;
    }
    
    let html = '';
    ads.forEach(ad => {
        const price = formatPrice(ad.price);
        const photo = ad.photos && ad.photos.length > 0 
            ? ad.photos[0]
            : 'assets/no-image.jpg';
        
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
                        <span>⚙️ ${ad.engine_type}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    adsGrid.innerHTML = html;
    
    document.querySelectorAll('.ad-card').forEach(card => {
        card.addEventListener('click', () => {
            window.location.href = `ad.html?id=${card.dataset.id}`;
        });
    });
}

async function loadFilters() {
    try {
        const filters = await api.search.getFilters();
        
        const brandSelect = document.getElementById('brandFilter');
        if (brandSelect && filters.brands) {
            brandSelect.innerHTML = '<option value="">Все марки</option>';
            filters.brands.forEach(brand => {
                brandSelect.innerHTML += `<option value="${escapeHtml(brand.name)}">${escapeHtml(brand.name)} (${brand.count})</option>`;
            });
        }
        
        // Устанавливаем диапазоны цен
        if (filters.price) {
            document.getElementById('priceMin').placeholder = `от ${formatPrice(filters.price.min)}`;
            document.getElementById('priceMax').placeholder = `до ${formatPrice(filters.price.max)}`;
        }
        
        if (filters.year) {
            document.getElementById('yearMin').placeholder = `от ${filters.year.min}`;
            document.getElementById('yearMax').placeholder = `до ${filters.year.max}`;
        }
        
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

function updatePagination() {
    const pageInfo = document.getElementById('pageInfo');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    pageInfo.textContent = `Страница ${currentPage} из ${totalPages}`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
}

function setupEventListeners() {
    // Поиск
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    searchBtn.addEventListener('click', () => {
        currentFilters.query = searchInput.value;
        currentPage = 1;
        loadAds();
    });
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentFilters.query = searchInput.value;
            currentPage = 1;
            loadAds();
        }
    });
    
    // Пагинация
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadAds();
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadAds();
        }
    });
    
    // Фильтры
    const toggleFilters = document.getElementById('toggleFilters');
    const filtersDiv = document.getElementById('filters');
    
    toggleFilters.addEventListener('click', () => {
        const isHidden = filtersDiv.style.display === 'none';
        filtersDiv.style.display = isHidden ? 'block' : 'none';
        toggleFilters.textContent = isHidden ? '🔼 Скрыть фильтры' : '🔽 Показать фильтры';
    });
    
    document.getElementById('applyFilters').addEventListener('click', () => {
        currentFilters = {
            brand: document.getElementById('brandFilter').value,
            model: document.getElementById('modelFilter').value,
            price_min: document.getElementById('priceMin').value,
            price_max: document.getElementById('priceMax').value,
            year_min: document.getElementById('yearMin').value,
            year_max: document.getElementById('yearMax').value
        };
        
        // Удаляем пустые фильтры
        Object.keys(currentFilters).forEach(key => {
            if (!currentFilters[key]) delete currentFilters[key];
        });
        
        currentPage = 1;
        loadAds();
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
            const pageUrl = pages[btn.dataset.page];
            if (pageUrl && window.location.pathname !== `/${pageUrl}`) {
                window.location.href = pageUrl;
            }
        });
    });
    
    // Меню
    document.getElementById('menuBtn').addEventListener('click', () => {
        tg.showPopup({
            title: 'Меню',
            message: 'Выберите действие:',
            buttons: [
                {id: 'my_ads', text: '📋 Мои объявления'},
                {id: 'favorites', text: '❤️ Избранное'},
                {id: 'help', text: '❓ Помощь'},
                {id: 'cancel', type: 'cancel', text: 'Закрыть'}
            ]
        }, (buttonId) => {
            if (buttonId && buttonId !== 'cancel') {
                window.location.href = buttonId === 'my_ads' ? 'my-ads.html' : buttonId + '.html';
            }
        });
    });
    
    // Профиль
    document.getElementById('profileBtn').addEventListener('click', () => {
        window.location.href = 'profile.html';
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}