// Background Service Worker
console.log('[ArxivBG] Service Worker Initialized');

// Listen for messages from Popup or Content Scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[ArxivBG] Received message:', message.action, message);

    if (message.action === 'ADD_SOURCE_TO_NOTEBOOK') {
        handleAddSource(message.notebookId, message.url, message.paperTitle);
        sendResponse({ status: 'started' });
    }

    if (message.action === 'NOTEBOOKS_SCRAPED') {
        console.log('[ArxivBG] Received scraped notebooks:', message.notebooks.length);
        updateNotebooks(message.notebooks);
    }

    if (message.action === 'CURRENT_NOTEBOOK_SCRAPED') {
        console.log('[ArxivBG] Received single notebook update:', message.notebook);
        updateNotebooks([message.notebook]);
    }
});

function updateNotebooks(newNotebooks) {
    chrome.storage.local.get(['notebooks'], (result) => {
        const existing = result.notebooks || [];
        console.log('[ArxivBG] Existing notebooks in storage:', existing.length);

        const notebookMap = new Map();

        // Populate map with existing
        existing.forEach(nb => notebookMap.set(nb.id, nb));

        // Merge new
        newNotebooks.forEach(nb => {
            if (!notebookMap.has(nb.id)) console.log('[ArxivBG] New notebook found:', nb.title);
            notebookMap.set(nb.id, nb);
        });

        // Convert back to array
        const params = { notebooks: Array.from(notebookMap.values()), lastScraped: Date.now() };
        console.log('[ArxivBG] Saving updated list to storage. Total:', params.notebooks.length);
        chrome.storage.local.set(params);
    });
}

async function handleAddSource(notebookId, paperUrl, paperTitle) {
    if (notebookId === 'NEW_NOTEBOOK') {
        console.log('[ArxivBG] initiating new notebook creation flow');
        // Store the action to be picked up after creation/redirect
        await chrome.storage.local.set({
            pendingAction: {
                type: 'ADD_SOURCE',
                url: paperUrl,
                title: paperTitle,
                timestamp: Date.now()
            }
        });
        // Open dashboard with autoCreate trigger
        const dashboardUrl = 'https://notebooklm.google.com/?autoCreate=true';
        await chrome.tabs.create({ url: dashboardUrl, active: true });

    } else {
        // Existing flow
        const notebookUrl = `https://notebooklm.google.com/notebook/${notebookId}?addSource=true&url=${encodeURIComponent(paperUrl)}`;
        console.log('[ArxivBG] Opening NotebookLM tab:', notebookUrl);
        const tab = await chrome.tabs.create({ url: notebookUrl, active: true });
    }
}
