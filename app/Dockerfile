FROM python:3.12
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip
WORKDIR /app/visual-dashboard
RUN python setup.py install
CMD ["python", "app.py"]
