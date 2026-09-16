import os
import tempfile
import streamlit as st
from markitdown import MarkItDown

# =====================================================================
# Configuracion de la pagina
# =====================================================================
st.set_page_config(
    page_title="Assetplan · PDF y Excel a Markdown",
    page_icon="🏢",
    layout="centered",
)

# =====================================================================
# 🎨 COLORES OFICIALES ASSETPLAN + estilos
# =====================================================================
COLOR_PRINCIPAL  = "#2B7FFF"
COLOR_ACENTO     = "#4285F4"
COLOR_AZUL_CLARO = "#BACCE3"
COLOR_GRIS       = "#5F6B7A"
COLOR_FONDO      = "#F5F8FC"

st.markdown(
    f"""
    <style>
    .stApp {{ font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif; }}
    h1 {{ color: {COLOR_PRINCIPAL} !important; }}
    .stButton > button {{
        background-color: {COLOR_PRINCIPAL};
        color: #FFFFFF; border: none; border-radius: 10px;
        padding: 12px 20px; font-weight: 600; font-size: 15px;
    }}
    .stButton > button:hover {{ filter: brightness(92%); color: #FFFFFF; }}
    .stDownloadButton > button {{
        background-color: {COLOR_ACENTO};
        color: #FFFFFF; border: none; border-radius: 10px; font-weight: 600;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {COLOR_FONDO};
        border: 2px dashed {COLOR_AZUL_CLARO}; border-radius: 12px;
    }}
    .stTabs [data-baseweb="tab"] {{ font-size: 17px; font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ color: {COLOR_PRINCIPAL}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Motor de conversion de Microsoft
md = MarkItDown()


# =====================================================================
# OCR de una imagen: prueba varios idiomas y modos hasta obtener texto
# =====================================================================
def ocr_imagen(imagen):
    import pytesseract
    from PIL import ImageOps
    img = imagen.convert("L")
    img = ImageOps.autocontrast(img)
    ultimo_error = ""
    configs = ["--oem 3 --psm 6", "--oem 3 --psm 4", "--oem 3 --psm 3", "--oem 3 --psm 11"]
    for cfg in configs:
        for lang in ("spa+eng", "spa", "eng"):
            try:
                texto = pytesseract.image_to_string(img, lang=lang, config=cfg)
                if texto.strip():
                    return texto, ""
            except Exception as e:
                ultimo_error = f"[lang={lang} {cfg}] {type(e).__name__}: {e}"
    return "", ultimo_error


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
        texto_pagina, _ = ocr_imagen(pagina)
        texto_pagina = texto_pagina.strip()
        if texto_pagina:
            paginas_con_texto += 1
        partes.append(f"## Página {i}\n\n{texto_pagina}")
        barra.progress(i / total_paginas, text=f"OCR: página {i} de {total_paginas}...")
    barra.empty()
    return "\n\n".join(partes), paginas_con_texto, primera_imagen


# =====================================================================
# Bloque de salida reutilizable (descarga + copiar + ver)
# =====================================================================
def mostrar_resultado(texto_md, nombre_salida, sufijo):
    st.download_button(
        label="📥 Descargar archivo .md",
        data=texto_md,
        file_name=nombre_salida,
        mime="text/markdown",
        key=f"dl_{sufijo}",
    )
    st.markdown("**📋 Copiar para pegar en una IA** (usa el ícono de copiar ⧉ arriba a la derecha del recuadro):")
    prompt_listo = (
        "Tengo este contenido en Markdown extraído de un documento. "
        "Ayúdame a analizarlo:\n\n" + texto_md
    )
    st.code(prompt_listo, language="markdown")
    with st.expander("👁️ Ver solo el contenido convertido"):
        st.text(texto_md)


# =====================================================================
# Encabezado
# =====================================================================
st.title("🏢 Herramienta Interna de Optimización Documental")
st.markdown(
    f"<p style='color:{COLOR_GRIS}; font-size:17px; margin-top:-8px;'>"
    "Convierte tus documentos a Markdown y ahorra hasta un 70% de tokens en Claude</p>",
    unsafe_allow_html=True,
)
st.divider()

tab_pdf, tab_excel = st.tabs(["📄  PDF", "📊  Excel"])

# =====================================================================
# PESTAÑA 1 — PDF
# =====================================================================
with tab_pdf:
    st.subheader("1. Carga tu PDF")
    archivo_pdf = st.file_uploader(
        "Arrastra tu PDF aquí o haz clic para subirlo",
        type=["pdf"],
        key="up_pdf",
    )

    if archivo_pdf is not None:
        if st.button("Optimizar y Convertir 🚀", key="btn_pdf"):
            try:
                pdf_bytes = archivo_pdf.read()
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
                if len(texto_md) < 20:
                    st.info("📷 El PDF parece escaneado (imágenes). Aplicando OCR... esto puede tardar varios minutos.")
                    texto_md, paginas_con_texto, primera_imagen = ocr_pdf(pdf_bytes)
                    texto_md = texto_md.strip()
                    metodo = "OCR"

                nombre_salida = f"{os.path.splitext(archivo_pdf.name)[0]}.md"
                ocr_vacio = (metodo == "OCR" and (paginas_con_texto or 0) == 0)

                if ocr_vacio:
                    st.error("⚠️ El OCR no logró leer texto de las imágenes. Abajo te muestro cómo está viendo la página 1.")
                    if primera_imagen is not None:
                        st.image(primera_imagen, caption="Así renderiza el sistema la página 1", use_container_width=True)
                    st.markdown(
                        "- **Hoja en blanco** → el PDF usa un formato que el lector gratuito no puede decodificar.\n"
                        "- **Documento visible** → suele ser una foto de celular (difícil para el OCR gratuito)."
                    )
                else:
                    if metodo == "OCR":
                        st.success(f"✅ ¡Éxito con OCR! '{nombre_salida}' listo. (Texto leído en {paginas_con_texto} páginas.)")
                    else:
                        st.success(f"✅ ¡Éxito! El archivo '{nombre_salida}' está listo para Claude.")
                    st.subheader("2. Descarga o copia el resultado")
                    mostrar_resultado(texto_md, nombre_salida, "pdf")
            except Exception as e:
                st.error(f"❌ Error en el proceso: {str(e)}")
    else:
        st.info("Sube un archivo PDF para comenzar.")

# =====================================================================
# PESTAÑA 2 — EXCEL
# =====================================================================
with tab_excel:
    st.subheader("1. Carga tu Excel")
    archivo_xls = st.file_uploader(
        "Arrastra tu Excel (.xlsx, .xls) o CSV aquí",
        type=["xlsx", "xls", "csv"],
        key="up_xls",
    )
    st.caption("💡 Para archivos muy grandes, conviene subir solo la hoja o el rango que necesitas.")

    if archivo_xls is not None:
        if st.button("Optimizar y Convertir 🚀", key="btn_xls"):
            try:
                with st.spinner("Leyendo la planilla..."):
                    extension = os.path.splitext(archivo_xls.name)[1] or ".xlsx"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                        tmp.write(archivo_xls.read())
                        ruta_tmp = tmp.name
                    resultado = md.convert(ruta_tmp)
                    os.unlink(ruta_tmp)
                    texto_md = (resultado.text_content or "").strip()

                nombre_salida = f"{os.path.splitext(archivo_xls.name)[0]}.md"

                if len(texto_md) < 5:
                    st.warning("⚠️ No se pudo extraer contenido de esta planilla. Puede estar vacía o protegida.")
                else:
                    st.success(f"✅ ¡Éxito! El archivo '{nombre_salida}' está listo para Claude.")
                    st.subheader("2. Descarga o copia el resultado")
                    mostrar_resultado(texto_md, nombre_salida, "xls")
            except Exception as e:
                st.error(f"❌ Error en el proceso: {str(e)}")
    else:
        st.info("Sube un archivo Excel o CSV para comenzar.")
