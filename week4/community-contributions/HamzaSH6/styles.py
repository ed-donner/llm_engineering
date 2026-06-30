CSS = """
:root {
    --bg: #0a0a0a;
    --panel: #111111;
    --panel-hover: #161616;
    --border: #232323;
    --text: #fafafa;
    --muted: #a1a1aa;

    --accent: #7c3aed;
    --python: #38bdf8;
}

html, body {
    background: var(--bg);
    color: var(--text);
}

.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    padding: 24px 32px !important;
    margin: 0 !important;
}

label {
    color: var(--text) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all .2s ease !important;
    min-height: 44px;
}

.optimize-btn button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
}

.optimize-btn button:hover {
    opacity: .9;
}

.run-btn button {
    background: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}

.run-btn button:hover {
    background: var(--panel-hover) !important;
}

.controls {
    margin: 20px 0;
}

.controls .wrap {
    gap: 12px !important;
}

textarea {
    border-radius: 14px !important;
}

.python-output textarea {
    background: #07141d !important;
    border: 1px solid rgba(56,189,248,.25) !important;
    color: #7dd3fc !important;
}

.optimized-python-output textarea {
    background: #0a1510 !important;
    border: 1px solid rgba(74,222,128,.20) !important;
    color: #86efac !important;
}

.markdown {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
}

.cm-editor {
    border-radius: 14px !important;
}

.cm-theme {
    background: #0f0f0f !important;
}

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #2a2a2a;
    border-radius: 999px;
}

* {
    transition:
        border-color .15s ease,
        background-color .15s ease;
}

.evaluation-box {
    background: #111111;
    border: 1px solid #232323;
    border-radius: 16px;
    padding: 18px;
    min-height: 180px;
}

.evaluation-box p, .evaluation-box li, .evaluation-box h1, .evaluation-box h2, .evaluation-box h3 {
    color: #fafafa !important;
}

.evaluation-box code {
    background: #1a1a1a;
    padding: 2px 6px;
    border-radius: 6px;
}

.dropdowns {
    background-color: transparent !important;
    padding: 0 !important;
}
"""