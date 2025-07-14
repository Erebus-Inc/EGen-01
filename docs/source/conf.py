# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'EGen Platform'
copyright = '2025, ErebusTN'
author = 'EGen Development Team'
release = '1.0.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Extension configurations
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
napolean_use_param = True
napolean_use_rtype = True

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'torch': ('https://pytorch.org/docs/stable/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}