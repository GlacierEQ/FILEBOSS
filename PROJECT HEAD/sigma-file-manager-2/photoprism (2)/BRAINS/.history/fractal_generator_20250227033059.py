#!/usr/bin/env python
"""
Fractal Image Generator

This script generates beautiful fractal images for use in the Sorting Hat UI.
It creates several images with blue and green color schemes.
"""
import os
import math
import numpy as np
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

# Ensure output directory exists
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_julia_set(width, height, c_real, c_imag, max_iter=100, zoom=1.0, offset_x=0, offset_y=0):
    """Generate a Julia set fractal"""
    # Create a new image
    fractal = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Compute the fractal
    for y in range(height):
        for x in range(width):
            # Map pixel position to complex plane
            zx = 1.5 * (x - width / 2) / (0.5 * zoom * width) + offset_x
            zy = 1.0 * (y - height / 2) / (0.5 * zoom * height) + offset_y
            
            i = 0
            while zx*zx + zy*zy < 4 and i < max_iter:
                tmp = zx*zx - zy*zy + c_real
                zy = 2.0*zx*zy + c_imag
                zx = tmp
                i += 1
            
            # Convert iteration count to color
            if i == max_iter:
                color = (0, 0, 0)  # Black for points in set
            else:
                # Blue and green color scheme
                v = i / max_iter
                r = int((0.3 * v) * 255)
                g = int((0.5 + 0.5 * v) * 255)
                b = int((0.7 + 0.3 * v) * 255)
                color = (r, g, b)
            
            fractal[y, x] = color
    
    return fractal

def generate_mandelbrot(width, height, max_iter=100, zoom=1.0, offset_x=0, offset_y=0):
    """Generate a Mandelbrot set fractal"""
    # Create a new image
    fractal = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Compute the fractal
    for y in range(height):
        for x in range(width):
            # Map pixel position to complex plane
            c_real = 3.0 * (x - width / 2) / (zoom * width) + offset_x
            c_imag = 2.0 * (y - height / 2) / (zoom * height) + offset_y
            
            z_real = 0
            z_imag = 0
            
            i = 0
            while z_real*z_real + z_imag*z_imag < 4 and i < max_iter:
                tmp = z_real*z_real - z_imag*z_imag + c_real
                z_imag = 2.0*z_real*z_imag + c_imag
                z_real = tmp
                i += 1
            
            # Convert iteration count to color
            if i == max_iter:
                color = (0, 0, 0)  # Black for points in set
            else:
                # Blue and green color scheme
                v = i / max_iter
                h = 0.6 + 0.4 * v  # Hue between blue and green
                s = 0.8  # Saturation
                l = 0.6 * v  # Lightness
                
                # HSL to RGB conversion
                c = (1 - abs(2 * l - 1)) * s
                x = c * (1 - abs((h * 6) % 2 - 1))
                m = l - c/2
                
                if 0 <= h < 1/6:
                    r, g, b = c, x, 0
                elif 1/6 <= h < 2/6:
                    r, g, b = x, c, 0
                elif 2/6 <= h < 3/6:
                    r, g, b = 0, c, x
                elif 3/6 <= h < 4/6:
                    r, g, b = 0, x, c
                elif 4/6 <= h < 5/6:
                    r, g, b = x, 0, c
                else:
                    r, g, b = c, 0, x
                
                color = (
                    int((r + m) * 255),
                    int((g + m) * 255),
                    int((b + m) * 255)
                )
            
            fractal[y, x] = color
    
    return fractal

def create_fractal_bg(width, height, output_path):
    """Create a beautiful blue-green fractal background"""
    print(f"Generating fractal background ({width}x{height})...")
    
    # Generate Julia set with blue-green parameters
    fractal = generate_julia_set(
        width, height, 
        c_real=-0.7, 
        c_imag=0.27, 
        max_iter=100,
        zoom=1.0
    )
    
    # Convert to PIL Image
    img = Image.fromarray(fractal)
    
    # Apply some post-processing
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Enhance colors
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)
    
    # Adjust brightness and contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)
    
    # Add a subtle vignette
    img = add_vignette(img)
    
    # Save the image
    ensure_dir(os.path.dirname(output_path))
    img.save(output_path)
    print(f"Saved background to {output_path}")
    return img

def create_fractal_pattern(width, height, output_path):
    """Create a seamless fractal pattern for background textures"""
    print(f"Generating fractal pattern ({width}x{height})...")
    
    # Generate a mandelbrot pattern with blue-green colors
    fractal = generate_mandelbrot(
        width, height,
        max_iter=50,
        zoom=2.5,
        offset_x=-0.5
    )
    
    # Convert to PIL Image
    img = Image.fromarray(fractal)
    
    # Make it tileable by reflecting
    img = ImageOps.mirror(img)
    
    # Apply a gaussian blur to smooth transitions
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Adjust opacity to make it subtle
    img = adjust_opacity(img, 0.3)
    
    # Save the image
    ensure_dir(os.path.dirname(output_path))
    img.save(output_path)
    print(f"Saved pattern to {output_path}")
    return img

