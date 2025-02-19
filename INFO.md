1. Arquitectura Concurrente

El sistema maneja múltiples solicitudes de análisis simultáneamente mediante multiprocesos y colas de tareas distribuidas con Celery. Se usa Redis como message broker para distribuir tareas de procesamiento de imágenes.

2. Comunicación Cliente-Servidor

Se utiliza Sockets TCP para permitir que múltiples clientes envíen imágenes al servidor y reciban los resultados de manera eficiente.

3. Procesamiento de Imágenes con Celery

Cada imagen se procesa en un worker de Celery independiente para optimizar el rendimiento y permitir escalabilidad horizontal.

4. Almacenamiento de Datos en PostgreSQL

Los resultados se guardan en PostgreSQL, permitiendo la persistencia de datos y futuras consultas sobre los diagnósticos.