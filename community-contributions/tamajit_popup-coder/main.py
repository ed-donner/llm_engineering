import time
import threading
from pynput import keyboard


# =========================
# GLOBAL STATE
# =========================
last_trigger = 0
is_running = False
lock = threading.Lock()


# =========================
# PIPELINE
# =========================
# main.py  (only run_pipeline shown — rest of file unchanged)

def run_pipeline():
    global last_trigger, is_running

    with lock:
        if is_running:
            print("[INFO] Already running, skipping...")
            return
        if time.time() - last_trigger < 2:
            return
        is_running = True
        last_trigger = time.time()

    try:
        from capture.screen import capture_screen
        from ocr.reader import extract_text
        from utils.cleaner import clean_text
        from ai.solver import solve_problem_stream
        from ui.popup import show_popup, clear_popup, send_chunk, finish_stream
        import pyperclip
        print("\n[INFO] Running pipeline...")

        # 1. Capture
        img_path = capture_screen()
        if not img_path:
            print("[ERROR] Screenshot failed")
            return

        # 2. OCR
        print("[INFO] Running OCR...")
        text = extract_text(img_path)

        # 3. Clean
        print("[INFO] Cleaning text...")
        cleaned = clean_text(text)
        print("\n===== CLEANED TEXT =====\n", cleaned[:300], "\n========================\n")

        # 4. Stream AI response directly into popup
        print("[INFO] Streaming to AI...")
        clear_popup()           # show "Solving..." immediately

        full_solution = []

        for chunk in solve_problem_stream(cleaned):
            send_chunk(chunk)           # → popup updates live
            full_solution.append(chunk) # accumulate for clipboard

        finish_stream()

        # 5. Clipboard (after stream completes)
        solution = "".join(full_solution)
        pyperclip.copy(solution)
        print("[INFO] Copied to clipboard ✅")

    except Exception as e:
        show_popup(f"[ERROR] {e}")
        print("[ERROR]", e)

    finally:
        with lock:
            is_running = False


# =========================
# HOTKEY SYSTEM
# =========================
def _set_start_hotkey():
    try:
        from capture.screen import set_start
        set_start()
    except Exception as e:
        print(f"[ERROR] set_start failed: {e}")
        try:
            from ui.popup import show_popup
            show_popup(f"[ERROR] set_start failed: {e}")
        except Exception:
            pass


def _set_end_hotkey():
    try:
        from capture.screen import set_end
        set_end()
    except Exception as e:
        print(f"[ERROR] set_end failed: {e}")
        try:
            from ui.popup import show_popup
            show_popup(f"[ERROR] set_end failed: {e}")
        except Exception:
            pass


def hotkey_listener_loop():
    print("System running...")
    print("CTRL + SHIFT + S → set TOP-LEFT")
    print("CTRL + SHIFT + D → set BOTTOM-RIGHT")
    print("CTRL + SHIFT + A → RUN PIPELINE\n")
    while True:
        try:
            keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+s': _set_start_hotkey,
                '<ctrl>+<shift>+d': _set_end_hotkey,
                '<ctrl>+<shift>+a': lambda: threading.Thread(
                    target=run_pipeline, daemon=True
                ).start()
            }).run()
        except Exception as e:
            print(f"[ERROR] Hotkey listener crashed: {e}")
            time.sleep(2)


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    # Start hotkey listener in background
    threading.Thread(target=hotkey_listener_loop, daemon=True).start()

    # Run UI in main thread (MANDATORY for macOS).
    try:
        from ui.popup import start_ui
        start_ui()
    except Exception as e:
        print(f"[ERROR] UI failed to start: {e}")

    print("[WARN] UI loop is not running. Keeping background process alive.")
    while True:
        time.sleep(60)
