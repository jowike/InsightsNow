#!/bin/sh
set -e  # Zatrzymuje skrypt w przypadku błędu

echo "Installing R..."
apt-get update && apt-get install -y r-base

echo "Installing strucchange package..."
Rscript -e "install.packages('strucchange', repos='http://cran.r-project.org')"

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies from setup.py..."
cd /app/visual-dashboard  # path inside the container; replace with cd app/visual-dashboard when running locally
python setup.py install

echo "Starting dashboard application..."
exec python app.py  # Uruchamiamy aplikację z katalogu /app/visual-dashboard (working_dir to /app/visual-dashboard)
