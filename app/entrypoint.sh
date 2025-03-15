#!/bin/sh
set -e  # Zatrzymuje skrypt w przypadku błędu

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies from setup.py..."
cd /app/visual-dashboard
python setup.py install

echo "Starting dashboard application..."
exec python app.py  # Uruchamiamy aplikację z katalogu /app/visual-dashboard (working_dir to /app/visual-dashboard)
