import asyncio
import json
import os
from collections import defaultdict

import agentops
import colorama
import ollama
import weave
from groq import AsyncGroq, Groq
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.schema import ImageDocument
from llama_index.core.node_parser import TokenTextSplitter
from termcolor import colored


@agentops.record_function("get directory summaries")
async def get_dir_summaries(path: str):
    doc_dicts = load_documents(path)
    # metadata = process_metadata(doc_dicts)

    summaries = await get_summaries(doc_dicts)

    # Convert path to relative path
    for summary in summaries:
        summary["file_path"] = os.path.relpath(summary["file_path"], path)

    return summaries

    # [
    #     {
    #         file_path:
    #         file_name:
    #         file_size:
    #         content:
    #         summary:
    #         creation_date:
    #         last_modified_date:
    #     }
    # ]


@agentops.record_function("load documents")
def load_documents(path: str):
    reader = SimpleDirectoryReader(
        input_dir=path,
        recursive=True,
        required_exts=[
            ".pdf",
            # ".docx",
            # ".py",
            ".txt",
            # ".md",
            ".png",
            ".jpg",
            ".jpeg",
            # ".ts",
        ],
    )
    splitter = TokenTextSplitter(chunk_size=6144)
    documents = []
    for docs in reader.iter_data():
        # By default, llama index split files into multiple "documents"
        if len(docs) > 1:
            # So we first join all the document contexts, then truncate by token count
            for d in docs:
                # Some files will not have text and need to be handled
                contents = splitter.split_text("\n".join(d.text))
                if len(contents) > 0:
                    text = contents[0]
                else:
                    text = ""
                documents.append(Document(text=text, metadata=docs[0].metadata))
        else:
            documents.append(docs[0])
    return documents


@agentops.record_tool("process_metadata")
def process_metadata(doc_dicts):
    file_seen = set()
    metadata_list = []
    for doc in doc_dicts:
        if doc["file_path"] not in file_seen:
            file_seen.add(doc["file_path"])
            metadata_list.append(doc)
    return metadata_list


async def summarize_document(doc, client):
    PROMPT = """
You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": json.dumps(doc)},
                ],
                model="llama-3.1-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0,
            )
            break
        except Exception as e:
            print("Error status {}".format(e.status_code))
            attempt += 1

    summary = json.loads(chat_completion.choices[0].message.content)

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)
        print(summary)

    return summary


async def summarize_image_document(doc: ImageDocument, client):
    PROMPT = """
You will be provided with an image along with its metadata. Provide a summary of the image contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    client = ollama.AsyncClient()
    chat_completion = await client.chat(
        messages=[
            # {"role": "system", "content": "Respond with one short sentence."},
            {
                "role": "user",
                "content": "Summarize the contents of this image.",
                "images": [doc.image_path],
            },
        ],
        model="moondream",
        # format="json",
        # stream=True,
        options={"num_predict": 128},
    )

    summary = {
        "file_path": doc.image_path,
        "summary": chat_completion["message"]["content"],
    }

    # Print the filename in green
    print(colored(summary["file_path"], "green"))
    print(summary["summary"])  # Print the summary of the contents
    # Print a separator line with spacing for readability
    print("-" * 80 + "\n")
    return summary


async def dispatch_summarize_document(doc, client):
    if isinstance(doc, ImageDocument):
        return await summarize_image_document(doc, client)
    elif isinstance(doc, Document):
        return await summarize_document({"content": doc.text, **doc.metadata}, client)
    else:
        raise ValueError("Document type not supported")


async def get_summaries(documents):
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    summaries = await asyncio.gather(
        *[dispatch_summarize_document(doc, client) for doc in documents]
    )
    return summaries


@agentops.record_function("merge")
def merge_summary_documents(summaries, metadata_list):
    list_summaries = defaultdict(list)

    for item in summaries:
        list_summaries[item["file_path"]].append(item["summary"])

    file_summaries = {
        path: ". ".join(summaries) for path, summaries in list_summaries.items()
    }

    file_list = [
        {"summary": file_summaries[file["file_path"]], **file} for file in metadata_list
    ]

    return file_list


################################################################################################
# Non-async versions of the functions                                                        #
################################################################################################


def get_file_summary(path: str):
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
    reader = SimpleDirectoryReader(input_files=[path]).iter_data()

    docs = next(reader)
    splitter = TokenTextSplitter(chunk_size=6144)
    text = splitter.split_text("\n".join([d.text for d in docs]))[0]
    doc = Document(text=text, metadata=docs[0].metadata)
    summary = dispatch_summarize_document_sync(doc, client)
    return summary


