import sys
import subprocess


def run_command(command):
    try:
        print(f"Executing: {command}")
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}\nError: {e}")
        sys.exit(1)

def install_packages():
    commands = [
        "pip install kedro",
        "pip install kedro-viz",
        "pip install kedro-datasets",
        "pip install bottleneck",
        "pip install pmdarima",
        "pip install linear-tree",
        "pip install git+https://github.com/jowike/mifs.git@maynard",  # TODO: git clone + git checkout
        "pip install numpy==1.26.4",
        "pip install seaborn",
        "pip install xlsxwriter",
        "pip install openpyxl",
        "pip install pyarrow",
        "pip install fastparquet",
        "pip install -U kaleido",
        "pip install dash-uploader",
        "pip install dash-spa",
        "pip install dash_chartist",
        "pip install dash_loading_spinners",
        "pip install diskcache",
        "pip install shap"
    ]
    for cmd in commands:
        run_command(cmd)

# Environment setup
if __name__ == "__main__":
    install_packages()

