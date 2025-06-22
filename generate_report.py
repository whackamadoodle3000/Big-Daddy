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
from fpdf import FPDF
import markdown
import re

# Load configuration via environment variables
LOG_PATH = os.getenv("LOG_PATH", "format.jsonl")
OUTPUT_DOC = os.getenv("OUTPUT_DOC", "parent_report.pdf")
GEMINI_API_KEY = "AIzaSyCPczjS5PlqeGWQsUyDWGC_FL7Qf3Hr8As"

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
        # ts = rec["timestamp"]
        # # pick top 2 emotions
        # emo = rec.get("emotion", {})
        # top2 = sorted(emo.items(), key=lambda kv: -kv[1])[:2]
        # emo_text = ", ".join(f"{k}={v:.2f}" for k, v in top2)

        # # number of cached events
        # events = rec.get("chain_events", [])
        # count = len(events)

        # lines.append(f"At {ts}, emotions: {emo_text}; chain events: {count} items.")

        ts        = rec["timestamp"]
        url       = rec.get("current_url", "<none>")
        category  = rec.get("site_category", "")
        tsec      = rec.get("time_on_site", 0.0)
        recmd     = rec.get("recommendation", "")
        emo       = rec.get("emotion", {})
        # top two emotions
        top2      = sorted(emo.items(), key=lambda kv: -kv[1])[:2]
        emo_text  = ", ".join(f"{k}={v:.2f}" for k,v in top2)

        lines.append(
            f"At {ts}, visited {url} (category: {category}) for {tsec:.1f}s; "
            f"recommendation: {recmd}. Emotions: {emo_text}."
        )

    joined = "\n".join(lines)

    return f"""
You are a security assistant summarizing a child's computer activity for their parents.
Below are raw data snapshots recorded in UTC:

{joined}

Please write a clear, compassionate 1-page summary that:
- Describes what the child viewed or did during these times.
- Notes any emotional trends or concerns.
- Offers simple, actionable suggestions for parents.

Provide the output in Markdown format.
"""

def call_gemini(prompt):
    client = genai.Client(api_key=GEMINI_API_KEY)
    chat = client.chats.create(model="gemini-2.5-pro")
    response = chat.send_message(prompt)
    return response.text

def clean_text_for_pdf(text):
    """Clean text to remove problematic Unicode characters for PDF generation."""
    # Replace common problematic Unicode characters
    replacements = {
        '\u2019': "'",  # Right single quotation mark
        '\u2018': "'",  # Left single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2026': '...',# Horizontal ellipsis
        '\u00a0': ' ',  # Non-breaking space
        '\u2022': '*',  # Bullet point
        '\u2023': '*',  # Triangular bullet
        '\u25e6': '*',  # White bullet
        '\u2043': '*',  # Hyphen bullet
        '\u204e': '*',  # Low asterisk
        '\u00b7': '*',  # Middle dot
    }
    
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # More aggressive cleaning - remove any remaining problematic characters
    # Keep only ASCII printable characters plus common safe characters
    cleaned_chars = []
    for char in text:
        if ord(char) < 128:  # ASCII characters
            cleaned_chars.append(char)
        elif char in ['\n', '\r', '\t']:  # Keep essential whitespace
            cleaned_chars.append(char)
        else:
            cleaned_chars.append('?')  # Replace unknown characters
    
    return ''.join(cleaned_chars)

