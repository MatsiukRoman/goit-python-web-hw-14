import sys
import os
from unittest.mock import MagicMock
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MOCK_MODULES = ["passlib", "passlib.context", "jose", "jose.jwt"]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

project = 'Rest API'
copyright = '2025, Roman Matsiuk'
author = 'Roman Matsiuk'
release = '0.0.1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx', 
]
autodoc_member_order = 'bysource'
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/latest/', None),
    'fastapi': ('https://fastapi.tiangolo.com/ko/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'nature'
html_static_path = ['_static']