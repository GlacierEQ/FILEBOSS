import os

def create_dir_and_file(directory, filename, content):
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create file with content
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Created file: {file_path}")

# Create base requirements.txt if not exists
base_requirements = """# Core dependencies for DeepSeek-Coder
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
"""

# Create the 'une' directory and requirements file
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
gradio>=3.50.0
Pillow>=9.0.0
markdown>=3.4.0
pygments>=2.15.0
pandas>=1.5.0
matplotlib>=3.6.0
seaborn>=0.12.0
scikit-learn>=1.1.0
pebble>=5.0.0
timeout-decorator>=0.5.0
multiprocess>=0.70.14
sympy==1.12
"""

# Create demo requirements.txt
demo_requirements = """# Demo dependencies for DeepSeek-Coder
gradio>=3.50.0
transformers>=4.30.0
torch>=2.0.0
accelerate>=0.20.0
numpy>=1.22.0
Pillow>=9.0.0
markdown>=3.4.0
pygments>=2.15.0
"""

# Create finetune requirements.txt that works better with pre-installed torch
finetune_requirements = """# Fine-tuning requirements for DeepSeek-Coder
transformers>=4.30.0
accelerate>=0.20.0
datasets>=2.10.0
tensorboard>=2.12.0
peft>=0.4.0
bitsandbytes>=0.39.0
safetensors>=0.3.0
pyyaml>=6.0
numpy>=1.22.0
tokenizers==0.14.0
attrdict
tqdm
tensorboardX

# Comment out deepspeed as it requires special installation
# deepspeed>=0.9.0  
# To install deepspeed, run:
# pip install deepspeed --no-deps
# pip install triton ninja packaging
"""

# Create HumanEval requirements
humaneval_requirements = """# HumanEval evaluation dependencies
accelerate>=0.20.0
attrdict>=2.0.1
transformers>=4.30.0
torch>=2.0.0
numpy>=1.22.0
tqdm>=4.64.0
"""

# Create MBPP requirements
mbpp_requirements = """# MBPP evaluation dependencies
accelerate>=0.20.0
attrdict>=2.0.1
transformers>=4.30.0
torch>=2.0.0
tqdm>=4.64.0
numpy>=1.22.0
"""

# Create PAL-Math requirements
palmath_requirements = """# PAL-Math evaluation dependencies
sympy==1.12
pebble>=5.0.0
timeout-decorator>=0.5.0
regex>=2022.1.18
multiprocess>=0.70.14
transformers>=4.30.0
torch>=2.0.0
numpy>=1.22.0
accelerate>=0.20.0
"""

# Create DS-1000 requirements
ds1000_requirements = """# DS-1000 evaluation dependencies
pandas>=1.5.0
matplotlib>=3.6.0
seaborn>=0.12.0
scikit-learn>=1.1.0
numpy>=1.22.0
transformers>=4.30.0
torch>=2.0.0
"""

# Create all directories and files
create_dir_and_file('.', 'requirements.txt', base_requirements)
create_dir_and_file('une', 'requirements.txt', une_requirements)
create_dir_and_file('demo', 'requirements.txt', demo_requirements)
create_dir_and_file('finetune', 'requirements.txt', finetune_requirements)
create_dir_and_file(os.path.join('Evaluation', 'HumanEval'), 'requirements.txt', humaneval_requirements)
create_dir_and_file(os.path.join('Evaluation', 'MBPP'), 'requirements.txt', mbpp_requirements)
create_dir_and_file(os.path.join('Evaluation', 'PAL-Math'), 'requirements.txt', palmath_requirements)
create_dir_and_file(os.path.join('Evaluation', 'DS-1000'), 'requirements.txt', ds1000_requirements)

print("\nAll directories and requirements files have been created successfully!")
print("\nTo install the 'une' requirements, run:")
print("    pip install -r une/requirements.txt")
print("\nNOTE: For DeepSpeed installation, run:")
print("    pip install deepspeed --no-deps")
print("    pip install triton ninja packaging")
