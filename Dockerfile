# Usar imagen oficial de Python
FROM python:3.12-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer puerto para Render
EXPOSE 10000

# Ejecutar app con Gunicorn para producción
# --bind 0.0.0.0:$PORT usa la variable de entorno PORT de Render
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]