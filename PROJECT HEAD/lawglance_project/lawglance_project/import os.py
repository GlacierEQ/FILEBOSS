import os
import re
import difflib
import docx
from docx.shared import Pt, RGBColor
import docx.enum.text as text
from docx.enum.style import WD_STYLE_TYPE
try:
    import win32com.client
    import pythoncom
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
