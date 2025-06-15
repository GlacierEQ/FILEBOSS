# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the project root directory to the path so we can import the package
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'DeepSeek-Coder'
copyright = '2024, DeepSeek AI'
author = 'DeepSeek AI Team'
release = '1.0.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'myst_parser',
    'nbsphinx',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv', '.env', 'venv', 'env']

# HTML output configuration
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '../pictures/logo.png'
html_favicon = '../pictures/logo.png'

# Theme options
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'style_nav_header_background': '#343131',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Extension configuration
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# MyST parser configuration
myst_enable_extensions = [
    'colon_fence',
    'deflist',
    'dollarmath',
    'html_image',
]
myst_heading_anchors = 3

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'torch': ('https://pytorch.org/docs/stable', None),
    'transformers': ('https://huggingface.co/transformers/master', None),
}
