import os
from datetime import datetime

start_pos = None
end_pos = None
_pyautogui = None
_pyautogui_import_error = None


def _get_pyautogui():
    global _pyautogui, _pyautogui_import_error
    if _pyautogui is not None:
        return _pyautogui
    if _pyautogui_import_error is not None:
        return None
    try:
        import pyautogui as _imported_pyautogui
        _pyautogui = _imported_pyautogui
        return _pyautogui
    except Exception as e:
        _pyautogui_import_error = e
        print(f"[ERROR] pyautogui unavailable: {e}")
        return None

def set_start():
    global start_pos
    pyautogui = _get_pyautogui()
    if pyautogui is None:
        print("[ERROR] Cannot set start point without pyautogui")
        return
    start_pos = pyautogui.position()
    print(f"[INFO] Top-left set at: {start_pos}")

def set_end():
    global end_pos
    pyautogui = _get_pyautogui()
    if pyautogui is None:
        print("[ERROR] Cannot set end point without pyautogui")
        return
    end_pos = pyautogui.position()
    print(f"[INFO] Bottom-right set at: {end_pos}")

def capture_screen():
    global start_pos, end_pos
    pyautogui = _get_pyautogui()
    if pyautogui is None:
        print("[ERROR] Cannot capture screen without pyautogui")
        return None

    if start_pos is None or end_pos is None:
        print("[ERROR] Region not set properly!")
        return None

    x1, y1 = start_pos
    x2, y2 = end_pos

    x = min(x1, x2)
    y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    if width == 0 or height == 0:
        print("[ERROR] Invalid region!")
        return None

    if not os.path.exists("temp"):
        os.makedirs("temp")

    filename = f"temp/screen_{int(datetime.now().timestamp())}.png"

    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    screenshot.save(filename)

    print(f"[INFO] Screenshot saved at: {filename}")

    return filename