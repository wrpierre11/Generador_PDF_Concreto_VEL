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
pdf_path = r"C:\Users\USUARIO\Documents\PROYECTO VEL - BIM\05. COORDINACION\05. PYTHON\Generar_PDF_Concreto\Issue detail-202509221321.pdf"

# 3. Extraer texto del PDF
pdf_text = extract_text_from_pdf(pdf_path)
# Puedes quitar esta parte del print si no la necesitas
print("--- TEXTO EXTRAÍDO DEL PDF ---")
print(pdf_text)
print("--- FIN DEL TEXTO EXTRAÍDO ---")

# 4. Usar expresiones regulares que coinciden con el texto real del PDF
# Usamos findall para encontrar todas las coincidencias
location_matches = re.findall(r"Location details\s+(\d+)", pdf_text)
vaciado_matches = re.findall(r"CIG_Vaciado\s+([^\s]+)", pdf_text)
mezclado_matches = re.findall(r"CIG_Tipo_Mezclado\s+([^\s]+)", pdf_text)

# 5. Verificar si los datos fueron encontrados
if location_matches and vaciado_matches and mezclado_matches:
    # 6. Crear un DataFrame de pandas y exportar a Excel
    # Creamos un diccionario con las listas de todos los datos encontrados
    data = {
        "Location details": location_matches,
        "CIG_Vaciado": vaciado_matches,
        "CIG_Tipo_Mezclado": mezclado_matches
    }
    df = pd.DataFrame(data)
    output_excel_path = "Datos_del_PDF.xlsx"
    df.to_excel(output_excel_path, index=False)
    print(f"Excel generado exitosamente en: {output_excel_path}")
else:
    print("No se encontraron todos los datos en el PDF. Revisa los mensajes de error.")
    print("--- DETALLES DEL ERROR ---")
    if not location_matches:
        print("El campo 'Location details' no fue encontrado.")
    if not vaciado_matches:
        print("El campo 'CIG_Vaciado' no fue encontrado.")
    if not mezclado_matches:
        print("El campo 'CIG_Tipo_Mezclado' no fue encontrado.")