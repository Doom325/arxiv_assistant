# arxiv_assistant — Chrome Extension

Browser extension for saving arXiv papers to the arxiv_assistant library directly from the browser.

## Stack

- **Manifest V3** Chrome extension
- Vanilla JavaScript (no build step)

## Structure

```
chrome_extension/
├── manifest.json     # Extension metadata & permissions
├── background.js     # Service worker
├── popup/            # Extension popup UI
├── scripts/          # Content scripts (page interaction)
└── icons/            # Extension icons
```

## How It Works

- Content scripts detect arXiv paper pages
- Popup UI lets users save papers to their library
- Communicates with the backend API to add papers via REST endpoints
