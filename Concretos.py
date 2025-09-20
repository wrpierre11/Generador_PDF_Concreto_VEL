import PyPDF2
import re
import pandas as pd

# 1. Función para extraer texto de un PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

# 2. Ruta a tu archivo PDF
pdf_path = r"C:\Users\USUARIO\Documents\PROYECTO VEL - BIM\05. COORDINACION\05.PYTHON\Generar_PDF_Concreto\Detalle de la incidencia-202509192028.pdf"

# 3. Extraer texto del PDF
pdf_text = extract_text_from_pdf(pdf_path)
print("--- TEXTO EXTRAÍDO DEL PDF ---")
print(pdf_text)
print("--- FIN DEL TEXTO EXTRAÍDO ---")

# 4. Usar expresiones regulares que coinciden con el texto real del PDF
# El patrón '\s+' busca uno o más espacios en blanco.
location_match = re.search(r"Location details\s+(\d+)", pdf_text)
vaciado_match = re.search(r"CIG_Vaciado\s+([^\s]+)", pdf_text)
mezclado_match = re.search(r"CIG_Tipo_Mezclado\s+([^\s]+)", pdf_text)

# 5. Obtener los valores extraídos
location_details = location_match.group(1).strip() if location_match else None
cig_vaciado = vaciado_match.group(1).strip() if vaciado_match else None
cig_tipo_mezclado = mezclado_match.group(1).strip() if mezclado_match else None

# 6. Verificar si los datos fueron encontrados
if location_details and cig_vaciado and cig_tipo_mezclado:
    # 7. Crear un DataFrame de pandas y exportar a Excel
    data = {
        "Location details": [location_details],
        "CIG_Vaciado": [cig_vaciado],
        "CIG_Tipo_Mezclado": [cig_tipo_mezclado]
    }
    df = pd.DataFrame(data)
    output_excel_path = "Datos_del_PDF.xlsx"
    df.to_excel(output_excel_path, index=False)
    print(f"Excel generado exitosamente en: {output_excel_path}")
else:
    print("No se encontraron todos los datos en el PDF. Revisa los mensajes de error.")
    print("--- DETALLES DEL ERROR ---")
    if not location_match:
        print("El campo 'Location details' no fue encontrado.")
    if not vaciado_match:
        print("El campo 'CIG_Vaciado' no fue encontrado.")
    if not mezclado_match:
        print("El campo 'CIG_Tipo_Mezclado' no fue encontrado.")