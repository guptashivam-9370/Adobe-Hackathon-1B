from tkinter.filedialog import test
import pymupdf  # PyMuPDF
import json
import os
from collections import Counter
import re

import os
import json
import pymupdf  # PyMuPDF
from collections import Counter

def group_spans_into_lines(page, tolerance=2):
    """
    Groups all text spans on a page into logical lines based on their vertical position.
    Only processes blocks that have exactly one line and that line has exactly one span.
    """
    spans = [
        s for b in page.get_text("dict")["blocks"]
        if isinstance(b, dict) and "lines" in b and isinstance(b["lines"], list)
        for l in b["lines"] for s in l["spans"]
    ]
    if not spans:
        return []

    spans.sort(key=lambda s: (s['bbox'][1], s['bbox'][0])) 

    lines = []
    current_line = []
    if spans:
        current_line.append(spans[0])
        last_y = spans[0]['bbox'][1]

    for s in spans[1:]:
        if abs(s['bbox'][1] - last_y) < tolerance:
            current_line.append(s)
        else:
            lines.append(sorted(current_line, key=lambda i: i['bbox'][0]))
            current_line = [s]
            last_y = s['bbox'][1]
    
    lines.append(sorted(current_line, key=lambda i: i['bbox'][0])) 
    
    return lines

def get_page_body_size(page):
    """
    Analyzes a single page to find its most common font size.
    """
    font_size_counts = Counter()
    spans = [s for b in page.get_text("dict")["blocks"] if "lines" in b for l in b["lines"] for s in l["spans"]]
    for s in spans:
        font_size_counts[round(s["size"])] += 1
    
    if not font_size_counts:
        return 12.0 # Default if no text on page

    most_common_size = font_size_counts.most_common(1)[0][0]
    
    # Safeguard: If the most common size is very large, it's likely a title page.
    # In that case, fall back to a standard default size.
    if most_common_size > 14:
        return 12.0

    return most_common_size

def find_title(doc):
    """Finds the title using spatial clustering on the first page."""
    if not doc or len(doc) == 0:
        return "No Title Found"
    
    lines = group_spans_into_lines(doc[0])
    
    max_size = 0
    title_line = None
    print('ho')
    for line in lines:
        print(line)
        if line:
            avg_size = sum(s['size'] for s in line) / len(line)
            if avg_size > max_size:
                text = " ".join(s['text'] for s in line)
                if len(text) > 3 and not text.isupper():
                    max_size = avg_size
                    title_line = line
    
    if title_line:
        return " ".join(s['text'].strip() for s in title_line)
    
    return "No Title Found"

