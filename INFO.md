# Informe Técnico de FarmEye

**Arquitectura Concurrente**
- Se utiliza **Sockets TCP** en el servidor para manejar múltiples clientes simultáneamente.
- Cada conexión de cliente se maneja en un **Thread** separado para evitar bloqueos.
- Se usa **Multiprocessing** con Celery para procesar imágenes en paralelo.

**Comunicación Cliente-Servidor**
- **Sockets TCP** permiten conexiones persistentes y eficientes entre clientes y servidor.
- **Multiprocessing Queue** se usa para enviar predicciones desde los Workers al servidor sin bloquearlo.

**Procesamiento de Imágenes con Celery**
- Redis actúa como **message broker** para distribuir las tareas de procesamiento.
- Los **Celery Workers** procesan las imágenes en paralelo para mejorar el rendimiento y escalabilidad.

**Almacenamiento de Datos en PostgreSQL**
- PostgreSQL almacena los resultados de los análisis de imágenes.
- Se diseñó un modelo de datos basado en imágenes y predicciones, permitiendo consultar diagnósticos por usuario.

**Elección de Multiproceso en Lugar de Multithread**
- **Multiprocessing** se usa para manejar tareas pesadas como el análisis de imágenes.
- **Threads** solo se utilizan para gestionar conexiones de clientes en el servidor.

