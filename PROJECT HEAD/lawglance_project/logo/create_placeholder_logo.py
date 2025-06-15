"""
Create a placeholder logo for LawGlance if none exists.
This script generates a simple logo with the LawGlance text and icon.
"""
import os
from pathlib import Path

def create_placeholder_logo():
    """Create a placeholder logo for LawGlance."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create directory if it doesn't exist
        logo_dir = Path(__file__).parent
        logo_dir.mkdir(exist_ok=True)
        
        # Define logo path
        logo_path = logo_dir / "logo.png"
        icon_path = logo_dir / "logo.ico"
        
        # Skip if logo already exists
        if logo_path.exists():
            return
        
        # Create image
        img_size = (512, 512)
        img = Image.new('RGBA', img_size, color=(33, 150, 243, 255))  # Blue background
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font_size = 72
            try:
                font = ImageFont.truetype("Arial Bold.ttf", font_size)
            except:
                font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        text = "LawGlance"
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (200, 40)
        position = ((img_size[0] - text_width) // 2, (img_size[1] - text_height) // 2)
        
        # Add a legal scale symbol
        draw.rectangle([156, 340, 356, 360], fill=(255, 255, 255, 255))  # Horizontal line
        draw.rectangle([246, 240, 266, 340], fill=(255, 255, 255, 255))  # Vertical line
        draw.ellipse([196, 190, 246, 240], outline=(255, 255, 255, 255), width=10)  # Left circle
        draw.ellipse([266, 190, 316, 240], outline=(255, 255, 255, 255), width=10)  # Right circle
        
        # Draw text
        draw.text(position, text, font=font, fill=(255, 255, 255, 255))
        
        # Save as PNG
        img.save(logo_path, 'PNG')
        print(f"Created logo at {logo_path}")
        
        # Also save as ICO for Windows applications
        if not icon_path.exists():
            img.save(icon_path, format='ICO', sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
            print(f"Created icon at {icon_path}")
        
    except ImportError:
        print("Error: PIL/Pillow not installed. Cannot create logo.")
    except Exception as e:
        print(f"Error creating logo: {str(e)}")

if __name__ == "__main__":
    create_placeholder_logo()
