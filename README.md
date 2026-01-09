# PROYECTO DE AUTOMATIZACIÓN QA: Integrens ERP

**Proyecto:** Integrens_Test_Automation  
**Objetivo:** Inventariar la navegación funcional y mapear la interfaz de usuario (UI) de la aplicación ERP "Integrens" para generar Casos de Prueba estructurados.

---

## 🚀 Quick Start (Inicio Rápido)
Si ya tienes todo configurado, sigue estos pasos para ejecutar la prueba:

1. **Abre la terminal** en la carpeta del proyecto.
2. **Activa el entorno virtual**:
   - PowerShell: `.\venv\Scripts\Activate.ps1`
   - CMD: `.\venv\Scripts\activate.bat`
3. **Ejecuta el robot**:
   ```bash
   python run_inventory.py
   ```
4. **Login**: Espera a que se abra el navegador. Ingresa el CAPTCHA manualmente y dale Login.
5. **Confirma**: Regresa a esta terminal y presiona **ENTER** cuando veas el Dashboard.
6. **Resultados**: Al finalizar, revisa la carpeta `outputs/`.

---

## 📋 Requisitos Previos
- **Python 3.11** o superior instalado.
- **Google Chrome** instalado.
- Acceso a internet para conectar al ERP Integrens.

## ⚙️ Instalación y Configuración (Solo la primera vez)

### 1. Crear Entorno Virtual
Para mantener las dependencias ordenadas, configura un entorno virtual:
```bash
python -m venv venv
```

### 2. Activar Entorno
**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```
**Windows Command Prompt (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

### 3. Instalar Dependencias
Una vez activado el entorno, instala las librerías necesarias:
```bash
pip install -r requirements.txt
```

### 4. Configurar Credenciales (.env)
**MUY IMPORTANTE:** Por seguridad, las claves no están en el código.
1. Crea un archivo nuevo llamado `.env` en la raíz del proyecto.
2. Pega el siguiente contenido reemplazando con tus datos reales:
```ini
INTEGRENS_USER=tu_usuario_aqui
INTEGRENS_PASS=tu_clave_secreta_aqui
```

---

## ✋ Manejo del CAPTCHA
Este proyecto **NO automatiza ni rompe el CAPTCHA** por políticas de seguridad y buenas prácticas.

**El Flujo es Semi-Automático:**
1. El robot abrirá el navegador y llenará tu Usuario y Contraseña automáticamente.
2. **El robot se DETENDRÁ**. Verás un aviso en la consola con un icono de alerta ⚠️.
3. **TU ACCIÓN:** Debes ir al navegador, leer el CAPTCHA y escribirlo manualmente. Luego haz clic en el botón de **Ingresar**.
4. Una vez que hayas entrado exitosamente al sistema (Dashboard visible), vuelve a la consola (pantalla negra) y presiona la tecla **ENTER**.
5. El robot seleccionará automáticamente la **Sucursal** (DACTA SAC 2021...) y comenzará a navegar.

---

## 📂 Resultados (Outputs)
Toda la información recolectada se guarda automáticamente en la carpeta `outputs/`.

| Archivo | Descripción |
| :--- | :--- |
| **inventory.csv** | Archivo Excel/CSV con el listado de todos los menús, botones y enlaces encontrados. Listo para importar a test cases. |
| **inventory.json** | Formato técnico para integración con otros sistemas. |
| **logs/execution.log** | Registro técnico de todo lo que hizo el robot (útil para revisar errores). |

---

## 🔒 Notas de Seguridad
- El archivo `.env` está ignorado por Git para que tus claves nunca se suban a la nube.
- El proyecto solo lee información pública de la UI, no modifica datos en el ERP.
