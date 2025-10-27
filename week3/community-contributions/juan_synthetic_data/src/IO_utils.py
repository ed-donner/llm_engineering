import os
import glob

def cleanup_temp_files(temp_dir: str):
    """
    Remove all temporary files from the given directory.
    """
    files = glob.glob(os.path.join(temp_dir, "*"))
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            print(f"[Warning] Could not delete {f}: {e}")
