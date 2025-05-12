"""
Configuration file for the Sphinx documentation.
"""

# SPDX-License-Identifier: MIT

import os
import sys
from importlib.metadata import version as get_version

sys.path.insert(0, os.path.abspath("../.."))

project = "fakepilot"
copyright = "Carlos Romero Cruz"
author = "Carlos Romero Cruz"
version = get_version("fakepilot")
release = version
templates_path = ["_templates"]
exclude_patterns = []
exclude_trees = ["_build"]
source_suffix = ".rst"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "notfound.extension",
    "sphinx.ext.viewcode",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "bs4": ("https://beautiful-soup-4.readthedocs.io/en/latest", None),
}

html_theme = "furo"

# Spelling check needs an additional module that is not installed by default.
# Add it only if spelling check is requested so docs can be generated without
# it.
if "spelling" in sys.argv:
    extensions.append("sphinxcontrib.spelling")


spelling_lang = "en_US"
spelling_word_list_filename = "spelling_wordlist.txt"
spelling_ignore_contributor_names = False

# OGP metadata configuration.
ogp_enable_meta_description = True
ogp_site_url = "https://fakepilot.readthedocs.io/"
