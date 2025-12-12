// mapModule.js - Handles the Chu dynasty archaeological sites map functionality

const API_BASE_URL = '/api';

export async function initMap() {
    const slider = document.getElementById('timeSlider');
    const yearText = document.getElementById('yearText');

    // --- 1. 还原：地图基础设置（锁定范围、缩放限制） ---
    const chinaBounds = [[15.0, 73.0], [54.0, 135.0]]; // 锁定在中国区域

    const map = L.map('chuMap', {
        center: [31.5, 113.0], // 中心：湖北附近
        zoom: 6,
        minZoom: 5,            // 禁止缩得太小
        maxZoom: 11,
        maxBounds: chinaBounds,
        maxBoundsViscosity: 1.0, // 拖动出界后的回弹力度
        zoomControl: false,
        attributionControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    // 使用素雅底图
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd', maxZoom: 13
    }).addTo(map);

    let mapLayers = [];

    try {
        // 获取后端数据
        const response = await fetch(`${API_BASE_URL}/sites`);
        const data = await response.json();

        // 确保数据结构正确
        const centerData = data.center_point || { lat: 30.3, lng: 112.2, name: "郢都" };
        const sitesData = data.sites || [];

        // --- 2. 绘制中心点 (如：纪南城) ---
        const centerIcon = L.divIcon({
            className: 'center-marker',
            html: `<div style="width: 16px; height: 16px; background: #B83B28; border: 3px solid #fff; border-radius: 50%; box-shadow: 0 0 10px #B83B28;"></div>`,
            iconSize: [20, 20]
        });
        L.marker([centerData.latitude, centerData.longitude], { icon: centerIcon })
         .addTo(map)
         .bindPopup(`<div class="popup-title">${centerData.name}</div>${centerData.description}`);

        // --- 3. 绘制遗址点 (包含连线、圆点、文字标签) ---
        sitesData.forEach(site => {
            const layerGroup = L.layerGroup().addTo(map);

            // A. 虚线 (赭石色)
            const line = L.polyline([[centerData.latitude, centerData.longitude], [site.latitude, site.longitude]], {
                color: '#D4A017', weight: 1, opacity: 0.6, dashArray: '5, 5'
            }).addTo(layerGroup);

            // B. 遗址圆点 (靛蓝色)
            const marker = L.circleMarker([site.latitude, site.longitude], {
                radius: 6,
                fillColor: "#202A38", // 靛蓝
                color: "#fff",
                weight: 1,
                fillOpacity: 1
            }).addTo(layerGroup);

            // C. 还原：城市文字标签 (site.location)
            if (site.location) {
                const labelIcon = L.divIcon({
                    className: 'city-label',
                    html: site.location,  // 显示 "江陵"、"包山" 等
                    iconSize: [80, 20],
                    iconAnchor: [-8, 10] //稍微偏移，别挡住圆点
                });
                L.marker([site.latitude, site.longitude], { icon: labelIcon, interactive: false }).addTo(layerGroup);
            }

            // D. 弹窗与交互
            const popupHtml = `
                <div class="popup-title">${site.name}</div>
                <div style="font-size:0.9em; color:#666; margin-bottom:5px;"><b>年份:</b> 约前 ${Math.abs(site.year)} 年</div>
                <div style="font-size:0.9em; line-height:1.5;">${site.description}</div>
            `;
            marker.bindPopup(popupHtml);
            line.bindPopup(popupHtml);

            // 鼠标悬停高亮逻辑
            marker.on('mouseover', () => {
                marker.setStyle({ radius: 9, fillColor: '#B83B28' }); // 变红
                line.setStyle({ color: '#B83B28', weight: 2, dashArray: null }); // 变红实线
            });
            marker.on('mouseout', () => {
                marker.setStyle({ radius: 6, fillColor: '#202A38' }); // 恢复蓝
                line.setStyle({ color: '#D4A017', weight: 1, dashArray: '5, 5' }); // 恢复金虚线
            });

            mapLayers.push({ data: site, group: layerGroup });
        });

        // --- 4. 时间轴过滤逻辑 ---
        function updateMap() {
            const currentYear = parseInt(slider.value);
            const absYear = Math.abs(currentYear);

            // 根据年份显示不同时期名称
            let period = "";
            if (currentYear <= -403) period = "战国早期";
            else if (currentYear <= -323) period = "战国中期";
            else period = "战国晚期";

            yearText.innerText = `${period} (前${absYear})`;

            // 过滤显示
            mapLayers.forEach(item => {
                // 逻辑：如果遗址年份早于当前拖动条年份（考虑30年存续期），则显示
                if (item.data.year <= currentYear + 30) {
                    if (!map.hasLayer(item.group)) map.addLayer(item.group);
                } else {
                    if (map.hasLayer(item.group)) map.removeLayer(item.group);
                }
            });
        }

        slider.addEventListener('input', updateMap);
        updateMap(); // 初始化一次

    } catch (error) {
        console.error("地图数据加载失败", error);
        // 错误提示UI
        document.getElementById('chuMap').innerHTML =
            `<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#B83B28;">
                <p>⚠ 无法连接服务器获取地图数据</p>
             </div>`;
    }
}