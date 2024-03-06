# install_deps.py
import subprocess
import os

def install_dependencies():
    # Get the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one directory level to the site-packages directory
    target_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

    dependencies = [
        "certifi>=2024.2.2",
        "isodate>=0.6.1",
        "python-dateutil>=2.9.0.post0",
        "simscale-sdk @ git+https://github.com/SimScaleGmbH/simscale-python-sdk.git@6.0.0",
        "six>=1.16.0",
        "urllib3>=2.2.1",
    ]

    for dep in dependencies:
        subprocess.check_call([
            "pip", "install", dep,
            "--target", target_dir
        ])

if __name__ == "__main__":
    install_dependencies()
