# GymSystem Pro 🏋️‍♂️

Sistema integral de gestión para gimnasios que combina control de acceso biométrico (Hikvision), gestión de miembros, planes de membresía y un punto de venta (POS) robusto.

## ✨ Características Principales

-   **Control de Acceso Hikvision**: Integración profunda con terminales de reconocimiento facial Hikvision a través de ISAPI.
    -   Sincronización automática de miembros.
    -   Enrolamiento facial directo desde la aplicación.
    -   Monitor de eventos en tiempo real.
    -   Apertura de puertas remota.
-   **Gestión de Miembros**: Registro completo, historial de membresías y estado de acceso.
-   **Planes de Membresía**: Configuración flexible de planes (diarios, mensuales, anuales, corporativos) con colores personalizables.
-   **Punto de Venta (POS)**: Venta de productos y suplementos vinculada a los miembros.
-   **Reportes y Dashboard**: Estadísticas de asistencia, ventas y métricas clave en tiempo real.

## 🚀 Tecnologías Utilizadas

-   **Backend**: Python, FastAPI, SQLAlchemy, SQLite (o PostgreSQL).
-   **Frontend**: React, TypeScript, Tailwind CSS, Vite.
-   **Integración**: Hikvision ISAPI (Protocolo propietario).
-   **Servidor de Eventos**: Node.js / Python.

## 🛠️ Instalación y Configuración

### Requisitos Previos
-   Python 3.10+
-   Node.js 18+
-   Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/jcgonzalez01/gimnasio.git
cd gimnasio
```

### 2. Configuración del Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuración del Frontend
```bash
cd ../frontend
npm install
```

### 4. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto (o dentro de la carpeta `backend`) basado en la configuración de `app/core/config.py`.

## 🏃‍♂️ Ejecución

El proyecto incluye un script de inicio rápido para Windows:

```bash
# Ejecutar desde la raíz del proyecto
./start-all.bat
```

Este script iniciará:
1.  **Backend** en `http://localhost:8001` (Puerto 8001 para evitar conflictos con servicios del sistema).
2.  **Frontend** en `http://localhost:5173`
3.  **Monitor de Eventos** para dispositivos Hikvision.

## 🚀 Novedades de esta Versión (v1.2)

### ⚙️ Infraestructura y Red
-   **Migración de Puerto**: El backend ahora corre por defecto en el puerto **8001** para eliminar interferencias con procesos antiguos y asegurar una conexión limpia.
-   **Seguridad de Red**: Configuración del servidor para escuchar en todas las interfaces (`0.0.0.0`), permitiendo la comunicación directa con hardware Hikvision en la red local.

### 📸 Estabilización Hikvision
-   **Modo Push Activo**: Configuración automática del terminal para enviar eventos al servidor al instante, sin esperas.
-   **Sincronización Horaria**: Herramientas para igualar la fecha, hora y zona horaria entre el PC y el hardware.
-   **Monitor Robusto**: Nuevo motor de monitoreo basado en números de secuencia (Serial Number) que ignora desajustes de reloj.

### 📊 Mejoras en Dashboard y Reportes
-   **Regla de las 4 Horas**: El contador de "Entradas Hoy" ahora es más real; múltiples entradas de un mismo socio en un lapso menor a 4 horas cuentan como una sola visita.
-   **Contador de Aperturas Manuales**: Nueva métrica para auditar cuántas veces se abrió la puerta desde el software.
-   **Dashboard Limpio**: La sección de "Recién Llegados" ahora muestra una sola foto por ID, priorizando el ingreso más reciente.
-   **Formato 24H**: Unificación de toda la interfaz al formato de hora de 24 horas.

## 📸 Control de Acceso (Hikvision)

Para que el sistema se comunique con los dispositivos:
1.  Configura la IP, puerto, usuario y contraseña del dispositivo en la sección **Dispositivos** de la aplicación.
2.  Asegúrate de que el backend sea accesible por el dispositivo para la recepción de eventos (Webhooks/Listen Service).

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
