from pynput import keyboard
from audio import get_audio, start_recording, stop_recording, is_currently_recording, start_audio_process, is_speech_empty
import pyperclip
from transcriber import convert_audio_to_text

kb = keyboard.Controller()
keys_pressed = set()

def on_press(key):
    keys_pressed.add(key)

    if not is_currently_recording() and keyboard.Key.ctrl_l in keys_pressed and keyboard.Key.shift in keys_pressed:
        print("start recording")
        start_recording()
        start_audio_process()

def on_release(key):
    keys_pressed.discard(key)

    if key == keyboard.Key.esc:
        return False

    if is_currently_recording() and (key == keyboard.Key.shift or key == keyboard.Key.ctrl_l):
        print('recording stopped, processing...')
        stop_recording()

        if is_speech_empty():
            return

        audio_array = get_audio()
        text = convert_audio_to_text(audio_array)
        print('pasting text')
        pyperclip.copy(text)
        with kb.pressed(keyboard.Key.ctrl):
            kb.press('v')
            kb.release('v')
        
def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            pass