def dispatch_summarize_document_sync(doc, client):
    if isinstance(doc, ImageDocument):
        return summarize_image_document_sync(doc, client)
    elif isinstance(doc, Document):
        return summarize_document_sync({"content": doc.text, **doc.metadata}, client)
    else:
        raise ValueError("Document type not supported")


def summarize_document_sync(doc, client):
    PROMPT = """
You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:
    
```json 
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": json.dumps(doc)},
        ],
        model="llama-3.1-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0,
    )
    summary = json.loads(chat_completion.choices[0].message.content)

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)
        print(summary)

    return summary


def summarize_image_document_sync(doc: ImageDocument, client):
    client = ollama.Client()
    chat_completion = client.chat(
        messages=[
            {
                "role": "user",
                "content": "Summarize the contents of this image.",
                "images": [doc.image_path],
            },
        ],
        model="moondream",
        # format="json",
        # stream=True,
        options={"num_predict": 128},
    )

    summary = {
        "file_path": doc.image_path,
        "summary": chat_completion["message"]["content"],
    }

    # Print the filename in green
    print(colored(summary["file_path"], "green"))
    print(summary["summary"])  # Print the summary of the contents
    # Print a separator line with spacing for readability
    print("-" * 80 + "\n")

    return summary


"""
File loader and summarizer for Sorting Hat
"""
import os
import asyncio
from pathlib import Path

async def get_file_summary(file_path):
    """
    Get summary information about a file.
    
    Args:
        file_path: Path to the file to summarize
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return {"file_path": file_path, "summary": "File not found"}
    
    try:
        file_size = os.path.getsize(file_path)
        is_binary = _is_binary(file_path)
        extension = os.path.splitext(file_path)[1].lower()
        
        # For text files, extract a sample
        sample_text = ""
        if not is_binary and file_size < 1024 * 1024:  # Skip files larger than 1MB
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample_text = f.read(2000)  # First 2000 chars as sample
            except Exception:
                sample_text = "Error extracting file content"
        
        rel_path = os.path.basename(file_path)
        
        return {
            "file_path": rel_path,
            "size": file_size,
            "is_binary": is_binary,
            "extension": extension,
            "summary": _generate_summary(rel_path, file_size, extension, is_binary, sample_text)
        }
    except Exception as e:
        return {"file_path": file_path, "summary": f"Error processing file: {str(e)}"}

async def get_dir_summaries(directory):
    """
    Get summaries for all files in a directory.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of file summaries
    """
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, directory)
            if _should_process_file(file_path, rel_path):
                files.append(file_path)
    
    # Process files concurrently
    tasks = [get_file_summary(file) for file in files]
    return await asyncio.gather(*tasks)

def _is_binary(file_path):
    """Check if a file is binary by looking at the first few bytes."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except:
        return True

def _should_process_file(file_path, rel_path):
    """Determine if a file should be processed based on its path."""
    # Skip hidden files and folders
    if rel_path.startswith('.') or '/.git/' in rel_path:
        return False
    
    # Skip common system files
    if rel_path in ['.DS_Store', 'Thumbs.db']:
        return False
        
    try:
        # Skip files we can't access
        if not os.access(file_path, os.R_OK):
            return False
    except:
        return False
        
    return True

def _generate_summary(file_path, file_size, extension, is_binary, sample_text):
    """Generate a human-readable summary of the file."""
    summary = []
    
    # Basic file info
    summary.append(f"Filename: {os.path.basename(file_path)}")
    
    # Size with appropriate unit
    if file_size < 1024:
        summary.append(f"Size: {file_size} bytes")
    elif file_size < 1024 * 1024:
        summary.append(f"Size: {file_size / 1024:.2f} KB")
    else:
        summary.append(f"Size: {file_size / (1024 * 1024):.2f} MB")
    
    # File type info
    summary.append(f"Type: {extension[1:].upper() if extension else 'Unknown'}")
    
    # Content type
    if is_binary:
        summary.append("Content: Binary file")
    else:
        # For text files, add first line as a hint
        if sample_text:
            first_line = sample_text.strip().split('\n')[0][:50]
            if first_line:
                summary.append(f"First line: {first_line}")
    
    # Join all parts with spaces
    return ". ".join(summary)
