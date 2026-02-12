# Usa Python base
FROM python:3.11-slim

# Copiamos solo requirements para aprovechar la cache de Docker
COPY requirements.txt .

# Instalamos dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto de Streamlit
EXPOSE 8501

# Comando por defecto para arrancar Streamlit
# Nota: no necesita copiar app.py porque lo montaremos con volumes
CMD ["streamlit", "run", "/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
