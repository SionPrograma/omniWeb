import re
import os

def test_regex():
    path = "frontend/shell/editor.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # New backward search logic
    inner_html_matches = list(re.finditer(r"(?:\.|)innerHTML\s*=\s*(?:[`'\"]|content)", content))
    print(f"Found {len(inner_html_matches)} innerHTML assignments.")
    
    for ih_match in inner_html_matches:
        ih_pos = ih_match.start()
        prefix = content[max(0, ih_pos - 1500) : ih_pos]
        method_heads = list(re.finditer(r"(?:^|[ \t]+)(?:async\s+|)(\w+)\s*\([^)]*\)\s*\{", prefix, re.MULTILINE))
        
        if method_heads:
            last_head = method_heads[-1]
            method_name = last_head.group(1)
            print(f"Assign at {ih_pos} -> Method: {method_name}")
        else:
            print(f"Assign at {ih_pos} -> No method head found in prefix.")


if __name__ == "__main__":
    test_regex()
