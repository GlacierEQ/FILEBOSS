import os
import shutil
import mimetypes
from flask import Flask, request, jsonify, render_template  # Added render_template
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the frontend

# Initialize OpenAI client with your API key
client = OpenAI(
    api_key="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"
)

# Function to classify file type using AI
def classify_file_with_ai(file_name, context="Classify the file type"):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"{context}: {file_name}"}
            ]
        )
        return completion.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"AI classification failed: {e}")
        return 'unknown'

# Function to categorize files based on MIME type and AI classification
def categorize_file(file_path, custom_rules=None):
    mime_type, _ = mimetypes.guess_type(file_path)
    category = 'Others'
    file_name = os.path.basename(file_path)
    
    if custom_rules and file_name in custom_rules:
        category = custom_rules[file_name]
    elif mime_type:
        if mime_type.startswith('image'):
            category = 'Images'
        elif mime_type.startswith('video'):
            category = 'Videos'
        elif mime_type.startswith('audio'):
            category = 'Audio'
        elif mime_type.startswith('text'):
            category = 'Documents'
        else:
            category = classify_file_with_ai(file_name)
    else:
        category = classify_file_with_ai(file_name)
    
    if category == 'unknown':
        category = 'Common'
    
    return category.capitalize()

# Function to organize files into directories
def organize_directory(directory, custom_rules=None):
    if not os.path.exists(directory):
        return f"Directory {directory} does not exist."
    
    log = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            category = categorize_file(file_path, custom_rules)
            category_dir = os.path.join(directory, category)
            os.makedirs(category_dir, exist_ok=True)
            shutil.move(file_path, os.path.join(category_dir, file))
            log.append(f"Moved {file} to {category}/")
    
    log.append("Directory organized successfully!")
    return "\n".join(log)

# New route to serve the frontend HTML file
@app.route('/')
def home():
    return render_template('mahendra.html')  # Renders mahendra.html from templates folder

# Flask route to handle organization request
@app.route('/organize', methods=['POST'])
def organize():
    data = request.get_json()
    directory = data.get('directory')
    custom_rules = {'example.txt': 'Important', 'notes.docx': 'Work'}  # Example rules
    
    if not directory:
        return jsonify({"message": "Error: No directory specified"}), 400
    
    result = organize_directory(directory, custom_rules)
    return jsonify({"message": result})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
