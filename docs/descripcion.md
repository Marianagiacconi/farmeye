Descripción del Proyecto

FarmEye - Sistema de Detección de Enfermedades en Gallinas

1. Descripción General

FarmEye es un sistema distribuido que permite la detección de enfermedades en gallinas mediante el análisis de imágenes enviadas por usuarios. Se basa en una arquitectura cliente-servidor utilizando Sockets TCP, multiprocesos, IPC (Inter-Process Communication) y colas de tareas distribuidas para un procesamiento concurrente eficiente.

2. Objetivo del Proyecto

El objetivo es proporcionar a los productores avícolas una herramienta eficiente que les permita detectar enfermedades en gallinas de manera automatizada, utilizando procesamiento de imágenes con inteligencia artificial.

3. Características Principales

Concurrencia: Múltiples clientes pueden enviar imágenes simultáneamente.

Procesamiento en paralelo: Se utilizan multiprocesos para distribuir la carga de trabajo.

IPC (Inter-Process Communication): Uso de memoria compartida y colas de mensajes para coordinación entre procesos.

Asincronismo de I/O: Permite manejar múltiples clientes sin bloquear el servidor.

Colas de tareas distribuidas: Redis se utiliza para almacenar las imágenes a procesar y distribuirlas entre los workers.

Manejo de argument parsing: Se permite la ejecución del cliente con distintos parámetros desde la línea de comandos.

Resultados en tiempo real: Los clientes reciben el diagnóstico una vez completado el procesamiento de la imagen.