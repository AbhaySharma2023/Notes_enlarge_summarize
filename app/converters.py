import re
from typing import Dict, List, Any


def plain_text_to_tiptap(text: str) -> Dict[str, Any]:
    """Convert plain text to Tiptap doc JSON format."""
    lines = text.strip().split('\n')
    content = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Check for ordered list (1. 2. 3. etc.)
        if re.match(r'^\d+\.\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                item_text = re.sub(r'^\d+\.\s+', '', lines[i].strip())
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": item_text
                        }]
                    }]
                })
                i += 1
            
            content.append({
                "type": "orderedList",
                "content": list_items
            })
            
        # Check for unordered list (- or * or •)
        elif re.match(r'^[-*•]\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^[-*•]\s+', lines[i].strip()):
                item_text = re.sub(r'^[-*•]\s+', '', lines[i].strip())
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": item_text
                        }]
                    }]
                })
                i += 1
            
            content.append({
                "type": "bulletList",
                "content": list_items
            })
            
        # Regular paragraph
        else:
            # Collect multi-line paragraphs
            paragraph_lines = [line]
            i += 1
            while (i < len(lines) and 
                   lines[i].strip() and 
                   not re.match(r'^[-*•]\s+', lines[i].strip()) and
                   not re.match(r'^\d+\.\s+', lines[i].strip())):
                paragraph_lines.append(lines[i].strip())
                i += 1
            
            paragraph_text = ' '.join(paragraph_lines)
            content.append({
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": paragraph_text
                }]
            })
    
    return {
        "type": "doc",
        "content": content
    }