















































































































































































































































































































































































































































































if __name__ == '__main__':
  main()
+ import csv
+ import io
+
+ output = io.StringIO()
+ writer = csv.writer(output)
+
+ # Header
+ writer.writerow([
+     'File', 'Line', 'Content', 'Priority',
+     'Category', 'Assignee', 'Due Date'
+ ])
+
+ # Data
+ for todo in todos:
+     writer.writerow([
+         todo.file_path,
+         todo.line_number,
+         todo.content,
+         todo.priority,
+         todo.category or '',
+         todo.assignee or '',
+         todo.due_date or ''
+     ])
+
+ return output.getvalue()
+
+ def scan_directory(directory: str) -> List[str]:
+     return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
+
+ def query_ai(prompt: str) -> str:
+     ollama_endpoint = 'http://localhost:11434/api/generate'
+     # Check if endpoint is accessible
+     health_check = requests.get('http://localhost:11434')
+     if health_check.status_code != 200 or 'ollama' not in health_check.text.lower():
+         return 'Ollama server not running or misconfigured. Start Ollama and ensure endpoint is correct.'
+     response = requests.post(ollama_endpoint, json={"model": "llama3", "prompt": prompt})
+     if response.status_code == 200:
+         return response.text
+     elif response.status_code == 404:
+         return 'AI endpoint not found. Check Ollama configuration.'
+     else:
+         return f'AI query failed with status code {response.status_code}'
+
+ def main():
+     files = scan_directory('.')
+     ai_suggestion = query_ai('Suggest sorting and renaming strategies for files: ' + str(files))
+     print(ai_suggestion)
+
+ if __name__ == '__main__':
+     main()
