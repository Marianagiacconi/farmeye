FarmEye es un sistema diseñado para ayudar a productores avícolas a detectar enfermedades en gallinas utilizando análisis de imágenes con inteligencia artificial. La arquitectura emplea Sockets TCP para la comunicación Cliente-Servidor y Multiprocesos con Celery para el procesamiento concurrente de imágenes.

Características

- Comunicación Cliente-Servidor con Sockets TCP.
- Procesamiento concurrente con multiprocesos y Celery.
- Uso de IPC (Inter-Process Communication) para la coordinación entre procesos.
- Almacenamiento en PostgreSQL.
- Notificaciones al cliente via Websockets.
- Docker.

