import os
import re
import sys

# We need AIArtist
sys.path.append("src")
from artist import AIArtist

artist = AIArtist()

edition_dir = "public/editions/2026-09-12"
os.makedirs(f"{edition_dir}/images", exist_ok=True)

for i in range(3):
    img_path = f"{edition_dir}/images/story_{i}_regen.jpg"
    print(f"Generating image {i}")
    prompt = artist.generate_image_prompt(f"Scientific Discovery {i}", "Recent discovery in longevity.")
    artist.generate_image(prompt, img_path)

for root, _, files in os.walk(edition_dir):
    for file in files:
        if not file.endswith(".html"): continue
        filepath = os.path.join(root, file)
        with open(filepath, "r") as f:
            content = f.read()
            
        # replace src="../../images/story_0_..." with src="images/story_0_regen.jpg"
        for i in range(3):
            content = re.sub(rf'src="\.\./\.\./images/story_{i}_[0-9]+\.jpg"', f'src="images/story_{i}_regen.jpg"', content)
            
        with open(filepath, "w") as f:
            f.write(content)
