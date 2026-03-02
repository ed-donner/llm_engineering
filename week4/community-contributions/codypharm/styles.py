CSS = """
:root {
  --py-color: #209dd7;
  --cpp-color: #ecad0a;
  --accent:   #753991;
  --card:     #161a22;
  --text:     #e9eef5;
}

/* Full-width layout */
.gradio-container {
  max-width: 100% !important;
  padding: 0 40px !important;
}

/* Code card styling */
.card {
  background: var(--card);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 14px;
  padding: 10px;
}

/* Buttons */
.convert-btn button {
  background: var(--accent) !important;
  border-color: rgba(255,255,255,.12) !important;
  color: white !important;
  font-weight: 700;
}
.run-btn button {
  background: #202631 !important;
  color: var(--text) !important;
  border-color: rgba(255,255,255,.12) !important;
}
.run-btn.py button:hover  { box-shadow: 0 0 0 2px var(--py-color) inset; }
.run-btn.cpp button:hover { box-shadow: 0 0 0 2px var(--cpp-color) inset; }
.convert-btn button:hover { box-shadow: 0 0 0 2px var(--accent) inset; }

/* Outputs with color tint */
.py-out textarea {
  background: #000000;
  border: 1px solid rgba(32,157,215,.35) !important;
  color: rgba(32,157,215,1) !important;
  font-weight: 600;
  box-sizing: border-box;
  width: 100% !important;
  min-height: 100% !important;
}
/* Output card: no inner padding so the textarea fills the container */
.py-out.card {
  padding: 0 !important;
}
.py-out.card .wrap,
.py-out.card .form {
  height: 100%;
  min-height: 100%;
}
.py-out.card textarea {
  min-height: 100%;
}
/* Output column: scrollable when content overflows */
.py-out.card {
  max-height: 70vh;
  overflow-y: auto;
}
.cpp-out textarea {
  background: #000000;
  border: 1px solid rgba(236,173,10,.45) !important;
  color: rgba(236,173,10,1) !important;
  font-weight: 600;
}

/* Align controls neatly */
.controls .wrap {
  gap: 10px;
  justify-content: center;
  align-items: center;
}
"""
