Instalación y Ejecución de FarmEye

Este documento proporciona las instrucciones detalladas para instalar, configurar y ejecutar el sistema FarmEye, que permite la detección de enfermedades en gallinas mediante procesamiento de imágenes concurrente.

- Requisitos del Sistema:

.Python 3.10 o superior

.Redis (para manejo de tareas en Celery)

.PostgreSQL (para almacenamiento de resultados)

 - Bibliotecas necesarias: pip install -r requirements.txt

- Instalación

    - Clonar el repositorio:

        .git clone https://github.com/usuario/farmeye.git
        .cd farmeye

- Crear y activar un entorno virtual:

    .python3 -m venv venv
    .source venv/bin/activate 

- Instalar dependencias:

    .pip install -r requirements.txt

- Configuración de la Base de Datos

    - Crear la base de datos en PostgreSQL:

        .CREATE DATABASE farmeye_db;

        .Configurar la conexión en src/utils/database.py con las credenciales correctas.

- Ejecución del Servidor TCP

    Para iniciar el servidor que recibe imágenes de los clientes:

    .python -m server.server

- Ejecución del Cliente

    Para enviar imágenes al servidor desde el cliente:

    .python src/client/client.py --images src/client/images/image1.webp src/client/images/image2.webp

- Ejecución de Celery y Redis

    Iniciar Redis:

    .redis-server

    Ejecutar el worker de Celery:
    .celery -A src.tasks.celery_config worker --loglevel=info