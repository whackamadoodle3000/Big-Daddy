# import json
# from google import genai
# # where log lives:
# LOG_PATH   = "format.jsonl"
# # where final text:
# OUTPUT_DOC = "parent_report.txt"
# # Gemini API key
# GEMINI_API_KEY = "AIzaSyDyYNsV7o27ppAIyTkBQkNlWjUte130xs8"

# def load_snapshots():
#     with open(LOG_PATH, "r") as f:
#         return [json.loads(line) for line in f]
# def build_prompt(snaps):
#     lines = []
#     for rec in snaps:
#         ts = rec["timestamp"]
#         # pick top 2 emotions by score
#         emo = rec["emotion"]
#         top2 = sorted(emo.items(), key=lambda kv: -kv[1])[:2]
#         emo_text = ", ".join(f"{k}={v:.2f}" for k, v in top2)
#         count = len(rec["chain_events"])
#         lines.append(f"At {ts}, emotions were {emo_text}; {count} chain events.")
#     joined = "\n".join(lines)

#     return f"""
# You are a security assistant summarizing a child's computer activity for their parents.
# Below are raw data snapshots:

# {joined}

# Please write a clear, compassionate summary that:
# - Describes what the child saw or did
# - Notes any emotional concerns
# - Offers simple suggestions for parents

# Deliver plain text only.
# """

# def call_gemini(prompt):
#     client = genai.Client(api_key=GEMINI_API_KEY, model="gemini-pro-v1")
#     res = client.chat([{"role": "user", "content": prompt}])
#     return res.choices[0].message.content
# def write_report(text):
#     with open(OUTPUT_DOC, "w") as f:
#         f.write(text)
# if __name__ == "__main__":
#     snaps  = load_snapshots()
#     prompt = build_prompt(snaps)
#     report = call_gemini(prompt)
#     write_report(report)
#     print(f"Report saved to {OUTPUT_DOC}")

import json
import os
from google import genai
from datetime import datetime, timezone

# Load configuration via environment variables
LOG_PATH = os.getenv("LOG_PATH", "format.jsonl")
OUTPUT_DOC = os.getenv("OUTPUT_DOC", "parent_report.txt")
GEMINI_API_KEY = "AIzaSyAwTF-bonFiKjb9a0IpggSkzxiW5FNxJ50"

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is required.")

def load_snapshots():
    """Load all JSONL snapshots into a list of records."""
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def build_prompt(snaps):
    """
    Build the instruction prompt for Gemini based on snapshots.
    """
    lines = []

    for rec in snaps:
        ts = rec["timestamp"]
        # pick top 2 emotions
        emo = rec.get("emotion", {})
        top2 = sorted(emo.items(), key=lambda kv: -kv[1])[:2]
        emo_text = ", ".join(f"{k}={v:.2f}" for k, v in top2)

        # number of cached events
        events = rec.get("chain_events", [])
        count = len(events)

        lines.append(f"At {ts}, emotions: {emo_text}; chain events: {count} items.")

    joined = "\n".join(lines)

    return f"""
You are a security assistant summarizing a child's computer activity for their parents.
Below are raw data snapshots recorded in UTC:

{joined}

Please write a clear, compassionate summary that:
- Describes what the child viewed or did during these times.
- Notes any emotional trends or concerns.
- Offers simple, actionable suggestions for parents.

Provide plain text output only.
"""

def call_gemini(prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    chat = client.chats.create(model="gemini-2.5-pro")
    response = chat.send_message(prompt)
    return response.text

def write_report(text):
    with open(OUTPUT_DOC, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Report saved to {OUTPUT_DOC} at {datetime.now(timezone.utc).isoformat()}Z")

if __name__ == "__main__":
    snaps = load_snapshots()
    if not snaps:
        print("No snapshots found. Exiting.")
        exit(1)
    prompt = build_prompt(snaps)
    report = call_gemini(prompt)
    write_report(report)