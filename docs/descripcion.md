**Funcionalidad del Proyecto**

## **Arquitectura del Sistema:**

### **Cliente**
- Envía imágenes al servidor a través de **Sockets TCP**.
- Recibe los resultados del análisis mediante **Sockets TCP**.
- Utiliza **argparse** para especificar la ruta de las imágenes a enviar o consultar el historial de análisis.
- Mantiene la conexión con el servidor hasta recibir todas las respuestas.
- Puede consultar el historial de imágenes procesadas enviando una solicitud al servidor.

### **Servidor**
- Maneja múltiples conexiones de clientes usando **Threads** para concurrencia.
- Recibe imágenes y las guarda en el sistema de archivos.
- Almacena las imágenes en una **cola de tareas en Redis**, gestionada con **Celery**.
- Envía las imágenes a los **Workers** para su procesamiento asincrónico.
- Recibe los resultados de los Workers y los guarda en **PostgreSQL**.
- Notifica a los clientes cuando el resultado está listo mediante **Sockets TCP**.
- Usa **multiprocessing** para gestionar el guardado de predicciones en la base de datos sin bloquear el servidor.
- Permite a los clientes consultar el historial de imágenes procesadas y sus resultados.

### **Procesador de Imágenes (Workers)**
- Extrae las imágenes de la **cola de tareas en Redis** usando **Celery**.
- Procesa las imágenes en paralelo utilizando **multiprocesamiento**.
- Simula un análisis de imágenes y genera un resultado con un porcentaje de confianza.
- Publica los resultados en un canal de **Redis Pub/Sub** para que el servidor los reciba y notifique a los clientes.

## **Flujo de Trabajo del Sistema**

1. **El Cliente** selecciona una o más imágenes y las envía al **Servidor** usando **Sockets TCP**.
2. **El Servidor** recibe las imágenes, las guarda en el sistema de archivos y las coloca en la **cola de tareas en Redis**.
3. **Los Workers** extraen las imágenes de la cola y realizan el procesamiento.
4. **Una vez finalizado el análisis**, el Worker publica el resultado en **Redis Pub/Sub**.
5. **El Servidor** recibe el resultado desde Redis y lo guarda en **PostgreSQL** usando un proceso separado con **multiprocessing**.
6. **El Servidor** notifica al cliente enviándole los resultados mediante **Sockets TCP**.
7. **El Cliente** recibe la notificación y, si lo desea, puede consultar el historial de análisis enviando una solicitud al servidor.

## **Tecnologías utilizadas:**
- **Sockets TCP**: Comunicación entre el cliente y el servidor.
- **Threads**: Manejo de múltiples clientes en el servidor.
- **Multiprocessing**: Guardado asincrónico de resultados en la base de datos.
- **Celery + Redis**: Cola de tareas para procesamiento de imágenes.
- **PostgreSQL + SQLAlchemy**: Almacenamiento de imágenes y predicciones.
- **Argparse**: Configuración de argumentos en el cliente.
- **Pub/Sub de Redis**: Comunicación entre los Workers y el Servidor.