def extract_structure_1b(pdf_path):
    """
    Extracts a structured outline with content using your fine-tuned stateful logic.
    """
    doc = pymupdf.open(pdf_path)
    title = find_title(doc)

    # --- PASS 1: Detect all headings using your provided stateful logic ---
    h_pattern = re.compile(r'^[1-9]\d*(\.\d+)*\.?\s|^Phase (I|II|III|IV|V):')
    
    candidates = []
    # Your stateful variables
    recent_h1_font_size = 0
    recent_h2_font_size = 0
    recent_h3_font_size = 0
    recent = -1

    for page_num, page in enumerate(doc):
        body_text_size = get_page_body_size(page)
        logical_lines = group_spans_into_lines(page)
        # print(logical_lines)
        for i, line in enumerate(logical_lines):
            if not line: continue
            full_text = re.sub(r'[^0-9a-zA-Z.\-\+\* ]', '', " ".join([s['text'] for s in line])).strip()
            # print(full_text)
            if not full_text or len(full_text) < 3 or full_text.lower() == title.lower():
                continue
            
            if not re.search(r'\b[a-zA-Z]{2,}\b', full_text):
                continue

            if len(line) > 1 and line[-1]['text'].strip().isdigit() and line[-1]['bbox'][0] > page.rect.width * 0.8:
                continue 

            # Your logic requires single-span lines for space calculation
            if len(line) != 1:
                continue

            span = line[0]
            font_size = round(span["size"])
            is_bold = "bold" in span["font"].lower()
            
            score = 0
            level = 0
            
            # Your vertical spacing logic
            space_above = None
            curr_top = line[0]['bbox'][1]
            if i > 0 and logical_lines[i-1]:
                # Ensure previous line is not empty and has spans
                if logical_lines[i-1]:
                    prev_bottom = logical_lines[i-1][-1]['bbox'][3]
                    space_above = curr_top - prev_bottom
            
            min_spacing = 2
            match = h_pattern.match(full_text)

            # Your heading detection and classification logic
            if match and (font_size > body_text_size):
                if space_above is not None and space_above > min_spacing:
                    score = 5
                    numbering = match.group().strip()
                    dot_count = numbering.count('.')
                    if numbering.endswith('.'): dot_count -= 1
                    level = dot_count + 1
            elif font_size > body_text_size:
                if (space_above and space_above > min_spacing) or i == 0:
                    score = 5
                    if recent == -1: level = 1
                    elif recent == 1: level = 1 if font_size >= recent_h1_font_size and recent_h1_font_size > 0 else 2
                    elif recent == 2:
                        if abs(font_size - recent_h2_font_size) <= 1 and recent_h2_font_size > 0: level = 2
                        elif font_size < recent_h2_font_size: level = 3
                        else: level = 1
                    else: # recent == 3
                        if abs(font_size - recent_h3_font_size) <= 1 and recent_h3_font_size > 0: level = 3
                        elif font_size > recent_h3_font_size:
                            if abs(font_size - recent_h2_font_size) <= 1 and recent_h2_font_size > 0: level = 2
                            else: level = 1
            elif font_size == body_text_size and is_bold:
                space_below = None
                if i < len(logical_lines) - 1 and logical_lines[i+1]:
                    next_top = logical_lines[i+1][0]['bbox'][1]
                    space_below = next_top - line[0]['bbox'][3]
                if (space_above and space_above > min_spacing) and (space_below and space_below > min_spacing):
                    score = 5
                    # Simplified level assignment for same-size bold headings
                    level = recent + 1 if recent != -1 and recent < 3 else 3

            if score >= 4:
                recent = level
                if level == 1: recent_h1_font_size = font_size
                elif level == 2: recent_h2_font_size = font_size
                elif level == 3: recent_h3_font_size = font_size
                
                candidates.append({
                    "text": full_text,
                    "page_num": page_num,
                    "bbox": pymupdf.Rect(line[0]['bbox']),
                    "level": f"H{level}"
                })

    if not candidates: return {"title": title, "outline": []}

    # --- PASS 2: Extract content between the finalized headings ---
    final_headings = sorted(candidates, key=lambda h: (h["page_num"], h["bbox"][1]))
    
    enriched_outline = []
    for i, heading in enumerate(final_headings):
        page_num = heading["page_num"]
        page = doc[page_num]
        
        start_pos = heading["bbox"][3] # Bottom of the current heading's bbox
        end_pos = page.rect.height # Default to bottom of page

        if i + 1 < len(final_headings):
            next_heading = final_headings[i+1]
            if next_heading["page_num"] == page_num:
                end_pos = next_heading["bbox"][1] # Top of the next heading's bbox
        
        clip_rect = pymupdf.Rect(page.rect.x0, start_pos, page.rect.x1, end_pos)
        # Extract text and clean unwanted symbols
        raw_content = page.get_text(clip=clip_rect)
        # Remove bullet symbols, newlines, and other non-alphanumeric characters except spaces and periods
        content = re.sub(r'[^\w\s\.\,]', '', raw_content)
        # Replace multiple spaces/newlines with a single space
        content = re.sub(r'\s+', ' ', content).strip()
        
        enriched_outline.append({
            "text": heading["text"],
            "page": page_num + 1,
            "level": heading["level"],
            "content": content
        })
    return {"title": title, "outline": enriched_outline}