const tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

let photos = [];
let user = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initUser();
    setupPhotoUpload();
    setupFormSubmit();
});

async function initUser() {
    try {
        const verifyResult = await api.auth.verify(tg.initData);
        if (verifyResult.status === 'ok') {
            user = await api.auth.me();
        }
    } catch (error) {
        console.error('Auth error:', error);
        tg.showPopup({
            title: 'Ошибка',
            message: 'Не удалось авторизоваться. Попробуйте позже.',
            buttons: [{type: 'close'}]
        });
    }
}

function setupPhotoUpload() {
    const uploadDiv = document.getElementById('photoUpload');
    const photoInput = document.getElementById('photoInput');
    const photoPreview = document.getElementById('photoPreview');
    
    uploadDiv.addEventListener('click', () => {
        photoInput.click();
    });
    
    photoInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        
        for (const file of files) {
            if (photos.length >= 10) {
                tg.showPopup({
                    title: 'Лимит фото',
                    message: 'Максимум 10 фотографий',
                    buttons: [{type: 'close'}]
                });
                break;
            }
            
            if (file.size > 10 * 1024 * 1024) {
                tg.showPopup({
                    title: 'Ошибка',
                    message: 'Файл слишком большой (макс. 10 МБ)',
                    buttons: [{type: 'close'}]
                });
                continue;
            }
            
            const reader = new FileReader();
            reader.onload = (event) => {
                photos.push({
                    file: file,
                    preview: event.target.result
                });
                renderPhotoPreview();
            };
            reader.readAsDataURL(file);
        }
        
        photoInput.value = '';
    });
}

function renderPhotoPreview() {
    const photoPreview = document.getElementById('photoPreview');
    
    if (photos.length === 0) {
        photoPreview.innerHTML = '';
        return;
    }
    
    let html = '';
    photos.forEach((photo, index) => {
        html += `
            <div style="position: relative; display: inline-block;">
                <img src="${photo.preview}" alt="Фото ${index + 1}">
                <div class="remove-photo" onclick="removePhoto(${index})">×</div>
            </div>
        `;
    });
    
    photoPreview.innerHTML = html;
}

function removePhoto(index) {
    photos.splice(index, 1);
    renderPhotoPreview();
}

async function uploadPhotoToServer(file) {
    // Здесь нужно реализовать загрузку фото на сервер
    // Пока возвращаем временный URL
    return URL.createObjectURL(file);
}

async function setupFormSubmit() {
    const form = document.getElementById('adForm');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!user) {
            tg.showPopup({
                title: 'Ошибка',
                message: 'Пожалуйста, авторизуйтесь',
                buttons: [{type: 'close'}]
            });
            return;
        }
        
        if (photos.length === 0) {
            tg.showPopup({
                title: 'Ошибка',
                message: 'Добавьте хотя бы одну фотографию',
                buttons: [{type: 'close'}]
            });
            return;
        }
        
        const formData = {
            brand: document.getElementById('brand').value.trim(),
            model: document.getElementById('model').value.trim(),
            year: parseInt(document.getElementById('year').value),
            price: parseInt(document.getElementById('price').value),
            mileage: parseInt(document.getElementById('mileage').value) || 0,
            engine_type: document.getElementById('engineType').value,
            engine_capacity: parseFloat(document.getElementById('engineCapacity').value) || 0,
            transmission: document.getElementById('transmission').value,
            drive: document.getElementById('drive').value,
            color: document.getElementById('color').value.trim(),
            description: document.getElementById('description').value.trim(),
            photos: [] // Здесь будут URL фото после загрузки
        };
        
        // Валидация
        if (!formData.brand || !formData.model || !formData.year || !formData.price) {
            tg.showPopup({
                title: 'Ошибка',
                message: 'Заполните все обязательные поля',
                buttons: [{type: 'close'}]
            });
            return;
        }
        
        if (formData.year < 1900 || formData.year > 2026) {
            tg.showPopup({
                title: 'Ошибка',
                message: 'Введите корректный год (1900-2026)',
                buttons: [{type: 'close'}]
            });
            return;
        }
        
        if (formData.price < 1000) {
            tg.showPopup({
                title: 'Ошибка',
                message: 'Минимальная цена - 1000 ₽',
                buttons: [{type: 'close'}]
            });
            return;
        }
        
        // Показываем индикатор загрузки
        tg.showPopup({
            title: 'Публикация',
            message: 'Загрузка фотографий...',
            buttons: [{type: 'close'}]
        });
        
        try {
            // Загружаем фото на сервер
            for (const photo of photos) {
                const photoUrl = await uploadPhotoToServer(photo.file);
                formData.photos.push(photoUrl);
            }
            
            const result = await api.ads.create(formData);
            
            if (result.id) {
                tg.showPopup({
                    title: 'Успешно!',
                    message: 'Объявление опубликовано',
                    buttons: [{id: 'view', text: 'Посмотреть'}]
                }, (buttonId) => {
                    if (buttonId === 'view') {
                        window.location.href = `ad.html?id=${result.id}`;
                    } else {
                        window.location.href = 'index.html';
                    }
                });
            } else {
                throw new Error('Failed to create ad');
            }
        } catch (error) {
            console.error('Error creating ad:', error);
            tg.showPopup({
                title: 'Ошибка',
                message: 'Не удалось опубликовать объявление. Попробуйте позже.',
                buttons: [{type: 'close'}]
            });
        }
    });
}

// Глобальная функция для удаления фото
window.removePhoto = removePhoto;