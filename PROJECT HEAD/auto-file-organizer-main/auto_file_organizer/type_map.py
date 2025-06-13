# These are the rules to sort the files using type.

TYPE_RULES = {
    "Images": {
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
        "subfolders": {}
    },
    "Videos": {
        "extensions": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"],
        "subfolders": {}
    },
    "Audios": {
        "extensions": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
        "subfolders": {}
    },
    "Documents": {
        "extensions": [".txt"],
        "subfolders": {
            "Word": {
                "extensions": [".doc", ".docx"],
                "subfolders": {}
            },
            "PDF": {
                "extensions": [".pdf"],
                "subfolders": {}
            },
            "Presentations": {
                "extensions": [".ppt", ".pptx"],
                "subfolders": {}
            },
            "Excel": {
                "extensions": [".xls", ".xlsx"],
                "subfolders": {
                    "CSV": {
                        "extensions": [".csv"],
                        "subfolders": {}
                    }
                }
            },
        }
    },
    "Archives": {
        "extensions": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "subfolders": {}
    },
    "Code": {
        "extensions": [".py", ".js", ".html", ".css", ".cpp", ".c", ".java", ".sh", ".bat", ".ts"],
        "subfolders": {
            "Python": {
                "extensions": [".py"],
                "subfolders": {
                    "Scripts": {
                        # You can refine this more later
                        "extensions": [".py"],
                        "subfolders": {}
                    }
                }
            },
            "JavaScript": {
                "extensions": [".js", ".ts"],
                "subfolders": {}
            },
            "HTML/CSS": {
                "extensions": [".html", ".css"],
                "subfolders": {}
            },
            "C and C++": {
                "extensions": [".c", ".cpp"],
                "subfolders": {}
            },
            "Java": {
                "extensions": [".java"],
                "subfolders": {}
            },
            "Shell Scripts": {
                "extensions": [".sh", ".bat"],
                "subfolders": {}
            }
        }
    },
    "Executables": {
        "extensions": [".exe", ".msi", ".apk", ".app"],
        "subfolders": {}
    },
    "Fonts": {
        "extensions": [".ttf", ".otf", ".woff", ".woff2"],
        "subfolders": {}
    }
}
