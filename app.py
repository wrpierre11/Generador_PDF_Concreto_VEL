from flask import Flask, request, render_template_string, send_file
import PyPDF2
import re
import pandas as pd
import os
import uuid

app = Flask(__name__)

# Código HTML para la página principal
HTML_CODE = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Automatización de Concretos</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: auto; padding: 20px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2 { text-align: center; color: #333; }
        .form-section { border: 1px solid #ccc; padding: 20px; border-radius: 6px; margin-bottom: 20px; }
        input[type="file"], input[type="text"] { display: block; width: 90%; margin: 10px 0; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        input[type="submit"] { background-color: #007BFF; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
        input[type="submit"]:hover { background-color: #0056b3; }
        .result { margin-top: 20px; text-align: center; }
        .result a { color: #007BFF; text-decoration: none; }
        .result a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Automatización de Excel con Python</h1>
        
        <div class="form-section">
            <h2>1. Extraer datos de PDF</h2>
            <form action="/process_pdf" method="post" enctype="multipart/form-data">
                <p>Selecciona un archivo PDF para extraer los datos:</p>
                <input type="file" name="pdf_file" accept=".pdf" required>
                <p>Nombra el archivo Excel generado:</p>
                <input type="text" name="excel_name_pdf" placeholder="Ej: Datos_del_PDF.xlsx" required>
                <input type="submit" value="Generar Excel del PDF">
            </form>
            <div class="result">{{ pdf_result }}</div>
        </div>

        <div class="form-section">
            <h2>2. Combinar archivos Excel</h2>
            <form action="/merge_excel" method="post" enctype="multipart/form-data">
                <p>Selecciona los dos archivos Excel para combinar:</p>
                <p>Archivo 1 (Teórico):</p>
                <input type="file" name="teorico_file" accept=".xlsx" required>
                <p>Archivo 2 (Record):</p>
                <input type="file" name="record_file" accept=".xlsx" required>
                <p>Nombra el archivo Excel combinado:</p>
                <input type="text" name="excel_name_merge" placeholder="Ej: Reporte_Final.xlsx" required>
                <input type="submit" value="Combinar y generar Excel">
            </form>
            <div class="result">{{ excel_result }}</div>
        </div>
    </div>
</body>
</html>
"""

# Funciones de extracción y combinación (las mismas que tenías)
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

@app.route('/')
def home():
    return render_template_string(HTML_CODE, pdf_result="", excel_result="")

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    if 'pdf_file' not in request.files:
        return "No se encontró el archivo."

    pdf_file = request.files['pdf_file']
    excel_name = request.form.get('excel_name_pdf')

    if pdf_file.filename == '' or excel_name == '':
        return "No se seleccionó un archivo o no se especificó un nombre."

    # Asegurarse de que el nombre del archivo termina en .xlsx
    if not excel_name.endswith('.xlsx'):
        excel_name += '.xlsx'

    # Guardar el archivo temporalmente
    temp_path = os.path.join("temp", f"{uuid.uuid4()}_{pdf_file.filename}")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    pdf_file.save(temp_path)

    try:
        pdf_text = extract_text_from_pdf(temp_path)
        
        location_matches = re.findall(r"Location details\s+(\d+)", pdf_text)
        vaciado_matches = re.findall(r"CIG_Vaciado\s+([^\s]+)", pdf_text)
        mezclado_matches = re.findall(r"CIG_Tipo_Mezclado\s+([^\s]+)", pdf_text)

        if location_matches and vaciado_matches and mezclado_matches:
            data = {
                "Location details": location_matches,
                "CIG_Vaciado": vaciado_matches,
                "CIG_Tipo_Mezclado": mezclado_matches
            }
            df = pd.DataFrame(data)
            output_excel_path = os.path.join("temp", excel_name)
            df.to_excel(output_excel_path, index=False)
            
            return send_file(output_excel_path, as_attachment=True, download_name=excel_name)
        else:
            return "Error: No se encontraron todos los datos en el PDF."
    except Exception as e:
        return f"Ocurrió un error: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/merge_excel', methods=['POST'])
def merge_excel():
    if 'teorico_file' not in request.files or 'record_file' not in request.files:
        return "Por favor, sube ambos archivos."

    teorico_file = request.files['teorico_file']
    record_file = request.files['record_file']
    excel_name = request.form.get('excel_name_merge')

    if teorico_file.filename == '' or record_file.filename == '' or excel_name == '':
        return "Por favor, selecciona ambos archivos y especifica un nombre."
    
    # Asegurarse de que el nombre del archivo termina en .xlsx
    if not excel_name.endswith('.xlsx'):
        excel_name += '.xlsx'

    # Guardar archivos temporalmente
    temp_teorico_path = os.path.join("temp", f"{uuid.uuid4()}_{teorico_file.filename}")
    temp_record_path = os.path.join("temp", f"{uuid.uuid4()}_{record_file.filename}")
    os.makedirs(os.path.dirname(temp_teorico_path), exist_ok=True)

    teorico_file.save(temp_teorico_path)
    record_file.save(temp_record_path)

    try:
        # Se asume que la hoja por defecto es la primera si no se especifica
        df_seguimiento = pd.read_excel(temp_teorico_path)
        df_datos_pdf = pd.read_excel(temp_record_path)
        
        df_combinado = pd.merge(
            df_seguimiento,
            df_datos_pdf,
            left_on="ID",
            right_on="Location details",
            how="left"
        )
        
        output_excel_path = os.path.join("temp", excel_name)
        df_combinado.to_excel(output_excel_path, index=False)
        
        return send_file(output_excel_path, as_attachment=True, download_name=excel_name)
    except Exception as e:
        return f"Ocurrió un error al combinar los archivos: {str(e)}"
    finally:
        if os.path.exists(temp_teorico_path):
            os.remove(temp_teorico_path)
        if os.path.exists(temp_record_path):
            os.remove(temp_record_path)

if __name__ == '__main__':
    app.run(debug=True)