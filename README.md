# Calculo-Apoyos-Elastomericos
# Calculadora de Apoyos Elastoméricos - BridgeBearing PRO 2026

Aplicación web desarrollada con **Streamlit** para el cálculo y verificación de apoyos elastoméricos de neopreno en estructuras de puentes, siguiendo las directrices normativas de la **UNE-EN 1337-3** (Aparatos de apoyo elastoméricos) y la **UNE-EN 1993-1-1** (Eurocódigo 3).

## 💡 Características Principales

*   **Modos de Cálculo:** Estándar (EN 1337-3) y Sísmico (EN 15129).
*   **Tipos de Apoyo:** Tipos A, B, C y Aisladores Sísmicos (LRB, HDRB).
*   **Materiales Normalizados:** Bases de datos integradas para aceros (S235JR, S275JR, S355JR) y elastómeros (Caucho Natural y Cloropreno).
*   **Verificaciones Automáticas:** Comprobaciones de deformación límite, espesor mínimo de zunchos y deslizamiento.

## 🛠️ Instalación y Uso Local

Para ejecutar esta aplicación en tu entorno local, sigue estos pasos:

1.  **Clona el repositorio:**
    ```bash
    git clone github.com
    cd Calculo-Apoyos-Elastom-ricos-
    ```

2.  **Instala las dependencias:**
    Asegúrate de tener Python instalado. Luego, instala las bibliotecas necesarias usando el archivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecuta la aplicación:**
    ```bash
    streamlit run app.py
    ```
    La aplicación se abrirá automáticamente en tu navegador web.

## ☁️ Despliegue en la Nube

Esta aplicación está diseñada para ser desplegada fácilmente en **Streamlit Community Cloud** (share.streamlit.io).

## 📄 Archivos Clave

*   `app.py`: Contiene toda la lógica de la interfaz de usuario y los cálculos normativos.
*   `config.toml`: Archivo de configuración para personalizar el tema y los colores de la interfaz.
*   `requirements.txt`: Lista de dependencias de Python necesarias.
*   `mres_logo.png`: Imagen utilizada para la cabecera y la marca de agua.

---
