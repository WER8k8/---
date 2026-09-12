"""Generate PWA icons for the website"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a square icon with company branding"""
    # Create image with blue background (company theme color)
    img = Image.new('RGB', (size, size), color='#1890ff')
    draw = ImageDraw.Draw(img)

    # Draw a simple logo - letter "Y" for Youding
    # Calculate proportions based on size
    margin = size // 5
    center_x = size // 2
    center_y = size // 2

    # Draw white circle background for the letter
    circle_radius = size // 2 - margin
    draw.ellipse(
        [center_x - circle_radius, center_y - circle_radius,
         center_x + circle_radius, center_y + circle_radius],
        fill='#ffffff'
    )

    # Draw stylized "Y" in blue
    y_color = '#1890ff'
    line_width = max(4, size // 20)

    # Left diagonal of Y
    left_top = (center_x - circle_radius // 2, center_y - circle_radius // 2)
    bottom = (center_x, center_y + circle_radius // 3)

    # Right diagonal of Y
    right_top = (center_x + circle_radius // 2, center_y - circle_radius // 2)

    draw.line([left_top, bottom], fill=y_color, width=line_width)
    draw.line([right_top, bottom], fill=y_color, width=line_width)

    # Vertical stem of Y
    stem_bottom = (center_x, center_y + circle_radius - margin // 2)
    draw.line([bottom, stem_bottom], fill=y_color, width=line_width)

    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created icon: {output_path} ({size}x{size})")

if __name__ == '__main__':
    icons_dir = os.path.dirname(os.path.abspath(__file__))

    # Create 192x192 icon
    create_icon(192, os.path.join(icons_dir, 'icon-192x192.png'))

    # Create 512x512 icon
    create_icon(512, os.path.join(icons_dir, 'icon-512x512.png'))

    print("All icons generated successfully!")
