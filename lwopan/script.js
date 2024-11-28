document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.overlay');
    const searchInput = document.querySelector('.search-input');
    const searchResults = document.querySelector('.search-results');
    const logoImage = document.querySelector('.logo img');
    const logoTitle = document.querySelector('.logo h1');
    let isMenuOpen = false;

    // 添加新的樣式
    const style = document.createElement('style');
    style.textContent = `
        .no-results, .search-result-item {
            opacity: 0;
            transform: translateY(-20px);
            transition: opacity 0.3s ease, transform 0.3s ease;
        }
        .no-results.show, .search-result-item.show {
            opacity: 1;
            transform: translateY(0);
        }
        .no-results {
            text-align: center;
            color: #888;
            margin-top: 20px;
        }
        .context-menu-disabled {
            position: fixed;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 9999;
        }
        .context-menu-disabled.show {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);

    // 添加防複製提示元素
    const contextMenuDisabled = document.createElement('div');
    contextMenuDisabled.className = 'context-menu-disabled';
    contextMenuDisabled.textContent = '禁止複製內容';
    document.body.appendChild(contextMenuDisabled);

    function showCopyProtectionMessage(x, y) {
        contextMenuDisabled.style.left = x + 'px';
        contextMenuDisabled.style.top = y + 'px';
        contextMenuDisabled.classList.add('show');

        setTimeout(() => {
            contextMenuDisabled.classList.remove('show');
        }, 1000);
    }

    function setupCopyProtection(resultElement) {
        resultElement.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            showCopyProtectionMessage(e.pageX, e.pageY);
        });

        resultElement.addEventListener('copy', (e) => {
            e.preventDefault();
            showCopyProtectionMessage(e.pageX, e.pageY);
        });

        resultElement.addEventListener('selectstart', (e) => {
            e.preventDefault();
        });

        resultElement.addEventListener('dragstart', (e) => {
            e.preventDefault();
        });
    }

    function toggleMenu() {
        isMenuOpen = !isMenuOpen;
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
        document.body.style.overflow = isMenuOpen ? 'hidden' : 'auto';
    }

    menuToggle.addEventListener('click', toggleMenu);
    overlay.addEventListener('click', toggleMenu);

    // Logo 點擊事件
    [logoImage, logoTitle].forEach(element => {
        if (element) {
            element.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/';
            });
        }
    });

    // 側邊欄鏈接點擊事件
    const sidebarLinks = document.querySelectorAll('.sidebar ul li a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.getAttribute('href') === '/404') {
                e.preventDefault();
                window.location.href = '/404';
            }
        });
    });

    // 檢測注音的函數
    function containsZhuyin(text) {
        const zhuyinRegex = /[ㄅ-ㄦ]/;
        return zhuyinRegex.test(text);
    }

    async function searchQuestions(query) {
        if (containsZhuyin(query)) {
            return [];
        }

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: query }),
            });

            if (!response.ok) {
                throw new Error('搜索請求失敗');
            }

            const data = await response.json();
            return data.result;
        } catch (error) {
            console.error('搜索出錯：', error);
            return [];
        }
    }

    function retractResults() {
        return new Promise(resolve => {
            const existingResults = searchResults.querySelectorAll('.search-result-item, .no-results');
            if (existingResults.length === 0) {
                resolve();
                return;
            }
            existingResults.forEach(element => {
                element.classList.remove('show');
            });
            setTimeout(resolve, 300);
        });
    }

    async function displayResults(results) {
        await retractResults();
        searchResults.innerHTML = '';
        if (results.length === 0 || (results.length === 1 && results[0].answer === "找不到相關題目，請檢查是否有錯字")) {
            const noResultsElement = document.createElement('p');
            noResultsElement.className = 'no-results';
            noResultsElement.textContent = '沒有找到相關題目';
            searchResults.appendChild(noResultsElement);
            setTimeout(() => noResultsElement.classList.add('show'), 50);
            return;
        }
        results.forEach((result, index) => {
            if (result.answer !== "找不到相關題目，請檢查是否有錯字") {
                const resultElement = document.createElement('div');
                resultElement.classList.add('search-result-item');
                resultElement.innerHTML = `
                    <div class="question">${result.question}</div>
                    <div class="arrow"></div>
                    <div class="answer">${result.answer}</div>
                `;
                searchResults.appendChild(resultElement);

                const arrow = resultElement.querySelector('.arrow');
                const answer = resultElement.querySelector('.answer');

                let arrowTimer;

                arrow.addEventListener('mouseenter', () => {
                    arrowTimer = setTimeout(() => {
                        arrow.classList.add('up');
                        answer.classList.add('show');
                    }, 200);
                });

                arrow.addEventListener('mouseleave', () => {
                    clearTimeout(arrowTimer);
                    arrow.classList.remove('up');
                    answer.classList.remove('show');
                });

                arrow.addEventListener('click', (e) => {
                    e.stopPropagation();
                    arrow.classList.toggle('up');
                    answer.classList.toggle('show');
                });

                // 添加複製保護
                setupCopyProtection(resultElement);

                // 添加動畫效果
                setTimeout(() => {
                    resultElement.classList.add('show');
                }, 50 * index);
            }
        });
    }

    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(async () => {
            const query = e.target.value.trim();
            if (query.length > 0) {
                if (!containsZhuyin(query)) {
                    const results = await searchQuestions(query);
                    displayResults(results);
                } else {
                    searchResults.innerHTML = '';
                }
            } else {
                retractResults().then(() => {
                    searchResults.innerHTML = '';
                });
            }
        }, 300);
    });

    // 全域防止複製事件
    document.addEventListener('keydown', (e) => {
        if (e.target.closest('.search-result-item')) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'C')) {
                e.preventDefault();
                showCopyProtectionMessage(e.pageX, e.pageY);
            }
        }
    });

    // 初始化函數
    function initializeResults() {
        const existingResults = searchResults.querySelectorAll('.search-result-item, .no-results');
        existingResults.forEach(element => {
            element.classList.remove('show');
        });
        setTimeout(() => {
            existingResults.forEach((element, index) => {
                setTimeout(() => {
                    element.classList.add('show');
                }, 50 * index);
            });
        }, 0);
    }

    // 頁面加載時初始化結果
    initializeResults();
});