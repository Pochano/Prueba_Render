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

# Exponer puerto (opcional)
EXPOSE 5000

# Ejecutar app con Gunicorn usando el puerto asignado por Render
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]