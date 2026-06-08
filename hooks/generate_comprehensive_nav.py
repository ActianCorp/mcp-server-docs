"""
MkDocs hook: regenerate comprehensive-nav-sections.js from docs/.pages before build/serve.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.generate_comprehensive_nav import write_sections_file


def on_config(config, **kwargs):
    docs_dir = Path(config.docs_dir)
    if not docs_dir.is_absolute():
        docs_dir = Path.cwd() / docs_dir
    write_sections_file(docs_dir=docs_dir)
    return config