def write_report(text):
    # Clean the text before processing
    cleaned_text = clean_text_for_pdf(text)
    
    # Create PDF with custom styling
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Define colors (RGB values)
    HEADER_COLOR = (41, 128, 185)    # Professional blue
    SUBHEADER_COLOR = (52, 152, 219) # Lighter blue
    TEXT_COLOR = (44, 62, 80)        # Dark gray
    BULLET_COLOR = (231, 76, 60)     # Red for bullet points
    
    # Set default text color
    pdf.set_text_color(*TEXT_COLOR)
    
    # Add title with styling
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(*HEADER_COLOR)
    pdf.cell(0, 15, "Student Activity Report", ln=True, align='C')
    pdf.ln(5)
    
    # Add date
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(128, 128, 128)  # Gray
    pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ln=True, align='C')
    pdf.ln(10)
    
    # Reset text color for content
    pdf.set_text_color(*TEXT_COLOR)
    
    # Split text into lines and process
    lines = cleaned_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(4)  # Small spacing for empty lines
            continue
            
        try:
            # Handle different markdown elements
            if line.startswith('# '):
                # Main header
                pdf.ln(8)
                pdf.set_font("Arial", 'B', 18)
                pdf.set_text_color(*HEADER_COLOR)
                header_text = line[2:].strip()
                pdf.cell(0, 12, header_text, ln=True)
                pdf.ln(6)
                pdf.set_text_color(*TEXT_COLOR)
                
            elif line.startswith('## '):
                # Subheader
                pdf.ln(6)
                pdf.set_font("Arial", 'B', 14)
                pdf.set_text_color(*SUBHEADER_COLOR)
                subheader_text = line[3:].strip()
                pdf.cell(0, 10, subheader_text, ln=True)
                pdf.ln(4)
                pdf.set_text_color(*TEXT_COLOR)
                
            elif line.startswith('### '):
                # Sub-subheader
                pdf.ln(4)
                pdf.set_font("Arial", 'B', 12)
                pdf.set_text_color(*SUBHEADER_COLOR)
                subsubheader_text = line[4:].strip()
                pdf.cell(0, 8, subsubheader_text, ln=True)
                pdf.ln(3)
                pdf.set_text_color(*TEXT_COLOR)
                
            elif line.startswith('- ') or line.startswith('* '):
                # Bullet points with color
                pdf.set_font("Arial", '', 11)
                bullet_text = line[2:].strip()
                
                # Add colored bullet
                pdf.set_text_color(*BULLET_COLOR)
                pdf.write(7, "  • ")
                pdf.set_text_color(*TEXT_COLOR)
                pdf.write(7, bullet_text)
                pdf.ln(7)
                
            elif '**' in line:
                # Handle bold text
                pdf.set_font("Arial", '', 11)
                
                # Check if entire line is bold (e.g., **Title**)
                if line.startswith('**') and line.endswith('**') and line.count('**') == 2:
                    # Entire line is bold
                    pdf.ln(4)
                    pdf.set_font("Arial", 'B', 13)
                    pdf.set_text_color(*HEADER_COLOR)
                    bold_text = line[2:-2].strip()  # Remove ** from both ends
                    pdf.cell(0, 10, bold_text, ln=True)
                    pdf.ln(4)
                    pdf.set_text_color(*TEXT_COLOR)
                else:
                    # Mixed bold and normal text within the line
                    parts = line.split('**')
                    x_start = pdf.get_x()
                    
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            # Normal text
                            pdf.set_font("Arial", '', 11)
                            pdf.write(7, part)
                        else:
                            # Bold text
                            pdf.set_font("Arial", 'B', 11)
                            pdf.set_text_color(*HEADER_COLOR)
                            pdf.write(7, part)
                            pdf.set_text_color(*TEXT_COLOR)
                    pdf.ln(7)
                
            elif line.startswith('> '):
                # Quote/callout box
                pdf.ln(3)
                pdf.set_fill_color(245, 245, 245)  # Light gray background
                pdf.set_font("Arial", 'I', 11)
                quote_text = line[2:].strip()
                pdf.cell(0, 8, f"   {quote_text}", ln=True, fill=True)
                pdf.ln(3)
                
            else:
                # Regular paragraph text
                pdf.set_font("Arial", '', 11)
                
                # Handle long lines by wrapping
                if len(line) > 80:
                    # Split long lines into multiple lines
                    words = line.split(' ')
                    current_line = ""
                    
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            if current_line.strip():
                                pdf.write(7, current_line.strip())
                                pdf.ln(7)
                            current_line = word + " "
                    
                    if current_line.strip():
                        pdf.write(7, current_line.strip())
                        pdf.ln(7)
                else:
                    pdf.write(7, line)
                    pdf.ln(7)
                    
        except Exception as e:
            # Fallback for any problematic lines
            pdf.set_font("Arial", '', 11)
            pdf.set_text_color(*TEXT_COLOR)
            safe_line = str(line).encode('ascii', errors='replace').decode('ascii')
            pdf.write(7, safe_line)
            pdf.ln(7)
    
    # Add footer
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, "Generated by Big Daddy Student Monitoring System", ln=True, align='C')
    
    pdf.output(OUTPUT_DOC)
    print(f"Report saved to {OUTPUT_DOC} at {datetime.now(timezone.utc).isoformat()}Z")

if __name__ == "__main__":
    snaps = load_snapshots()
    if not snaps:
        print("No snapshots found. Exiting.")
        exit(1)
    prompt = build_prompt(snaps)
    report = call_gemini(prompt)
    write_report(report)