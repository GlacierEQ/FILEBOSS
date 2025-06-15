"""
Tree generator for file organization

This module handles creating suggested file organization structures
based on file summaries.
"""
import json
import os
from groq import Groq

DEFAULT_PROMPT = """
You will be provided with list of source files and a summary of their contents. For each file, propose a new path and filename, using a directory structure that optimally organizes the files using known conventions and best practices.

If the file is already named well or matches a known convention, set the destination path to the same as the source path.

Your response must be a JSON object with the following schema:
```json
{
    "files": [
        {
            "src_path": "original file path",
            "dst_path": "new file path under proposed directory structure with proposed file name"
        }
    ]
}
```
"""

def create_file_tree(summaries, session=None):
    """
    Create a suggested file tree based on file summaries
    
    Args:
        summaries: List of file summary dictionaries
        session: Optional session for tracking
        
    Returns:
        Dictionary with suggested file organization
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Use mock response for testing if no API key
            print("No GROQ_API_KEY found. Using mock response.")
            return _mock_file_tree(summaries)
        
        client = Groq(api_key=api_key)
        
        summaries_json = json.dumps(summaries)
        
        cmpl = client.chat.completions.create(
            messages=[
                {"content": DEFAULT_PROMPT, "role": "system"},
                {"content": summaries_json, "role": "user"},
            ],
            model="llama-3.1-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0,
        )
        
        result = json.loads(cmpl.choices[0].message.content)
        return result["files"]
        
    except Exception as e:
        print(f"Error in create_file_tree: {e}")
        return _mock_file_tree(summaries)

def _mock_file_tree(summaries):
    """Create a mock file tree for testing or when API calls fail"""
    files = []
    file_types = {
        ".pdf": "Documents/PDFs",
        ".docx": "Documents/Word",
        ".xlsx": "Documents/Excel",
        ".pptx": "Documents/PowerPoint",
        ".txt": "Documents/Text",
        ".jpg": "Images",
        ".jpeg": "Images",
        ".png": "Images",
        ".gif": "Images",
        ".mp3": "Audio",
        ".wav": "Audio",
        ".mp4": "Video",
        ".mov": "Video",
        ".py": "Code/Python",
        ".js": "Code/JavaScript",
        ".html": "Code/HTML",
        ".css": "Code/CSS",
        ".zip": "Archives",
        ".rar": "Archives",
    }
    
    for summary in summaries:
        src_path = summary["file_path"]
        file_name = os.path.basename(src_path)
        extension = os.path.splitext(file_name)[1].lower()
        
        # Determine destination folder based on extension
        dst_folder = file_types.get(extension, "Other")
        dst_path = os.path.join(dst_folder, file_name)
        
        files.append({
            "src_path": src_path,
            "dst_path": dst_path
        })
    
    return files
