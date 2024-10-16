import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

project_name = "introlix_api"

list_of_files = [
    f"src/{project_name}/components/__init__.py",
    f"src/{project_name}/components/data_ingestion.py",
    f"src/{project_name}/components/data_transformation.py",
    f"src/{project_name}/components/data_pusher.py",
    f"src/{project_name}/exception/__init__.py",
    f"src/{project_name}/logger/__init__.py",
    f"src/{project_name}/pipeline/__init__.py",
    f"src/{project_name}/pipeline/common_pipeline.py",
    f"src/{project_name}/pipeline/periodic_pipeline.py",
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/common.py",
    f"src/{project_name}/ml/__init__.py",
    f"src/{project_name}/ml/model.py",
    f"src/{project_name}/app/spider/__init__.py",
    f"src/{project_name}/app/routes/__init__.py",
    f"src/{project_name}/app/routes/auth.py",
    f"src/{project_name}/app/database.py",
    f"src/{project_name}/app/model.py",
    f"src/{project_name}/app/appwrite.py",
    "tests/__init__.py",
    "tests/test_app.py",
    "tests/test_components.py",
    "tests/test_pipeline.py",
    "docs/requirements.md",
    "docs/design.md",
    ".github/workflows/ci.yml",
    "main.py",
    "demo.py",
    "requirements.txt",
    "requirements-dev.txt",
    "Dockerfile",
    "setup.py",
    ".dockerignore",
    ".gitignore",
    ".env",
    "README.md",
]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir:
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir} for file: {filename}")
        
    if not filepath.exists() or filepath.stat().st_size == 0:
        with open(filepath, "w") as f:
            pass
        logging.info(f"Created file: {filename}")
    else:
        logging.info(f"{filename} already exists")
