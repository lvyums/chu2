/**
 * 楚韵 - 文字挑战逻辑库
 * 数据源：quiz_questions.json
 */

const DATA_URL = '/quiz_questions.json';

const game = {
    fullLibrary: [],      // 存放从 JSON 读取的完整题库
    currentQuestions: [], // 当前局抽取的5题
    currentIdx: 0,
    score: 0,
    isAnswering: false,

    // 初始化：自动从 JSON 文件加载数据
    init: async function() {
        try {
            console.log('正在加载题库...');
            const response = await fetch(DATA_URL);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.fullLibrary = await response.json();
            console.log(`题库加载成功，共 ${this.fullLibrary.length} 题`);

            // 可选：更新 UI 提示用户准备就绪（如果有加载文字的话）

        } catch (e) {
            console.error("题库加载失败:", e);
            const ui = this.getUI();
            // 在开始界面显示错误提示
            if(ui.startScreen) {
                ui.startScreen.innerHTML += `<p style="color:#B83B28; margin-top:10px;">⚠️ 题库数据加载失败，请检查 quiz_questions.json 文件位置。</p>`;
            }
        }
    },

    // 获取 DOM 元素
    getUI: function() {
        return {
            startScreen: document.getElementById('start-screen'),
            gameScreen: document.getElementById('game-screen'),
            endScreen: document.getElementById('end-screen'),

            questionVisual: document.getElementById('question-visual'),
            questionText: document.getElementById('question-text'),
            optionsContainer: document.getElementById('options-container'),

            currentNum: document.getElementById('current-num'),
            explanationText: document.getElementById('explanation-text'),
            nextBtn: document.getElementById('next-btn'),

            finalScore: document.getElementById('final-score'),
            finalMessage: document.getElementById('final-message')
        };
    },

    // 1. 开始游戏
    start: function() {
        // 检查数据是否已加载
        if (!this.fullLibrary || this.fullLibrary.length === 0) {
            alert("题库数据正在加载或加载失败，请刷新页面重试！");
            // 尝试重新加载
            this.init();
            return;
        }

        // 随机打乱完整题库，取前5个
        const shuffled = [...this.fullLibrary].sort(() => 0.5 - Math.random());
        this.currentQuestions = shuffled.slice(0, 5);

        this.currentIdx = 0;
        this.score = 0;

        const ui = this.getUI();
        ui.startScreen.classList.add('hidden');
        ui.endScreen.classList.add('hidden');
        ui.gameScreen.classList.remove('hidden');

        this.loadQuestion();
    },

    // 2. 加载题目
    loadQuestion: function() {
        const data = this.currentQuestions[this.currentIdx];
        const ui = this.getUI();
        this.isAnswering = true;

        // 更新进度
        ui.currentNum.innerText = this.currentIdx + 1;

        // 重置反馈区
        ui.nextBtn.classList.add('hidden');
        ui.explanationText.innerHTML = '';
        ui.optionsContainer.innerHTML = '';

        // 设置题目
        ui.questionVisual.innerText = data.visual;
        ui.questionText.innerText = data.question;

        // 生成选项
        data.options.forEach((opt, index) => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerText = opt;
            btn.onclick = () => this.checkAnswer(index, btn);
            ui.optionsContainer.appendChild(btn);
        });
    },

    // 3. 检查答案
    checkAnswer: function(selectedIndex, btnElement) {
        if (!this.isAnswering) return;
        this.isAnswering = false;

        const data = this.currentQuestions[this.currentIdx];
        const isCorrect = selectedIndex === data.answer;
        const ui = this.getUI();
        const buttons = ui.optionsContainer.children;

        // 样式反馈
        if (isCorrect) {
            btnElement.classList.add('correct');
            this.score++;
            ui.explanationText.innerHTML = `<span style="color:#4CAF50; font-weight:bold;">🎉 正确！</span> ${data.explanation}`;
        } else {
            btnElement.classList.add('wrong');
            buttons[data.answer].classList.add('correct');
            ui.explanationText.innerHTML = `<span style="color:#B83B28; font-weight:bold;">❌ 错误！</span> ${data.explanation}`;
        }

        Array.from(buttons).forEach(btn => btn.disabled = true);

        // 显示下一题按钮
        ui.nextBtn.classList.remove('hidden');
        ui.nextBtn.innerText = (this.currentIdx === 4) ? "查看结果" : "下一题";
    },

    // 4. 下一题
    next: function() {
        if (this.currentIdx < 4) {
            this.currentIdx++;
            this.loadQuestion();
        } else {
            this.endGame();
        }
    },

    // 5. 游戏结束
    endGame: function() {
        const ui = this.getUI();
        ui.gameScreen.classList.add('hidden');
        ui.endScreen.classList.remove('hidden');

        ui.finalScore.innerText = this.score;

        let msg = "";
        if (this.score === 5) msg = "🏆 楚学宗师！屈原都要为你点赞！";
        else if (this.score >= 3) msg = "📜 学识渊博，离精通楚文化只差一点点。";
        else if (this.score >= 1) msg = "🕯️ 继续努力，建议去【资料库】多看看哦。";
        else msg = "🍂 即使失败也是一种经历，再试一次吧！";

        ui.finalMessage.innerText = msg;
    }
};

// ==================== 启动与挂载 ====================

// 1. 自动执行初始化，加载 JSON 数据
game.init();

// 2. 将 game 对象挂载到 window，确保 HTML onclick 能访问到它
window.game = game;