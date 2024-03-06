# install_deps.py
import subprocess
import os

def install_dependencies():
    # Get the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(script_dir, 'requirements.txt')
    # Navigate up one directory level to the site-packages directory
    target_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

    subprocess.check_call([
        "pip", "install", "-r", requirements_path,
        "--target", target_dir,
        "--upgrade"
    ])

if __name__ == "__main__":
    install_dependencies()
