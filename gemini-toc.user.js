// ==UserScript==
// @name         Gemini Chat Table of Contents (v3.0 Glass)
// @namespace    http://tampermonkey.net/
// @version      3.0
// @description  Gemini 消息目录：自动刷新、精简显示、毛玻璃悬浮UI
// @author       You
// @match        https://gemini.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // ================= 配置区域 =================
    const USER_MSG_SELECTOR = 'user-query-content, .user-query-content, [data-test-id="user-query"]';
    const MAX_CHARS = 50; // 限制字符数
    // ===========================================

    // 1. 注入优化后的 CSS (支持毛玻璃和新布局)
    const style = document.createElement('style');
    style.textContent = `
        /* 侧边悬浮面板 */
        #gemini-toc-sidebar {
            position: fixed;
            top: 50%;             /* 垂直居中 */
            right: -340px;        /* 默认隐藏位置 */
            transform: translateY(-50%); /* 修正垂直居中偏移 */
            width: 300px;
            height: 50vh;         /* 占据视窗高度的 50% */

            /* 背景透明度 30% (即0.7不透明) + 毛玻璃特效 */
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);

            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 9999;
            transition: right 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            display: flex;
            flex-direction: column;
            border-radius: 16px 0 0 16px; /* 左侧圆角 */
            border: 1px solid rgba(255, 255, 255, 0.5);
            font-family: 'Google Sans', sans-serif;
        }

        /* 打开状态 */
        #gemini-toc-sidebar.open {
            right: 0;
        }

        /* 顶部标题栏 */
        .toc-header {
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.5); /* 标题栏稍微深一点 */
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 16px 0 0 0;
        }
        .toc-title { font-weight: 600; color: #333; font-size: 14px; }
        .toc-close { cursor: pointer; font-size: 20px; color: #5f6368; padding: 0 5px; opacity: 0.7;}
        .toc-close:hover { opacity: 1; }

        /* 列表区域 */
        #toc-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            /* 隐藏滚动条但保留功能 */
            scrollbar-width: thin;
        }

        /* 列表项 */
        .toc-item {
            padding: 8px 12px;
            margin-bottom: 6px;
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            color: #3c4043;
            transition: all 0.2s;
            line-height: 1.5;
        }
        .toc-item:hover {
            background: #fff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transform: translateX(-2px); /* 悬停时微微左移 */
            color: #1a73e8;
        }

        /* 悬浮开关按钮 */
        #toc-toggle-btn {
            position: fixed;
            top: 50%;
            right: 0;
            transform: translateY(-50%);
            width: 36px;
            height: 36px;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(4px);
            color: #5f6368;
            border: 1px solid rgba(0,0,0,0.1);
            border-right: none;
            border-radius: 12px 0 0 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 10000;
            box-shadow: -2px 2px 8px rgba(0,0,0,0.1);
            font-size: 18px;
            transition: right 0.3s;
        }
        /* 当侧边栏打开时，隐藏按钮 */
        #gemini-toc-sidebar.open + #toc-toggle-btn, /* 这里只是为了逻辑，实际通过JS隐藏 */
        body.toc-open #toc-toggle-btn {
            right: -50px;
        }

        /* 暗黑模式适配 */
        @media (prefers-color-scheme: dark) {
            #gemini-toc-sidebar {
                background: rgba(30, 30, 30, 0.7);
                border-color: rgba(255,255,255,0.1);
            }
            .toc-header { background: rgba(255, 255, 255, 0.05); border-bottom-color: rgba(255,255,255,0.1); }
            .toc-title { color: #e8eaed; }
            .toc-close { color: #9aa0a6; }
            .toc-item { background: rgba(255, 255, 255, 0.05); color: #bdc1c6; }
            .toc-item:hover { background: rgba(255, 255, 255, 0.1); color: #8ab4f8; }
            #toc-toggle-btn {
                background: rgba(30,30,30,0.8);
                color: #e8eaed;
                border-color: rgba(255,255,255,0.1);
            }
        }
    `;
    document.head.appendChild(style);

    // 2. 创建 UI (TrustedHTML 安全版)
    function createUI() {
        const toggleBtn = document.createElement('div');
        toggleBtn.id = 'toc-toggle-btn';
        toggleBtn.textContent = '☰';
        toggleBtn.title = "消息列表";
        toggleBtn.onclick = toggleSidebar;
        document.body.appendChild(toggleBtn);

        const sidebar = document.createElement('div');
        sidebar.id = 'gemini-toc-sidebar';

        const header = document.createElement('div');
        header.className = 'toc-header';

        const title = document.createElement('span');
        title.className = 'toc-title';
        title.textContent = '对话导航';

        const closeBtn = document.createElement('span');
        closeBtn.className = 'toc-close';
        closeBtn.textContent = '✕';
        closeBtn.onclick = toggleSidebar;

        header.appendChild(title);
        header.appendChild(closeBtn);

        const listContainer = document.createElement('div');
        listContainer.id = 'toc-list';

        sidebar.appendChild(header);
        sidebar.appendChild(listContainer);
        document.body.appendChild(sidebar);
    }

    function toggleSidebar() {
        const sidebar = document.getElementById('gemini-toc-sidebar');
        const btn = document.getElementById('toc-toggle-btn');
        const isOpen = sidebar.classList.contains('open');

        if (!isOpen) {
            sidebar.classList.add('open');
            btn.style.right = '-50px'; // 隐藏按钮
            refreshList();
        } else {
            sidebar.classList.remove('open');
            btn.style.right = '0'; // 恢复按钮
        }
    }

    // 3. 核心：刷新逻辑（含截断和清空）
    function refreshList() {
        const listContainer = document.getElementById('toc-list');
        // 安全清空
        while (listContainer.firstChild) {
            listContainer.removeChild(listContainer.firstChild);
        }

        const msgs = Array.from(document.querySelectorAll(USER_MSG_SELECTOR));

        if (msgs.length === 0) {
            // 如果没找到消息，可能是页面还没渲染完，稍等重试一次（针对自动跳转）
            // 但为了不无限循环，这里显示空状态即可
            const empty = document.createElement('div');
            empty.textContent = '暂无消息或加载中...';
            empty.style.padding = '15px';
            empty.style.color = '#999';
            empty.style.textAlign = 'center';
            empty.style.fontSize = '12px';
            listContainer.appendChild(empty);
            return;
        }

        msgs.forEach((msg, index) => {
            let fullText = msg.innerText.trim().replace(/\s+/g, ' '); // 去除多余换行

            // 需求：50字符 + 省略号
            let displayText = fullText;
            if (displayText.length > MAX_CHARS) {
                displayText = displayText.substring(0, MAX_CHARS) + '...';
            }

            const item = document.createElement('div');
            item.className = 'toc-item';
            item.textContent = `${index + 1}. ${displayText}`;
            item.title = fullText; // 鼠标悬停显示完整内容

            item.onclick = () => {
                msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // 高亮动画
                const originalBg = msg.style.backgroundColor;
                const originalTrans = msg.style.transition;
                msg.style.transition = 'background-color 0.5s';
                msg.style.backgroundColor = 'rgba(255, 235, 59, 0.3)';
                setTimeout(() => {
                    msg.style.backgroundColor = originalBg;
                    msg.style.transition = originalTrans;
                }, 1500);
            };

            listContainer.appendChild(item);
        });
    }

    // 4. 自动刷新逻辑 (解决切换对话不刷新问题)
    let lastUrl = location.href;

    // 定时检查 URL 变化 (UserScript 中最稳健的方法)
    setInterval(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            // URL 变了，说明切换了对话
            // Gemini 加载内容需要时间，延迟 1.5 秒再刷新列表，确保 DOM 已渲染
            setTimeout(() => {
                const sidebar = document.getElementById('gemini-toc-sidebar');
                if (sidebar && sidebar.classList.contains('open')) {
                    refreshList();
                }
            }, 1500);
        }
    }, 1000);

    // 启动
    setTimeout(createUI, 1500);

})();
