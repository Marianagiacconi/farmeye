# **FarmEye** - Detección de Enfermedades en Gallinas  

FarmEye es un sistema diseñado para ayudar a productores avícolas a detectar enfermedades en gallinas mediante el análisis de imágenes con inteligencia artificial. Utiliza una arquitectura distribuida basada en **Sockets TCP, Multiprocesos, Celery y WebSockets** para garantizar procesamiento eficiente y en tiempo real.  

## **Características Principales**  

**Comunicación Cliente-Servidor con Sockets TCP**  
- Permite la transmisión de imágenes desde el cliente al servidor.  
- Manejo eficiente de múltiples conexiones simultáneas.  

**Procesamiento Concurrente con Multiprocesos y Celery**  
- Las imágenes se procesan en paralelo utilizando **multiprocessing**.  
- Se emplea **Celery y Redis** para distribuir la carga de trabajo en Workers.  

**Uso de IPC (Inter-Process Communication)**  
- Coordinación entre procesos para evitar bloqueos y mejorar la eficiencia.  

**Almacenamiento en PostgreSQL**  
- Los resultados de los análisis se guardan en PostgreSQL para futuras consultas.  
- Posibilidad de consultar el historial de imágenes procesadas.  

**Notificaciones al Cliente vía WebSockets**  
- Los clientes reciben actualizaciones en **tiempo real** cuando la predicción ha finalizado.  


## **Uso de FarmEye**  

### **Enviar una imagen para análisis**  
```bash
python3 src/client/client.py --images src/client/images/image1.webp src/client/images/image2.webp
```

### **Consultar el historial de predicciones**  
```bash
python3 src/client/client.py --historial <user_id>
```

### **Iniciar el Servidor**  
```bash
python3 -m server.server
```

### **Iniciar Redis y Celery Worker**  

#### ** Iniciar Redis**
```bash
redis-server
```

#### ** Iniciar el Worker de Celery**
```bash
celery -A src.tasks.celery_config worker --loglevel=info
```

##  **Estructura del Proyecto**  

```
farmeye/
│── src/
│   ├── client/          # Código del cliente
│   ├── server/          # Código del servidor
│   ├── tasks/           # Configuración de Celery y Workers
│   ├── utils/           # Configuración de la base de datos
│── requirements.txt     # Dependencias del proyecto
│── INSTALL.md           # Instrucciones de instalación
│── README.md            # Documentación general
│── INFO.md              # Justificación de diseño
│── TODO.md              # Mejoras futuras
```

## **Requisitos del Sistema**  
- **Python 3.10 o superior**  
- **Redis** (para manejo de tareas en Celery)  
- **PostgreSQL** (para almacenamiento de resultados)  
- **Bibliotecas necesarias** (instalar con `pip install -r requirements.txt`)  
