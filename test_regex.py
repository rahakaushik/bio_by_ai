import re
with open("public/editions/2026-09-12/index.html", "r") as f:
    content = f.read()

new_select = "REPLACED_SELECT"
new_content = re.sub(r'<select onchange="if \(this\.value\) window\.location\.href=this\.value;".*?</select>', new_select, content, flags=re.DOTALL)

if "REPLACED_SELECT" in new_content:
    print("MATCHED!")
else:
    print("FAILED TO MATCH")
