# ui/popup.py
# ── Stealth mode: invisible to Zoom/QuickTime/OBS screen capture ──
# ── All-Spaces mode: visible across every macOS Space/fullscreen app ──

import tkinter as tk
from queue import Queue, Empty

text_queue  = Queue()
chunk_queue = Queue()

_root     = None
_text_box = None
STREAM_DONE = object()


def _apply_window_behaviors():
    global _root
    try:
        from AppKit import (
            NSApplication,
            NSWindowSharingNone,
            NSWindowSharingReadOnly,
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorIgnoresCycle,
            NSFloatingWindowLevel,
            NSApplicationActivationPolicyAccessory, 
        )

        ns_app = NSApplication.sharedApplication()

        # ── Set AFTER tkinter is fully initialised ───────────────
        ns_app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        behavior = (
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | NSWindowCollectionBehaviorIgnoresCycle
        )

        windows = ns_app.windows()
        if not windows:
            print("[WINDOW] No windows found yet, retrying in 500ms...")
            if _root and _root.winfo_exists():
                _root.after(500, _apply_window_behaviors)
            return

        applied = 0
        for ns_win in windows:
            ns_win.setSharingType_(NSWindowSharingReadOnly)
            ns_win.setCollectionBehavior_(behavior)
            ns_win.setLevel_(NSFloatingWindowLevel)
            ns_win.setHidesOnDeactivate_(False)
            ns_win.makeKeyAndOrderFront_(None)
            applied += 1

        print(f"[WINDOW] Stealth + All-Spaces applied to {applied} window(s). Dock icon hidden ✅")

    except Exception as e:
        print(f"[WINDOW] Error: {e}")


def start_ui():
    global _root, _text_box

    _root = tk.Tk()              # ← tkinter fully initialised first
    _root.title("AI Solution")
    _root.attributes("-topmost", True)
    _root.geometry("700x500")

    scroll = tk.Scrollbar(_root)
    scroll.pack(side="right", fill="y")

    _text_box = tk.Text(
        _root, wrap="word",
        yscrollcommand=scroll.set,
        font=("Courier", 12)
    )
    _text_box.pack(expand=True, fill="both")
    scroll.config(command=_text_box.yview)

    _text_box.insert("1.0", "Waiting for input...\n")
    _text_box.config(state="disabled")

    # ── Now safe to call — tkinter is fully up ───────────────────
    _root.after(800, _apply_window_behaviors)
    _root.update()
    _root.after(30, _poll_queues)
    _root.mainloop()


def _poll_queues():
    global _root, _text_box

    if not _root or not _root.winfo_exists() or _text_box is None:
        return

    try:
        while not text_queue.empty():
            try:
                text = text_queue.get_nowait()
                _text_box.config(state="normal")
                _text_box.delete("1.0", tk.END)
                _text_box.insert("1.0", text)
                _text_box.config(state="disabled")
            except Empty:
                break

        while not chunk_queue.empty():
            try:
                chunk = chunk_queue.get_nowait()
                _text_box.config(state="normal")

                if chunk is STREAM_DONE:
                    _text_box.config(state="disabled")
                else:
                    _text_box.insert(tk.END, chunk)
                    _text_box.see(tk.END)
            except Empty:
                break

    finally:
        if _root and _root.winfo_exists():
            _root.after(30, _poll_queues)


def clear_popup():
    text_queue.put("⏳ Solving...\n\n")

def send_chunk(chunk):
    chunk_queue.put(chunk)

def finish_stream():
    chunk_queue.put(STREAM_DONE)

def show_popup(text):
    text_queue.put(text)