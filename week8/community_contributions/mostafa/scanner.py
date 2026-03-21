import psutil
import os
import json
from datetime import datetime

# Path to store fingerprints (could be SQLite, but JSON for simplicity)
FINGERPRINT_FILE = "process_fingerprints.json"

def load_fingerprints():
    try:
        with open(FINGERPRINT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_fingerprints(fingerprints):
    with open(FINGERPRINT_FILE, 'w') as f:
        json.dump(fingerprints, f, indent=2)

def get_process_fingerprint(proc):
    """Return a unique fingerprint string for a process."""
    try:
        exe = proc.exe()
        inode = os.stat(exe).st_ino if os.path.exists(exe) else 0
        cmdline = ' '.join(proc.cmdline())
        uid = proc.uids().real
        return f"{exe}|{inode}|{cmdline}|{uid}"
    except:
        return None

def get_all_processes():
    """Collect all running processes with relevant details."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'net_connections', 'open_files']):
        try:
            p = proc.info
            pid = p['pid']
            name = p['name'] or "unknown"
            exe = p['exe'] or "unknown"
            cmdline = ' '.join(p['cmdline']) if p['cmdline'] else ""
            user = p['username'] or "unknown"
            # Parent
            try:
                parent = psutil.Process(proc.ppid()).name()
            except:
                parent = "unknown"
            # Network connections
            conns = []
            try:
                for conn in proc.net_connections(kind='inet'):
                    # laddr/raddr are (ip, port) tuples - use indexing for compatibility
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "?"
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "?"
                    conns.append(f"{laddr} -> {raddr} ({conn.status})")
            except:
                conns = ["(access denied)"]
            # Open files
            files = []
            try:
                for f in proc.open_files():
                    files.append(f.path)
            except:
                files = ["(access denied)"]
            processes.append({
                "pid": pid,
                "name": name,
                "exe": exe,
                "cmdline": cmdline,
                "user": user,
                "parent": parent,
                "connections": conns,
                "open_files": files
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return processes

def get_new_or_changed_processes(processes, fingerprints):
    """Return only processes that are new or have changed fingerprint."""
    new_list = []
    for p in processes:
        # Create a temporary psutil.Process object to compute fingerprint (inefficient)
        # For simplicity, we'll use the collected data to create a fingerprint-like key
        # But fingerprint requires exe, inode, cmdline, uid – we have them in p.
        # We'll recompute fingerprint here (could be done during collection)
        # For demo, we'll just use exe+cmdline+user as a weak key.
        key = f"{p['exe']}|{p['cmdline']}|{p['user']}"
        if key not in fingerprints or fingerprints[key].get('last_analyzed') is None:
            new_list.append(p)
        # else skip
    return new_list