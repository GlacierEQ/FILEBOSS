@echo off
echo Creating directories and requirements files...
python create_dirs.py

echo.
echo Installing requirements...
echo.
echo 1. Installing core requirements...
pip install -r requirements.txt

echo.
echo 2. Installing demo requirements...
pip install -r demo/requirements.txt

echo.
echo 3. Installing fine-tuning requirements (without DeepSpeed)...
pip install -r finetune/requirements.txt

echo.
echo 4. Installing evaluation requirements...
pip install -r Evaluation/HumanEval/requirements.txt
pip install -r Evaluation/MBPP/requirements.txt
pip install -r Evaluation/PAL-Math/requirements.txt
pip install -r Evaluation/DS-1000/requirements.txt

echo.
echo 5. Installing une requirements...
pip install -r une/requirements.txt

echo.
echo All requirements installed successfully!
echo.
echo Note: To install DeepSpeed separately (requires additional steps):
echo       pip install deepspeed --no-deps
echo       pip install triton ninja packaging
echo.
pause
