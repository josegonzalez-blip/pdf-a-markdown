import os
import tempfile
import streamlit as st
from markitdown import MarkItDown

# =====================================================================
# Configuracion de la pagina
# =====================================================================
st.set_page_config(
    page_title="Assetplan · PDF a Markdown",
    page_icon="🏢",
    layout="centered",
)

# =====================================================================
# 🎨 COLORES OFICIALES ASSETPLAN + estilos
# =====================================================================
COLOR_PRINCIPAL  = "#2B7FFF"   # Azul primario Assetplan
COLOR_ACENTO     = "#4285F4"   # Azul acento
COLOR_AZUL_CLARO = "#BACCE3"   # Azul claro (bordes)
COLOR_GRIS       = "#5F6B7A"   # Texto atenuado
COLOR_FONDO      = "#F5F8FC"   # Fondo suave

st.markdown(
    f"""
    <style>
    .stApp {{ font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif; }}

    /* Titulo principal en azul de marca */
    h1 {{ color: {COLOR_PRINCIPAL} !important; }}

    /* Boton principal Assetplan */
    .stButton > button {{
        background-color: {COLOR_PRINCIPAL};
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 600;
        font-size: 15px;
    }}
    .stButton > button:hover {{
        filter: brightness(92%);
        color: #FFFFFF;
    }}

    /* Boton de descarga */
    .stDownloadButton > button {{
        background-color: {COLOR_ACENTO};
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        font-weight: 600;
    }}

    /* Zona de carga de archivos */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {COLOR_FONDO};
        border: 2px dashed {COLOR_AZUL_CLARO};
        border-radius: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Motor de conversion de Microsoft
md = MarkItDown()

# =====================================================================
# Encabezado
# =====================================================================
st.title("🏢 Herramienta Interna de Optimización Documental")
st.markdown(
    f"<p style='color:{COLOR_GRIS}; font-size:17px; margin-top:-8px;'>"
    "Transforma tus PDFs a Markdown estructurado para ahorrar hasta un 70% "
    "de tokens en Claude</p>",
    unsafe_allow_html=True,
)
st.divider()

# =====================================================================
# Paso 1: cargar el PDF
# =====================================================================
st.subheader("1. Carga tu documento")
archivo = st.file_uploader(
    "Arrastra tu PDF aquí o haz clic para subirlo",
    type=["pdf"],
)

# =====================================================================
# Paso 2: convertir y descargar
# =====================================================================
if archivo is not None:
    if st.button("Optimizar y Convertir 🚀"):
        with st.spinner("Convirtiendo tu documento..."):
            try:
                # Guardamos el PDF subido en un archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(archivo.read())
                    ruta_tmp = tmp.name

                # Conversion con MarkItDown
                resultado = md.convert(ruta_tmp)
                texto_md = resultado.text_content
                os.unlink(ruta_tmp)  # limpiamos el temporal

                nombre_base = os.path.splitext(archivo.name)[0]
                nombre_salida = f"{nombre_base}.md"

                st.success(f"✅ ¡Éxito! El archivo '{nombre_salida}' está listo para Claude.")

                st.subheader("2. Descarga el resultado")
                st.download_button(
                    label="📥 Descargar archivo .md",
                    data=texto_md,
                    file_name=nombre_salida,
                    mime="text/markdown",
                )

                with st.expander("👁️ Ver el contenido convertido"):
                    st.text(texto_md)

            except Exception as e:
                st.error(f"❌ Error en el proceso: {str(e)}")
else:
    st.info("Sube un archivo PDF para comenzar.")
