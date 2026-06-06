CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

.marimo-app, .mo-markdown, .mo-hstack, .mo-vstack, body {
    font-family: 'Outfit', sans-serif !important;
}

.marimo-callout {
    border-radius: 16px !important;
    border: 1px solid rgba(240, 246, 252, 0.08) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15) !important;
    backdrop-filter: blur(6px) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.marimo-callout.kind-success {
    background: rgba(46, 160, 67, 0.08) !important;
    border: 1px solid rgba(46, 160, 67, 0.2) !important;
}

.marimo-callout.kind-danger {
    background: rgba(248, 81, 73, 0.08) !important;
    border: 1px solid rgba(248, 81, 73, 0.2) !important;
}

.marimo-callout.kind-info {
    background: rgba(56, 139, 253, 0.08) !important;
    border: 1px solid rgba(56, 139, 253, 0.2) !important;
}

button {
    font-family: 'Outfit', sans-serif !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button:hover:not(:disabled) {
    transform: translateY(-1.5px) !important;
    box-shadow: 0 4px 15px rgba(56, 139, 253, 0.3) !important;
}

button:active:not(:disabled) {
    transform: scale(0.96) !important;
    opacity: 0.85 !important;
    box-shadow: none !important;
}

textarea {
    font-family: 'Outfit', sans-serif !important;
    border-radius: 10px !important;
    border: 1px solid rgba(240, 246, 252, 0.15) !important;
    background: rgba(22, 27, 34, 0.5) !important;
    color: #e6edf3 !important;
    transition: border-color 0.2s ease !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    resize: vertical !important;
}

/* Marimo renders text_area as a <marimo-text-area> custom element */
marimo-text-area {
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
}

/* Target every wrapper layer Marimo places around the textarea */
div:has(textarea),
div:has(> textarea),
div:has(> div > textarea),
div:has(marimo-text-area) {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

textarea:focus {
    border-color: #58a6ff !important;
}

div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 12px !important;
    max-width: 100% !important;
}

div[role="radiogroup"] label {
    display: flex !important;
    align-items: flex-start !important;
    gap: 10px !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    max-width: 100% !important;
    line-height: 1.4 !important;
    cursor: pointer !important;
}

div[style*="position: fixed"] button {
    background: #f85149 !important;
    color: white !important;
    border: none !important;
}

div[style*="position: fixed"] button:hover:not(:disabled) {
    background: #da3633 !important;
    box-shadow: 0 4px 15px rgba(248, 81, 73, 0.4) !important;
    transform: translateY(-1.5px) !important;
}
</style>
"""
