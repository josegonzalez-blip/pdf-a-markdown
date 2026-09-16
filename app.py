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
    h1 {{ color: {COLOR_PRINCIPAL} !important; }}
    .stButton > button {{
        background-color: {COLOR_PRINCIPAL};
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 600;
        font-size: 15px;
    }}
    .stButton > button:hover {{ filter: brightness(92%); color: #FFFFFF; }}
    .stDownloadButton > button {{
        background-color: {COLOR_ACENTO};
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        font-weight: 600;
    }}
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
# OCR: leer PDFs escaneados (imagenes) pagina por pagina
# =====================================================================
def ocr_pdf(pdf_bytes):
    """Convierte cada pagina del PDF a imagen y le aplica OCR en espanol."""
    from pdf2image import convert_from_bytes, pdfinfo_from_bytes
    import pytesseract

    info = pdfinfo_from_bytes(pdf_bytes)
    total_paginas = info["Pages"]

    partes = []
    barra = st.progress(0, text="Aplicando OCR (leyendo las imágenes)...")

    for i in range(1, total_paginas + 1):
        # Procesamos de a una pagina para no gastar memoria
        imagenes = convert_from_bytes(pdf_bytes, dpi=200, first_page=i, last_page=i)
        texto_pagina = pytesseract.image_to_string(imagenes[0], lang="spa")
        partes.append(f"## Página {i}\n\n{texto_pagina.strip()}")
        barra.progress(i / total_paginas, text=f"OCR: página {i} de {total_paginas}...")

    barra.empty()
    return "\n\n".join(partes)


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
        try:
            # Leemos los bytes del PDF una sola vez
            pdf_bytes = archivo.read()

            with st.spinner("Leyendo el documento..."):
                # 1) Intento normal: extraer texto real con MarkItDown
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_bytes)
                    ruta_tmp = tmp.name
                resultado = md.convert(ruta_tmp)
                os.unlink(ruta_tmp)
                texto_md = (resultado.text_content or "").strip()
                metodo = "texto"

            # 2) Si vino casi vacio -> el PDF es escaneado -> aplicamos OCR
            if len(texto_md) < 20:
                st.info("📷 El PDF parece escaneado (imágenes). Aplicando OCR para leer el texto... esto puede tardar un poco.")
                texto_md = ocr_pdf(pdf_bytes).strip()
                metodo = "OCR"

            nombre_base = os.path.splitext(archivo.name)[0]
            nombre_salida = f"{nombre_base}.md"

            if len(texto_md) < 5:
                st.warning("⚠️ No se pudo extraer texto legible de este PDF. Puede estar en muy baja calidad o protegido.")
            else:
                if metodo == "OCR":
                    st.success(f"✅ ¡Éxito con OCR! El archivo '{nombre_salida}' está listo para Claude.")
                else:
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
