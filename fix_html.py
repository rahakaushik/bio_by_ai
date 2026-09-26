import os
import re

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            # Remove the line with 2026-09-25
            new_content = re.sub(r'[ \t]*<option value="[^"]*2026-09-25/index\.html"[^>]*>2026-09-25</option>\n?', '', content)
            
            if new_content != content:
                with open(path, "w") as f:
                    f.write(new_content)
                print(f"Fixed {path}")

# Fix knowledge_graph.json
kg_path = "knowledge_graph.json"
if os.path.exists(kg_path):
    with open(kg_path, "r") as f:
        kg_content = f.read()
    
    new_kg = kg_content.replace("editions/2026-09-25", "editions/2026-09-26")
    
    if new_kg != kg_content:
        with open(kg_path, "w") as f:
            f.write(new_kg)
        print("Fixed knowledge_graph.json")

