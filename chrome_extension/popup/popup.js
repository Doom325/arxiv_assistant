// Popup Logic

const ui = {
    title: document.getElementById('paper-title'),
    url: document.getElementById('paper-url'),
    select: document.getElementById('notebook-select'),
    addBtn: document.getElementById('add-btn'),
    syncLink: document.getElementById('sync-link'),
    status: document.getElementById('status')
};

let currentPaper = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('[ArxivPopup] Popup opened');

    // 1. Get Current Tab Info
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        console.log('[ArxivPopup] Current tab:', tab.url, tab.title);

        if (isArxivPage(tab.url)) {
            console.log('[ArxivPopup] Detected Arxiv page');

            // Rewrite URL if on local app
            let paperUrl = tab.url;
            if (paperUrl.includes('/paper/')) {
                // Local App URL: http://.../paper/2103.00020
                const match = paperUrl.match(/paper\/([0-9.]+)(v[0-9]+)?/);
                if (match) {
                    paperUrl = `https://arxiv.org/abs/${match[1]}`;
                    console.log('[ArxivPopup] Rewrote local URL to:', paperUrl);
                }
            }

            currentPaper = {
                title: tab.title.replace(' [arXiv:.*]', ''), // Simple cleanup
                url: paperUrl
            };

            ui.title.textContent = currentPaper.title;
            ui.url.textContent = currentPaper.url;
            ui.addBtn.disabled = false; // Will enable if notebook selected
        } else {
            console.log('[ArxivPopup] Not an Arxiv page');
            ui.title.textContent = "Not an Arxiv Paper";
            ui.url.textContent = "Please visit arxiv.org or Arxiv Assistant";
            ui.addBtn.disabled = true;
        }
    } catch (e) {
        console.error('[ArxivPopup] Error querying tabs:', e);
        ui.status.textContent = "Error reading tab info";
    }

    // 2. Load Notebooks
    loadNotebooks();

    // 3. Handlers
    ui.syncLink.addEventListener('click', () => {
        chrome.tabs.create({ url: 'https://notebooklm.google.com/' });
    });

    ui.addBtn.addEventListener('click', () => {
        const notebookId = ui.select.value;
        if (!notebookId || !currentPaper) return;

        chrome.runtime.sendMessage({
            action: 'ADD_SOURCE_TO_NOTEBOOK',
            notebookId: notebookId,
            url: currentPaper.url,
            paperTitle: currentPaper.title
        });

        ui.status.textContent = "Opening NotebookLM...";
        setTimeout(() => window.close(), 1500);
    });

    ui.select.addEventListener('change', () => {
        if (ui.select.value && currentPaper) {
            ui.addBtn.disabled = false;
        }
    });
});

function isArxivPage(url) {
    return url.includes('arxiv.org') || url.includes('/paper/');
}

async function loadNotebooks() {
    console.log('[ArxivPopup] Loading notebooks from storage...');
    const data = await chrome.storage.local.get(['notebooks', 'lastScraped']);
    const notebooks = data.notebooks || [];
    console.log('[ArxivPopup] Found notebooks:', notebooks.length);

    // Clear existing
    ui.select.innerHTML = '<option value="" disabled selected>Select a notebook...</option>';

    // Add "Create New" Option
    const createOpt = document.createElement('option');
    createOpt.value = "NEW_NOTEBOOK";
    createOpt.text = "➕ Create New Notebook";
    ui.select.add(createOpt);

    if (notebooks.length === 0) {
        const opt = document.createElement('option');
        opt.text = "No existing notebooks found";
        opt.disabled = true;
        ui.select.add(opt);
    }

    // Sort by recent? (Assuming scraper order is recent)
    notebooks.forEach(nb => {
        const opt = document.createElement('option');
        opt.value = nb.id;
        opt.text = nb.title;
        ui.select.add(opt);
    });
}
