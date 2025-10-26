# Usa una imagen base de Python oficial
FROM python:3.10-slim

# Establece variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala las dependencias del sistema necesarias para psycopg (PostgreSQL)
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos e instálalos
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia el resto del código del backend al directorio de trabajo
COPY . .

# Expone el puerto en el que correrá Gunicorn
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "claro_project.wsgi:application", "--bind", "0.0.0.0:8000"]