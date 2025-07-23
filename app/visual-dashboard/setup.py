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
        "pip install kedro==0.19.9",
        "pip install kedro-viz==10.1.0",
        "pip install kedro-datasets==6.0.0",
        "pip install bottleneck==1.4.0",
        "pip install numpy==1.26.4",
        "pip install pmdarima==2.0.4",
        "pip install linear-tree==0.3.5",
        "pip install git+https://github.com/jowike/mifs.git@maynard",
        "pip install numpy==1.26.4",
        "pip install seaborn==0.12.2",
        "pip install xlsxwriter==3.2.2",
        "pip install openpyxl==3.1.5",
        "pip install pyarrow==18.0.0",
        "pip install fastparquet==2024.5.0",
        "pip install -U kaleido==0.2.1",
        "pip install dash-uploader==0.6.1",
        "pip install dash-spa==1.1.5",
        "pip install dash_chartist==0.0.5",
        "pip install dash_loading_spinners==1.0.3",
        "pip install dash==2.11.1",
        "pip install diskcache==5.6.3",
        "pip install shap==0.47.0",
        "pip install rpy2==3.5.11",
        "pip install scipy==1.11.4"
    ]
    for cmd in commands:
        run_command(cmd)


# Environment setup
if __name__ == "__main__":
    install_packages()
