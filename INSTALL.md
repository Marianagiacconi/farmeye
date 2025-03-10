# Instalación y Ejecución de FarmEye  

Este documento proporciona instrucciones detalladas para instalar, configurar y ejecutar **FarmEye**, un sistema distribuido para la detección de enfermedades en gallinas mediante procesamiento concurrente de imágenes.

## **Requisitos del Sistema**
- **Python** 3.10 o superior  
- **Redis** (para manejo de tareas en Celery)  
- **PostgreSQL** (para almacenamiento de resultados)  

## **Instalación**  

### **Clonar el Repositorio**  
```bash
git clone https://github.com/Marianagiacconi/farmeye.git
cd farmeye
```

### **Crear y Activar un Entorno Virtual**  
```bash
python3 -m venv venv
source venv/bin/activate
```

### **Instalar Dependencias**  
```bash
pip install -r requirements.txt
```

## **Configuración de la Base de Datos**  

### **Crear la base de datos en PostgreSQL**  
Abre PostgreSQL e ingresa:  
```sql
CREATE DATABASE farmeye_db;
```

###  **Configurar la Conexión**  
Edita el archivo `src/utils/database.py` y ajusta las credenciales de la base de datos según tu configuración.


## **Ejecución del Servidor**  
Para iniciar el servidor que recibe imágenes de los clientes:  
```bash
python3 -m server.server
```

## **Ejecución del Cliente**  
Para enviar imágenes al servidor desde el cliente:  
# IPV6: 
```bash
 python3 src/client/client.py --images src/client/images/image1.webp --host fe80::d25:d801:69ca:92b1%wlp0s20f3 --port 5000
```
# IPV4: 
```bash
python3 src/client/client.py --images src/client/images/image1.webp 
```
Para consultar el historial de predicciones:  
```bash
python3 src/client/client.py --historial <user_id>
```
## **Ejecución de Celery y Redis**  

### **Iniciar Redis**  
```bash
redis-server
```

### **Ejecutar el Worker de Celery**  
```bash
celery -A src.tasks.celery_config worker --loglevel=info
```

### ***VM **
# VM MULTIPASS: 
multipass shell cliente-vm

# Activar Multipass shell:
multipass start cliente-vm
