/**
 * Fractal Effects for Sorting Hat UI
 * 
 * This script provides interactive fractal effects and animations
 * for the Sorting Hat web interface.
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize fractal background effect
    initFractalBackground();
    
    // Initialize card hover effects
    initCardEffects();
    
    // Initialize theme toggle
    initThemeToggle();
    
    // Create fractal canvas if container exists
    const fractalContainer = document.getElementById('fractal-canvas-container');
    if (fractalContainer) {
        createFractalCanvas(fractalContainer);
    }
});

/**
 * Initialize interactive background effect
 */
function initFractalBackground() {
    const body = document.querySelector('body');
    
    // Create subtle movement on mouse move
    document.addEventListener('mousemove', function(e) {
        const moveX = (e.clientX / window.innerWidth) * 10;
        const moveY = (e.clientY / window.innerHeight) * 10;
        
        body.style.backgroundPosition = `calc(50% + ${moveX}px) calc(50% + ${moveY}px)`;
    });
}

/**
 * Initialize card hover effects
 */
function initCardEffects() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const angleX = (y - centerY) / 20;
            const angleY = (centerX - x) / 20;
            
            card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) translateZ(10px)`;
        });
        
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
        });
    });
}

/**
 * Initialize theme toggle functionality
 */
function initThemeToggle() {
    const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    if (!toggleSwitch) return;
    
    // Check for saved theme preference
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        document.documentElement.setAttribute('data-theme', currentTheme);
        if (currentTheme === 'dark') {
            toggleSwitch.checked = true;
        }
    }
    
    // Add toggle event
    toggleSwitch.addEventListener('change', function(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
}

/**
 * Create an interactive fractal canvas
 */
function createFractalCanvas(container) {
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    function resizeCanvas() {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Julia set parameters
    let cReal = -0.7;
    let cImag = 0.27;
    const maxIterations = 100;
    
    // Colors
    const colors = [
        [15, 52, 67],    // Dark blue
        [0, 195, 255],   // Bright blue
        [52, 232, 158],  // Green
        [17, 153, 142]   // Teal
    ];
    
    // Draw the fractal
    function drawFractal() {
        const width = canvas.width;
        const height = canvas.height;
        
        const imageData = ctx.createImageData(width, height);
        const data = imageData.data;
        
        // Scale parameters based on canvas size
        const scale = Math.min(width, height) * 0.004;
        const offsetX = width / 2;
        const offsetY = height / 2;
        
        // Calculate fractal values for each pixel
        for (let x = 0; x < width; x++) {
            for (let y = 0; y < height; y++) {
                // Map pixel position to complex plane
                const zx = (x - offsetX) * scale;
                const zy = (y - offsetY) * scale;
                
                let iteration = 0;
                let zReal = zx;
                let zImag = zy;
                
                // Julia set iteration
                while (iteration < maxIterations && zReal * zReal + zImag * zImag < 4) {
                    // z = z² + c
                    const tempReal = zReal * zReal - zImag * zImag + cReal;
                    const tempImag = 2 * zReal * zImag + cImag;
                    
                    zReal = tempReal;
                    zImag = tempImag;
                    
                    iteration++;
                }
                
                // Set pixel color based on iteration count
                const pixelIndex = (y * width + x) * 4;
                
                if (iteration === maxIterations) {
                    // Point is in the set - black
                    data[pixelIndex] = 0;
                    data[pixelIndex + 1] = 0;
                    data[pixelIndex + 2] = 0;
                    data[pixelIndex + 3] = 255;
                } else {
                    // Point is outside - color based on how quickly it escaped
                    const colorIndex = iteration % colors.length;
                    const nextColorIndex = (colorIndex + 1) % colors.length;
                    const blend = (iteration % 1) * 0.7;
                    
                    const r = colors[colorIndex][0] * (1 - blend) + colors[nextColorIndex][0] * blend;
                    const g = colors[colorIndex][1] * (1 - blend) + colors[nextColorIndex][1] * blend;
                    const b = colors[colorIndex][2] * (1 - blend) + colors[nextColorIndex][2] * blend;
                    
                    const brightness = 1 - (iteration / maxIterations);
                    
                    data[pixelIndex] = r * brightness;
                    data[pixelIndex + 1] = g * brightness;
                    data[pixelIndex + 2] = b * brightness;
                    data[pixelIndex + 3] = 220; // Slight transparency
                }
            }
        }
        
        ctx.putImageData(imageData, 0, 0);
    }
    
    // Animate the fractal parameters
    let angle = 0;
    function animate() {
        angle += 0.01;
        const radius = 0.3;
        cReal = -0.7 + Math.cos(angle) * radius;
        cImag = 0.27 + Math.sin(angle) * radius;
        
        drawFractal();
        requestAnimationFrame(animate);
    }
    
    // Start animation
    animate();
}

/**
 * Create particle effect for the header
 */
function createParticleEffect(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    container.appendChild(canvas);
    
    // Set canvas size
    function resize() {
        canvas.width = container.offsetWidth;
        canvas.height = container.offsetHeight;
    }
    
    resize();
    window.addEventListener('resize', resize);
    
    // Particle class
    class Particle {
        constructor() {
            this.reset();
        }
        
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 3 + 1;
            this.speedX = Math.random() * 1 - 0.5;
            this.speedY = Math.random() * 1 - 0.5;
            this.color = getRandomColor();
        }
        
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            
            // Wrap around edges
            if (this.x < 0) this.x = canvas.width;
            if (this.x > canvas.width) this.x = 0;
            if (this.y < 0) this.y = canvas.height;
            if (this.y > canvas.height) this.y = 0;
        }
        
        draw() {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    // Get a random color from the theme
    function getRandomColor() {
        const colors = [
            'rgba(0, 195, 255, 0.5)',  // Blue
            'rgba(52, 232, 158, 0.5)', // Green
            'rgba(15, 52, 67, 0.3)',   // Dark blue
            'rgba(17, 153, 142, 0.4)'  // Teal
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    // Create particles
    const particles = [];
    const particleCount = Math.floor(canvas.width * canvas.height / 10000);
    
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    // Connect particles with lines
    function connectParticles() {
        const maxDistance = 100;
        
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < maxDistance) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(52, 232, 158, ${0.2 * (1 - distance / maxDistance)})`;
                    ctx.lineWidth = 1;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }
    
    // Animation loop
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Update and draw particles
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        connectParticles();
        requestAnimationFrame(animate);
    }
    
    animate();
}

// Register particle effect for header when available
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('header-particles')) {
        createParticleEffect('header-particles');
    }
});
