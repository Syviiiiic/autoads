const API_BASE = '/api';

const api = {
    // Auth
    auth: {
        async verify(initData) {
            const response = await fetch(`${API_BASE}/auth/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ initData })
            });
            return response.json();
        },
        
        async me() {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        }
    },
    
    // Ads
    ads: {
        async getAll(params = {}) {
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`${API_BASE}/ads?${query}`, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        },
        
        async getById(id) {
            const response = await fetch(`${API_BASE}/ads/${id}`, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        },
        
        async create(adData) {
            const response = await fetch(`${API_BASE}/ads`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                },
                body: JSON.stringify(adData)
            });
            return response.json();
        },
        
        async update(id, adData) {
            const response = await fetch(`${API_BASE}/ads/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                },
                body: JSON.stringify(adData)
            });
            return response.json();
        },
        
        async delete(id) {
            const response = await fetch(`${API_BASE}/ads/${id}`, {
                method: 'DELETE',
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        },
        
        async getUserAds(userId) {
            const response = await fetch(`${API_BASE}/ads/user/${userId}`, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        }
    },
    
    // Favorites
    favorites: {
        async getAll() {
            const response = await fetch(`${API_BASE}/favorites`, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        },
        
        async add(adId) {
            const response = await fetch(`${API_BASE}/favorites`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                },
                body: JSON.stringify({ ad_id: adId })
            });
            return response.json();
        },
        
        async remove(adId) {
            const response = await fetch(`${API_BASE}/favorites/${adId}`, {
                method: 'DELETE',
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        }
    },
    
    // Search
    search: {
        async suggestions(query) {
            const response = await fetch(`${API_BASE}/search/suggestions?query=${encodeURIComponent(query)}`);
            return response.json();
        },
        
        async getFilters() {
            const response = await fetch(`${API_BASE}/search/filters`);
            return response.json();
        }
    },
    
    // User
    user: {
        async update(data) {
            const response = await fetch(`${API_BASE}/user`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                },
                body: JSON.stringify(data)
            });
            return response.json();
        },
        
        async getStats() {
            const response = await fetch(`${API_BASE}/user/stats`, {
                headers: {
                    'X-Telegram-Init-Data': window.Telegram.WebApp.initData
                }
            });
            return response.json();
        }
    }
};

// Helper function for formatting
function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU').format(price) + ' ₽';
}

function formatMileage(mileage) {
    return new Intl.NumberFormat('ru-RU').format(mileage) + ' км';
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('ru-RU');
}