FarmEye - Sistema de Detección de Enfermedades en Gallinas
1. Descripción General
FarmEye es un sistema distribuido que permite la detección de enfermedades en gallinas mediante el análisis de imágenes enviadas por los usuarios. Se basa en una arquitectura cliente-servidor con procesamiento concurrente, utilizando Sockets TCP, WebSockets, Redis, Celery y PostgreSQL para garantizar eficiencia y escalabilidad.

2. Objetivo del Proyecto
El objetivo de FarmEye es proporcionar a los productores avícolas una herramienta automatizada para detectar posibles enfermedades en gallinas a partir del análisis de imágenes, utilizando inteligencia artificial y técnicas de procesamiento distribuido.

3. Características Principales
 - Concurrencia y escalabilidad:
    Permite que múltiples clientes envíen imágenes simultáneamente sin bloquear el servidor.       
    Se usa asyncio en el servidor para manejar conexiones concurrentes de manera eficiente.

- Procesamiento distribuido y en paralelo:
    Se utilizan Colas de tareas en Redis y Celery Workers para distribuir la carga de procesamiento de imágenes.    Los Workers procesan las imágenes en paralelo y envían los resultados al servidor.
- Inter-Process Communication (IPC):
    Uso de multiprocesamiento para mejorar el rendimiento del procesamiento de imágenes.
- Asincronismo de I/O:
    El servidor maneja múltiples clientes sin bloquear la ejecución gracias a WebSockets y Sockets TCP.
- Colas de tareas distribuidas:s
    Redis + Celery permiten la distribución eficiente de tareas entre múltiples Workers.
- Almacenamiento de Resultados:
    Los resultados del análisis se almacenan en PostgreSQL, lo que permite una fácil consulta del historial de imágenes procesadas.
- Manejo de Argumentos por Línea de Comandos:
    Se usa argparse para permitir la ejecución del cliente con distintos parámetros configurables.
- Resultados en Tiempo Real:
    Se utiliza WebSockets para que los clientes reciban notificaciones instantáneas con el diagnóstico cuando el análisis de la imagen ha finalizado.