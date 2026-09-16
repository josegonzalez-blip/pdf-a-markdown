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
# OCR de una imagen: prueba varios idiomas hasta obtener texto
# =====================================================================
def ocr_imagen(imagen):
    import pytesseract
    from PIL import ImageOps

    # Preprocesamos: escala de grises + auto contraste (ayuda con fotos)
    img = imagen.convert("L")
    img = ImageOps.autocontrast(img)

    # Probamos distintos "modos de pagina" (PSM). El 6 y el 4 suelen rescatar
    # fotos con borde/fondo donde el modo automatico (3) falla.
    configs = ["--oem 3 --psm 6", "--oem 3 --psm 4", "--oem 3 --psm 3", "--oem 3 --psm 11"]
    for cfg in configs:
        for lang in ("spa+eng", "spa", "eng"):
            try:
                texto = pytesseract.image_to_string(img, lang=lang, config=cfg)
                if texto.strip():
                    return texto
            except Exception:
                continue
    return ""


# =====================================================================
# OCR del PDF completo, pagina por pagina (alta resolucion)
# =====================================================================
def ocr_pdf(pdf_bytes):
    from pdf2image import convert_from_bytes, pdfinfo_from_bytes

    info = pdfinfo_from_bytes(pdf_bytes)
    total_paginas = info["Pages"]

    partes = []
    paginas_con_texto = 0
    primera_imagen = None
    barra = st.progress(0, text="Aplicando OCR (leyendo las imágenes)...")

    for i in range(1, total_paginas + 1):
        imagenes = convert_from_bytes(pdf_bytes, dpi=300, first_page=i, last_page=i)
        pagina = imagenes[0]
        if i == 1:
            primera_imagen = pagina
        texto_pagina = ocr_imagen(pagina).strip()
        if texto_pagina:
            paginas_con_texto += 1
        partes.append(f"## Página {i}\n\n{texto_pagina}")
        barra.progress(i / total_paginas, text=f"OCR: página {i} de {total_paginas}...")

    barra.empty()
    return "\n\n".join(partes), paginas_con_texto, primera_imagen


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
# Paso 2: convertir, mostrar y descargar
# =====================================================================
if archivo is not None:
    if st.button("Optimizar y Convertir 🚀"):
        try:
            pdf_bytes = archivo.read()

            with st.spinner("Leyendo el documento..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_bytes)
                    ruta_tmp = tmp.name
                resultado = md.convert(ruta_tmp)
                os.unlink(ruta_tmp)
                texto_md = (resultado.text_content or "").strip()
                metodo = "texto"

            primera_imagen = None
            paginas_con_texto = None

            # Si vino casi vacio -> PDF escaneado -> OCR
            if len(texto_md) < 20:
                st.info("📷 El PDF parece escaneado (imágenes). Aplicando OCR... esto puede tardar varios minutos.")
                texto_md, paginas_con_texto, primera_imagen = ocr_pdf(pdf_bytes)
                texto_md = texto_md.strip()
                metodo = "OCR"

            nombre_base = os.path.splitext(archivo.name)[0]
            nombre_salida = f"{nombre_base}.md"

            # Detectamos si el OCR no logro leer nada real
            ocr_vacio = (metodo == "OCR" and (paginas_con_texto or 0) == 0)

            if ocr_vacio:
                st.error(
                    "⚠️ El OCR no logró leer texto de las imágenes. Abajo te muestro "
                    "**cómo está viendo la página 1** para diagnosticar el problema."
                )
                if primera_imagen is not None:
                    st.image(
                        primera_imagen,
                        caption="Así renderiza el sistema la página 1 de tu PDF",
                        use_container_width=True,
                    )
                st.markdown(
                    "- Si arriba ves la **hoja en blanco** → tu PDF usa un formato de imagen "
                    "que el lector gratuito no puede decodificar (habría que buscar otra vía).\n"
                    "- Si ves el **documento con texto** → el OCR debería haberlo leído; avísame "
                    "y ajustamos la configuración."
                )
            else:
                if metodo == "OCR":
                    st.success(f"✅ ¡Éxito con OCR! '{nombre_salida}' listo. (Texto leído en {paginas_con_texto} páginas.)")
                else:
                    st.success(f"✅ ¡Éxito! El archivo '{nombre_salida}' está listo para Claude.")

                st.subheader("2. Descarga o copia el resultado")

                # Boton de descarga
                st.download_button(
                    label="📥 Descargar archivo .md",
                    data=texto_md,
                    file_name=nombre_salida,
                    mime="text/markdown",
                )

                # NUEVO: bloque listo para copiar y pegar en una IA
                st.markdown("**📋 Copiar para pegar en una IA** (usa el ícono de copiar ⧉ arriba a la derecha del recuadro):")
                prompt_listo = (
                    "Tengo este contenido en Markdown extraído de un PDF. "
                    "Ayúdame a analizarlo:\n\n" + texto_md
                )
                st.code(prompt_listo, language="markdown")

                with st.expander("👁️ Ver solo el contenido convertido"):
                    st.text(texto_md)

        except Exception as e:
            st.error(f"❌ Error en el proceso: {str(e)}")
else:
    st.info("Sube un archivo PDF para comenzar.")
