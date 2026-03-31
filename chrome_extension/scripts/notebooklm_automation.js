// NotebookLM Automation Script

const SELECTORS = {
    NOTEBOOK_CARD: 'mat-card',
    ADD_SOURCE_BTN: 'button[aria-label="Add source"]',
    ADD_SOURCE_SIDEBAR_BTN: '.add-source-button',
    WEBSITES_OPTION: 'button.drop-zone-icon-button',
    URL_INPUT: 'textarea[aria-label="Enter URLs"]',
    INSERT_BTN: 'button.mat-primary',
};

const LOG_PREFIX = '[ArxivExt]';
let lastUrl = location.href;

function log(...args) {
    console.log(LOG_PREFIX, ...args);
}

// === Main Router & SPA Handler ===
(function init() {
    log('Script initialized.');

    // Run logic immediately
    handleNavigation();

    // Check for URL changes (SPA navigation)
    setInterval(() => {
        const currentUrl = location.href;
        if (currentUrl !== lastUrl) {
            log('URL changed to:', currentUrl);
            lastUrl = currentUrl;
            handleNavigation();
        }
    }, 1000);
})();

function handleNavigation() {
    const url = location.href;

    // 1. Dashboard Logic (including Auto Create)
    if (url === 'https://notebooklm.google.com/' || url.includes('/u/0/') || (!url.includes('/notebook/') && !url.includes('autoCreate'))) {

        // Check for Auto Create Trigger
        const params = new URLSearchParams(window.location.search);
        if (params.get('autoCreate') === 'true') {
            log('Mode: Auto Create Triggered');
            waitForElement('.create-new-action-button, button.create-new-button', 5000).then(btn => {
                log('Clicking Create New...');
                btn.click();
            }).catch(e => log('Create New button not found', e));
        } else {
            // Just scraping
            log('Mode: Dashboard Detect - Waiting for cards...');
            waitForElements(SELECTORS.NOTEBOOK_CARD, 5000).then(() => {
                scrapeDashboard();
            }).catch(() => log('No notebook cards found (timeout).'));
        }
    }

    // 2. Notebook Logic (including Pending Action Check)
    if (url.includes('/notebook/')) {
        log('Mode: Notebook Detect - Starting scraper...');
        scrapeCurrentNotebook();

        // Give the UI a moment to settle after navigation
        setTimeout(() => {
            checkPendingAction();
        }, 1500);
    }

    // 3. Add Source Automation (Legacy URL Param method)
    const params = new URLSearchParams(window.location.search);
    if (params.get('addSource') === 'true' && params.get('url')) {
        log('Mode: Automation Triggered via URL:', params.get('url'));
        automateAddSource(params.get('url'));
    }
}

async function checkPendingAction() {
    try {
        const data = await chrome.storage.local.get('pendingAction');
        if (data.pendingAction) {
            const action = data.pendingAction;
            // Check expiry (e.g. 5 minutes)
            if (Date.now() - action.timestamp > 5 * 60 * 1000) {
                log('Pending action expired');
                chrome.storage.local.remove('pendingAction');
                return;
            }

            if (action.type === 'ADD_SOURCE') {
                log('Found pending action: Add Source', action.url);

                // Clear it immediately to prevent loops
                await chrome.storage.local.remove('pendingAction');

                automateAddSource(action.url);
            }
        }
    } catch (e) {
        log('Error checking pending action:', e);
    }
}


// === Scraper Logic ===

function scrapeDashboard() {
    const cards = document.querySelectorAll(SELECTORS.NOTEBOOK_CARD);
    // log(`Found ${cards.length} cards.`);
    const notebooks = [];

    cards.forEach(card => {
        const link = card.querySelector('a');
        if (!link || !link.href.includes('/notebook/')) return;

        const match = link.href.match(/notebook\/([a-zA-Z0-9-]+)/);
        if (!match) return;
        const id = match[1];

        let title = "Untitled Notebook";
        const titleEl = card.querySelector('.title, .mat-mdc-card-title, h3, a');
        if (titleEl) {
            title = titleEl.textContent.trim();
        } else {
            title = card.textContent.trim().split('\n')[0];
        }

        if (title.toLowerCase().includes('new notebook') && !id) return;

        notebooks.push({ id, title });
    });

    if (notebooks.length > 0) {
        chrome.runtime.sendMessage({ action: 'NOTEBOOKS_SCRAPED', notebooks: notebooks });
    }
}

function scrapeCurrentNotebook() {
    waitForElement('.notebook-title, .title-input, header h1', 10000).then((titleEl) => {
        const match = window.location.href.match(/notebook\/([a-zA-Z0-9-]+)/);
        if (!match) return;
        const id = match[1];

        const title = titleEl.value || titleEl.textContent || document.title.split(' - ')[0];

        if (title) {
            const notebook = { id, title: title.trim() };
            // log('Scraped current notebook:', notebook);
            chrome.runtime.sendMessage({ action: 'CURRENT_NOTEBOOK_SCRAPED', notebook: notebook });
        }
    }).catch((e) => { });
}


// === Automation Logic ===
async function automateAddSource(targetUrl) {
    try {
        log('Starting Added Source Automation for:', targetUrl);

        // 1. Find Add Source Button
        log('Waiting for Add Source button...');
        const addBtn = await waitForElement(SELECTORS.ADD_SOURCE_BTN, 10000);
        addBtn.click();

        // 2. Find "Websites" Option
        log('Waiting for Websites option...');
        await delay(500);
        const buttons = await waitForElements(SELECTORS.WEBSITES_OPTION, 5000);
        const apiBtn = Array.from(buttons).find(b => b.textContent.includes('Websites') || b.textContent.includes('Website'));

        if (!apiBtn) throw new Error('Websites option not found');
        apiBtn.click();

        // 3. Find Input
        log('Waiting for URL input...');
        const input = await waitForElement(SELECTORS.URL_INPUT, 5000);
        input.focus();
        input.value = targetUrl;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));

        // 4. Submit
        log('Waiting for Insert button...');
        await delay(1000);
        const primaryBtns = await waitForElements(SELECTORS.INSERT_BTN, 5000);

        const insertBtn = Array.from(primaryBtns).find(b => {
            const txt = b.textContent.toLowerCase();
            return txt.includes('insert') || txt.includes('add') || txt.includes('submit');
        });

        if (insertBtn) {
            // log('Found insert button:', insertBtn.textContent);
            if (!insertBtn.disabled) {
                insertBtn.click();
                log('Success! URL submitted.');
            } else {
                log('Insert button is disabled.');
            }
        } else {
            log('Insert button not found.');
        }

    } catch (e) {
        console.error(LOG_PREFIX, 'Automation failed:', e);
        // Retry logic?
    }
}


// === Helpers ===
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function waitForElement(selector, timeout) {
    return new Promise((resolve, reject) => {
        const el = document.querySelector(selector);
        if (el) return resolve(el);

        const observer = new MutationObserver(() => {
            const el = document.querySelector(selector);
            if (el) {
                observer.disconnect();
                resolve(el);
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });

        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Timeout waiting for ${selector}`));
        }, timeout);
    });
}

function waitForElements(selector, timeout) {
    return new Promise((resolve, reject) => {
        if (document.querySelectorAll(selector).length > 0) return resolve(document.querySelectorAll(selector));

        const observer = new MutationObserver(() => {
            if (document.querySelectorAll(selector).length > 0) {
                observer.disconnect();
                resolve(document.querySelectorAll(selector));
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });

        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Timeout waiting for elements ${selector}`));
        }, timeout);
    });
}
