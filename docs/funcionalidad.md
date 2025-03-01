
**Funcionalidad del Proyecto**
        **Arquitectura del Sistema:**

**Cliente**
- Envía imágenes al servidor a través de Sockets TCP.
- Recibe los resultados del análisis a través de sockets.
- Utiliza argparse para especificar la ruta de la imagen a enviar.
- Permite la consulta del historial de análisis al servidor mediante una solicitud API.

**Servidor**
- Recibe conexiones concurrentes de múltiples clientes usando asyncio.
- Almacena las imágenes en una cola de tareas distribuida en Redis, gestionada con Celery.
- Envía las imágenes a los Workers para su procesamiento.
- Recibe los resultados de los Workers, los almacena en PostgreSQL y notifica al Cliente mediante sockets.
- Expone una API para consultar el historial de imágenes procesadas y sus resultados.

**Procesador de Imágenes (Workers)**
- Extrae las imágenes de la cola de tareas en Redis usando Celery.
- Procesa las imágenes en paralelo, aprovechando multiprocesamiento.
- Utiliza IPC (Inter-Process Communication) para coordinar subtareas del procesamiento.
- Envía los resultados al Servidor, en lugar de escribir directamente en la base de datos.

**Flujo de Trabajo del Sistema**
1. El Cliente selecciona una imagen y la envía al Servidor usando Sockets TCP.
2. El Servidor recibe la imagen y la coloca en la cola de tareas en Redis.
3. Los Workers extraen las imágenes de la cola y procesan la información.
4. Una vez finalizado el análisis, el Worker devuelve el resultado al Servidor.
5. El Servidor guarda el resultado en PostgreSQL y envía una notificación al Cliente mediante WebSockets.
6. El Cliente recibe la notificación y puede consultar el historial de análisis a través de la API.