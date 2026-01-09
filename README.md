# Integrens Test Automation

## Objetivo
Proyecto de automatización de QA para inventariar la navegación funcional y mapeo de UI de la aplicación ERP "Integrens".
Genera archivos CSV/JSON listos para crear Casos de Prueba.

## Requisitos
- Python 3.11+
- Google Chrome instalado

## Instalación

1. Crear un entorno virtual (recomendado):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración (.env)
**IMPORTANTE**: Debes crear un archivo `.env` en la raíz del proyecto para tus credenciales. Este archivo NO se sube al repositorio.

Contenido de `.env`:
```ini
INTEGRENS_USER=tu_usuario
INTEGRENS_PASS=tu_clave
```

## Ejecución
```bash
python run_inventory.py
```

## Flujo de Login y CAPTCHA
La aplicación tiene un CAPTCHA que NO se automatiza.
1. El script abrirá el navegador y llenará usuario/clave.
2. El script se PAUSARÁ y te pedirá en la consola que resuelvas el CAPTCHA manualmente.
3. Una vez logueado, presiona ENTER en la consola para continuar.
4. El script validará el login y comenzará el inventario.

## Outputs
Los resultados se guardan en la carpeta `outputs/`:
- `inventory.csv` / `inventory.json`: Mapeo de la UI.
- `logs/`: Logs de ejecución.
