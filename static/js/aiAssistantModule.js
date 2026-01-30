// AI助手模块 - 统一管理悬浮球链接
const AI_ASSISTANT_URL = 'http://8.162.10.98:8501/';
const STORAGE_KEY = 'ai_float_ball_pos';

// 初始化AI助手悬浮球
export function initAiAssistant() {
    const floatBall = document.querySelector('.ai-float-ball');
    if (floatBall) {
        // 初始化位置（从本地存储读取）
        const savedPos = JSON.parse(localStorage.getItem(STORAGE_KEY));
        if (savedPos) {
            floatBall.style.transform = `translate(${savedPos.x}px, ${savedPos.y}px)`;
        }

        // 处理点击跳转逻辑（配合拖动拦截）
        floatBall.addEventListener('click', (e) => {
            // 如果元素上有 'data-dragging' 标记，说明刚才在拖动，阻止跳转
            if (floatBall.dataset.dragging === 'true') {
                e.preventDefault();
                // 消费掉这个标记
                floatBall.dataset.dragging = 'false';
            } else {
                // 正常点击，跳转
                window.location.href = AI_ASSISTANT_URL;
            }
        });

        // 初始化拖动逻辑
        initDraggable(floatBall);
    }
}

// 拖动功能 - 长按进入拖动模式，松开停止
function initDraggable(element) {
    let isLongPress = false;   // 是否触发了长按
    let isDragActive = false;  // 是否正在进行拖拽操作

    let startX = 0, startY = 0;
    let initialTranslateX = 0, initialTranslateY = 0;
    let currentTranslateX = 0, currentTranslateY = 0;

    let pressTimer = null;
    const LONG_PRESS_DURATION = 300;

    // 获取当前的 transform 值
    function getCurrentTranslate() {
        const style = window.getComputedStyle(element);
        const matrix = new WebKitCSSMatrix(style.transform);
        return { x: matrix.m41, y: matrix.m42 };
    }

    // 长按触发
    pressTimer = setTimeout(() => {
        isLongPress = true;
        isDragActive = true;

        // 视觉反馈：设置标记，CSS会处理样式
        element.dataset.dragging = 'true';

        // 关键：JS 只负责移动，不负责 scale 了，scale 交给 CSS 的 .ai-ball-inner
        element.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px)`;
    }, LONG_PRESS_DURATION);

    // 移动中
    function onMove(e) {
        if (!isDragActive) return;
        if (e.cancelable) e.preventDefault();

        // ...计算位置 deltaX, deltaY...

        currentTranslateX = initialTranslateX + deltaX;
        currentTranslateY = initialTranslateY + deltaY;

        // 关键：只更新位置
        element.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px)`;
    }

    // --- 结束按压 ---
    function onEnd(e) {
        // 清理定时器
        if (pressTimer) {
            clearTimeout(pressTimer);
            pressTimer = null;
        }

        // 移除全局监听
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('mouseup', onEnd);
        document.removeEventListener('touchend', onEnd);

        // 恢复样式
        element.style.cursor = 'pointer';
        element.style.transition = 'transform 0.3s ease, opacity 0.3s ease'; // 恢复动画
        element.style.opacity = '1';

        if (isDragActive) {
            // 如果确实发生了拖动
            element.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px) scale(1)`;

            // 标记为已拖动，通知 click 事件不要跳转
            element.dataset.dragging = 'true';

            // 保存位置到本地存储
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                x: currentTranslateX,
                y: currentTranslateY
            }));
        } else {
            // 如果没触发长按（且没移动），说明是点击
            // click 事件会随后触发，dataset.dragging 为 false，允许跳转
        }

        isDragActive = false;
    }

    // 绑定开始事件
    element.addEventListener('mousedown', startPress);
    element.addEventListener('touchstart', startPress, { passive: true }); // passive: true 允许页面滚动直到长按触发
}