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

import time
import base64
import json
import os
from datetime import datetime, timezone
from cache import langchain_cache
from screen import capture_screenshot
from emotion import get_latest_emotion

# Path to append snapshots
LOG_PATH = os.getenv("LOG_PATH", "format.jsonl")
# Interval between snapshots (seconds)
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", 86400))

def log_snapshot():
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
    # langchain_cache.load_memory_variables returns a dict, often with 'history'
    mem = langchain_cache.load_memory_variables({})
    events = mem.get("history", []) if isinstance(mem, dict) else []
    img_b64 = base64.b64encode(capture_screenshot()).decode("utf-8")
    emo_data = get_latest_emotion()

    record = {
        "timestamp":    ts,
        "chain_events": events,
        "screenshot":   img_b64,
        "emotion":      emo_data
    }

    # Ensure log file exists\ n    os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"[{ts}] Logged snapshot to {LOG_PATH}")

if __name__ == "__main__":
    try:
        log_snapshot()  # initial run
        while True:
            time.sleep(INTERVAL_SECONDS)
            log_snapshot()
    except KeyboardInterrupt:
        print("Shutting down logger.")