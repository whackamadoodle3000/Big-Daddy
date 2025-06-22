# import time, base64, json
# from datetime import datetime, timezone
# # call into existing tools:
# from cache import langchain_cache
# from screen import capture_screenshot
# from emotion import get_latest_emotion

# LOG_PATH = "format.jsonl"
# INTERVAL_SECONDS = 86400  # change to whatever sec

# def log_snapshot():
#     ts = datetime.now(timezone.utc).isoformat()
#     events = langchain_cache.load_memory_variables({})
#     img_bytes = capture_screenshot()
#     img_b64   = base64.b64encode(img_bytes).decode("utf-8")
#     emo_data  = get_latest_emotion()
#     record = {
#         "timestamp":   ts,
#         "chain_events": events,
#         "screenshot":  img_b64,
#         "emotion":     emo_data
#     }
#     with open(LOG_PATH, "a") as f:
#         f.write(json.dumps(record) + "\n")
#     print(f"[{ts}] logged.")

# if __name__ == "__main__":
#     log_snapshot()           # do one immediately
#     while True:
#         time.sleep(INTERVAL_SECONDS)
#         log_snapshot()

# import time
# import base64
# import json
# import os
# from datetime import datetime, timezone
# from cache import langchain_cache
# from screen import capture_screenshot
# from emotion import get_latest_emotion

# # Path to append snapshots
# LOG_PATH = os.getenv("LOG_PATH", "format.jsonl")
# # Interval between snapshots (seconds)
# INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", 86400))

# def log_snapshot():
#     ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
#     # langchain_cache.load_memory_variables returns a dict, often with 'history'
#     mem = langchain_cache.load_memory_variables({})
#     events = mem.get("history", []) if isinstance(mem, dict) else []
#     img_b64 = base64.b64encode(capture_screenshot()).decode("utf-8")
#     emo_data = get_latest_emotion()

#     record = {
#         "timestamp":    ts,
#         "chain_events": events,
#         "screenshot":   img_b64,
#         "emotion":      emo_data
#     }

#     # Ensure log file exists\ n    os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
#     with open(LOG_PATH, "a", encoding="utf-8") as f:
#         f.write(json.dumps(record) + "\n")

#     print(f"[{ts}] Logged snapshot to {LOG_PATH}")

# if __name__ == "__main__":
#     try:
#         log_snapshot()  # initial run
#         while True:
#             time.sleep(INTERVAL_SECONDS)
#             log_snapshot()
#     except KeyboardInterrupt:
#         print("Shutting down logger.")

import csv
import json
import os
import glob
from datetime import datetime

AGENT_LOGS    = "agent_logs.csv"
EMOTION_LOG   = "emotionLog.txt"
SCREENSHOT_DIR= "screenshots"
OUTPUT_JSONL  = "format.jsonl"
KEYS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

def load_emotions():
    """
    Parse emotionLog.txt, return a dict mapping datetime → {emotion: value, …}
    """
    emo_map = {}
    with open(EMOTION_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # first two tokens are date and time
            ts_str = " ".join(parts[:2])
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            # remaining tokens are k:v
            emo = {k: 0.0 for k in KEYS}
            for kv in parts[2:]:
                if ":" not in kv:
                    continue
                k, v = kv.split(":", 1)
                try:
                    emo[k] = float(v)
                except ValueError:
                    pass
            emo_map[dt] = emo
    return emo_map

def find_screenshot(dt: datetime) -> str | None:
    """
    Given a datetime, look for screenshots/screenshot_<epoch>.png
    Fallback to any file with that epoch prefix.
    """
    epoch = int(dt.timestamp())
    base = f"screenshot_{epoch}.png"
    path = os.path.join(SCREENSHOT_DIR, base)
    if os.path.exists(path):
        return base
    # fallback: any file starting with screenshot_<epoch>
    matches = glob.glob(os.path.join(SCREENSHOT_DIR, f"screenshot_{epoch}*.png"))
    if matches:
        return os.path.basename(matches[0])
    return None

def build_jsonl():
    emotions = load_emotions()
    # open CSV and JSONL
    with open(AGENT_LOGS, newline="", encoding="utf-8") as csvf, \
         open(OUTPUT_JSONL, "w", encoding="utf-8") as out:

        reader = csv.DictReader(csvf)
        for row in reader:
            dt = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            
            emo = emotions.get(dt, {})

            # find the screenshot filename
            shot = find_screenshot(dt)

            # build one JSON object per line, in the same order as your CSV
            record = {
                "timestamp":          row["timestamp"],
                "current_url":        row.get("current_url", ""),
                "site_category":      row.get("site_category", ""),
                "time_on_site":       float(row.get("time_on_site", 0) or 0),
                "recommendation":     row.get("recommendation", ""),
                "message":            row.get("message", ""),
                "encouragement_count":int(row.get("encouragement_count", 0) or 0),
                "warning_count":      int(row.get("warning_count", 0) or 0),
                "intervention_count": int(row.get("intervention_count", 0) or 0),
                "screenshot":         shot,
                "emotion":            emo
            }

            out.write(json.dumps(record) + "\n")
            print(f"Wrote JSONL for {row['timestamp']} → screenshot={shot}, emotion_keys={list(emo)}")

if __name__ == "__main__":
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    build_jsonl()