def create_fractal_side(width, height, output_path):
    """Create a decorative fractal side panel"""
    print(f"Generating fractal side panel ({width}x{height})...")
    
    # Generate Julia set with different parameters
    fractal = generate_julia_set(
        width, height,
        c_real=-0.4,
        c_imag=0.6,
        max_iter=80,
        zoom=1.2
    )
    
    # Convert to PIL Image
    img = Image.fromarray(fractal)
    
    # Apply radial gradient to fade one side
    gradient = create_horizontal_gradient(width, height)
    img = Image.composite(img, Image.new('RGB', (width, height), (0, 0, 0)), gradient)
    
    # Apply some post-processing
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Save the image
    ensure_dir(os.path.dirname(output_path))
    img.save(output_path)
    print(f"Saved side panel to {output_path}")
    return img

def create_fractal_logo(size, output_path):
    """Create a fractal-based logo"""
    print(f"Generating fractal logo ({size}x{size})...")
    
    # Start with a small Julia set
    fractal = generate_julia_set(
        size, size,
        c_real=-0.8,
        c_imag=0.156,
        max_iter=100,
        zoom=0.8
    )
    
    # Convert to PIL Image
    img = Image.fromarray(fractal)
    
    # Apply circular mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply mask to create circular logo
    img_circle = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    img_circle.paste(img, (0, 0), mask)
    
    # Add a hat silhouette
    hat = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hat)
    
    # Draw a simple wizard hat
    center_x = size / 2
    base_y = size * 0.7
    hat_width = size * 0.7
    hat_height = size * 0.5
    
    # Hat base (brim)
    draw.ellipse(
        (center_x - hat_width/2, base_y - 5, 
         center_x + hat_width/2, base_y + 5),
        fill=(0, 0, 0, 180)
    )
    
    # Hat cone
    draw.polygon(
        [
            (center_x - hat_width/3, base_y),
            (center_x + hat_width/3, base_y),
            (center_x, base_y - hat_height)
        ],
        fill=(0, 0, 0, 180)
    )
    
    # Combine logo and hat
    final_logo = Image.alpha_composite(img_circle, hat)
    
    # Save the image
    ensure_dir(os.path.dirname(output_path))
    final_logo.save(output_path)
    print(f"Saved logo to {output_path}")
    return final_logo

def add_vignette(img, intensity=0.8):
    """Add a vignette effect to an image"""
    width, height = img.size
    
    # Create radial gradient for vignette
    gradient = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(gradient)
    
    # Draw radial gradient
    for i in range(min(width, height) // 2, 0, -1):
        # Circle gets darker as i gets smaller
        intensity_step = int(255 * (1 - (i / (min(width, height) / 2)) ** 2) * intensity)
        draw.ellipse(
            (width/2 - i, height/2 - i, width/2 + i, height/2 + i),
            fill=255 - intensity_step
        )
    
    # Apply vignette to image
    return Image.composite(img, Image.new('RGB', (width, height), (0, 0, 0)), gradient)

def create_horizontal_gradient(width, height):
    """Create a horizontal gradient mask"""
    gradient = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(gradient)
    
    for x in range(width):
        # Convert x to opacity (255 to 0 from left to right)
        opacity = 255 - int(255 * (x / width))
        draw.line([(x, 0), (x, height)], fill=opacity)
        
    return gradient

def adjust_opacity(img, opacity):
    """Adjust the opacity of an image"""
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Get the alpha channel
    alpha = img.split()[3]
    
    # Adjust opacity
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    
    # Put the modified alpha channel back
    r, g, b, _ = img.split()
    return Image.merge('RGBA', (r, g, b, alpha))

def generate_all_assets():
    """Generate all fractal assets for the UI"""
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    images_dir = os.path.join(static_dir, "images")
    ensure_dir(images_dir)
    
    print("Generating all fractal UI assets...")
    
    # Background image
    create_fractal_bg(1920, 1080, os.path.join(images_dir, "fractal-bg.png"))
    
    # Pattern for textures
    create_fractal_pattern(512, 512, os.path.join(images_dir, "fractal-pattern.png"))
    
    # Side panel decoration
    create_fractal_side(800, 1200, os.path.join(images_dir, "fractal-side.png"))
    
    # Logo
    create_fractal_logo(256, os.path.join(images_dir, "logo-fractal.png"))
    
    print("All fractal assets generated successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fractal images for UI")
    parser.add_argument("--all", action="store_true", help="Generate all assets")
    parser.add_argument("--bg", action="store_true", help="Generate background only")
    parser.add_argument("--pattern", action="store_true", help="Generate pattern only")
    parser.add_argument("--side", action="store_true", help="Generate side panel only")
    parser.add_argument("--logo", action="store_true", help="Generate logo only")
    
    args = parser.parse_args()
    
    # If no specific flag is provided, generate all assets
    if not (args.bg or args.pattern or args.side or args.logo):
        args.all = True
    
    if args.all:
        generate_all_assets()
    else:
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        images_dir = os.path.join(static_dir, "images")
        ensure_dir(images_dir)
        
        if args.bg:
            create_fractal_bg(1920, 1080, os.path.join(images_dir, "fractal-bg.png"))
        if args.pattern:
            create_fractal_pattern(512, 512, os.path.join(images_dir, "fractal-pattern.png"))
        if args.side:
            create_fractal_side(800, 1200, os.path.join(images_dir, "fractal-side.png"))
        if args.logo:
            create_fractal_logo(256, os.path.join(images_dir, "logo-fractal.png"))