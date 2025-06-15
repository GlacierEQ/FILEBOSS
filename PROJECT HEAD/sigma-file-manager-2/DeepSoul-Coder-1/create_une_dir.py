import os

# Create une directory if it doesn't exist
une_dir = 'une'
if not os.path.exists(une_dir):
    os.makedirs(une_dir)
    print(f"Created directory: {une_dir}")
else:
    print(f"Directory {une_dir} already exists")

# Create une requirements file
une_requirements = """# Une requirements for DeepSeek-Coder
# This is a merged requirements file containing dependencies from all components
transformers>=4.30.0
torch>=2.0.0
accelerate>=0.20.0
attrdict>=2.0.1
numpy>=1.22.0
tqdm>=4.64.0
huggingface-hub>=0.16.0
pyyaml>=6.0
filelock>=3.9.0
regex>=2022.1.18
packaging>=20.0
requests>=2.28.0
# Demo dependencies
gradio>=3.50.0
Pillow>=9.0.0
markdown>=3.4.0
pygments>=2.15.0
# Data science dependencies
pandas>=1.5.0
matplotlib>=3.6.0
seaborn>=0.12.0
scikit-learn>=1.1.0
# PAL-Math dependencies
pebble>=5.0.0
timeout-decorator>=0.5.0
multiprocess>=0.70.14
sympy==1.12  # Note: Using 1.12 for compatibility with special evaluations
"""

# Write the requirements file
requirements_path = os.path.join(une_dir, 'requirements.txt')
with open(requirements_path, 'w') as f:
    f.write(une_requirements)
print(f"Created file: {requirements_path}")

print("\nTo install the une requirements, run:")
print("    pip install -r une/requirements.txt")

# Also create a simple batch script to run this command
bat_content = """@echo off
echo Installing une requirements...
pip install -r une/requirements.txt
pause
"""

with open('install_une_requirements.bat', 'w') as f:
    f.write(bat_content)
print("Created install_une_requirements.bat script")
