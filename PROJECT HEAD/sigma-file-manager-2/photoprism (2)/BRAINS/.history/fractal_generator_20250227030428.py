#!/usr/bin/env python
"""
Fractal Image Generator

This script generates beautiful fractal images for use in the Sorting Hat UI.
It creates several images with blue and green color schemes.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

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
    img = img.filter(ImageFilter.GaussianBlur