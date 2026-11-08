from PIL import Image, ImageDraw, ImageFont
import os
import math

os.makedirs("tests/fixtures", exist_ok=True)
img = Image.new("RGB", (256, 256), color=(240, 242, 245))
draw = ImageDraw.Draw(img)

# Draw detailed geometric lines & gradients
for i in range(0, 256, 8):
    draw.line([(i, 0), (256 - i, 256)], fill=(i % 255, (i * 2) % 255, 180), width=1)
    draw.line([(0, i), (256, 256 - i)], fill=(120, i % 255, (256 - i) % 255), width=1)

# Circles
for r in range(10, 80, 10):
    draw.ellipse([128 - r, 128 - r, 128 + r, 128 + r], outline=(30, 40, 90), width=2)

# High frequency pattern
for x in range(20, 80, 4):
    for y in range(20, 80, 4):
        draw.rectangle([x, y, x + 2, y + 2], fill=(20, 120, 40))

# Fine text label
draw.text((150, 200), "AETHER 1X", fill=(10, 10, 10))

out_path = "tests/fixtures/test_input.png"
img.save(out_path, format="PNG")
print(f"Generated test image: {out_path} ({img.size[0]}x{img.size[1]})")

