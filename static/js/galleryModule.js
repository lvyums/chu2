// galleryModule.js - Handles the artifact gallery functionality

const API_BASE_URL = 'http://127.0.0.1:5000/api';

export async function initGallery() {
    const container = document.getElementById('galleryContainer');
    try {
        const res = await fetch(`${API_BASE_URL}/artifacts`);
        const items = await res.json();

        container.innerHTML = '';
        items.forEach(item => {
            let imgSrc = item.img_url;

            // 1. 如果 JSON 里没有图片链接，使用占位图
            if (!imgSrc) {
                imgSrc = 'https://via.placeholder.com/300x200?text=No+Image';
            }
            // 2. 如果链接不是以 http 开头（说明是本地文件），也不是以 /static 开头
            //    则自动加上 /static/images/ 前缀
            else if (!imgSrc.startsWith('http') && !imgSrc.startsWith('/static/')) {
                imgSrc = `/static/images/${imgSrc}`;
            }
            const card = document.createElement('div');
            card.className = 'artifact-card';
            card.innerHTML = `
                <div class="img-box">
                    <img src="${item.img_url || 'placeholder.jpg'}" alt="${item.title}" onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
                </div>
                <div class="info-box">
                    <span class="tag">楚简</span>
                    <h3>${item.title}</h3>
                    <p>${item.desc}</p>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        container.innerHTML = `<p style="color:var(--chu-red); text-align:center;">数据加载失败</p>`;
    }
}