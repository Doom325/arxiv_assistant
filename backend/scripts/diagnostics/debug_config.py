import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
from config import settings

print(f"CWD: {os.getcwd()}")
print(f"ENV PDF_SAVE_DIR: {os.environ.get('PDF_SAVE_DIR')}")
print(f"Settings PDF_SAVE_DIR: {settings.PDF_SAVE_DIR}")
