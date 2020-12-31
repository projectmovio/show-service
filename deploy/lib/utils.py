import os
import shutil

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(CURRENT_DIR, "..", "..")


def clean_pycache():
    for root, dirs, files in os.walk(ROOT_DIR):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
        for f in files:
            if ".so" in f:
                os.remove(os.path.join(root, f))
