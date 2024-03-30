from datetime import datetime

project = 'Fakepilot'
copyright = f"{datetime.now().year}, Carlos Romero Cruz"
author = 'Carlos Romero Cruz'
version = '0.0.1'
release = version

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = ".rst"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "bs4": ("https://beautiful-soup-4.readthedocs.io/en/latest", None),
}



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_theme_options = {
    "description": "Trustpilot scrapping Python package.",
    "github_user": "phoenixsite",
    "github_repo": "fakepilot",
}
html_static_path = ['_static']
