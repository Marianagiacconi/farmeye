Funcionalidad del Proyecto

1. Arquitectura del Sistema

El sistema está compuesto por los siguientes módulos:

- Cliente

Envía imágenes al servidor a través de Sockets TCP.

Recibe los resultados de la clasificación de las imágenes.

Utiliza argparse para especificar la ruta de la imagen.

- Servidor

Recibe conexiones concurrentes de múltiples clientes.

Coloca las imágenes en una cola de tareas distribuida en Redis.

Devuelve los resultados a los clientes mediante Sockets TCP.

- Procesador de Imágenes (Workers)

Extrae imágenes de la cola distribuida.

Procesa las imágenes en paralelo usando multiprocesamiento.

Utiliza IPC (Inter-Process Communication) para coordinar tareas.

Guarda los resultados en Redis y los envía de vuelta al servidor.

2. Flujo de Trabajo del Sistema

El Cliente selecciona una imagen y la envía al Servidor.

El Servidor recibe la imagen y la almacena en la cola de tareas Redis.

Los Workers procesan las imágenes en paralelo, analizando la información con un modelo de IA.

El Worker almacena el resultado en Redis y lo marca como completado.

El Servidor recupera el resultado y lo envía de vuelta al Cliente.

El Cliente muestra el diagnóstico final en su pantalla.

