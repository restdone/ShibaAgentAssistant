import os
from pathlib import Path
from flask import Flask

PORT = 1990
BASE_DIR = Path(os.path.expanduser("~/Shiba/server_files"))
BASE_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
