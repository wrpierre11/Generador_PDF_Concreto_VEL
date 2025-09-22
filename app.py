from flask import Flask, request, render_template, send_file
import PyPDF2
import re
import pandas as pd
import os
import uuid

app = Flask(__name__)

# Las funciones para procesar los datos no cambian

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

@app.route('/')
def home():
    # Ahora Flask busca el archivo index.html en la carpeta 'templates'
    return render_template('index.html', pdf_result="", excel_result="")

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    if 'pdf_file' not in request.files:
        return render_template('index.html', pdf_result="Error: No se encontró el archivo.")

    pdf_file = request.files['pdf_file']
    excel_name = request.form.get('excel_name_pdf')

    if pdf_file.filename == '' or excel_name == '':
        return render_template('index.html', pdf_result="Error: No se seleccionó un archivo o no se especificó un nombre.")

    if not excel_name.endswith('.xlsx'):
        excel_name += '.xlsx'

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
            return render_template('index.html', pdf_result="Error: No se encontraron todos los datos en el PDF.")
    except Exception as e:
        return render_template('index.html', pdf_result=f"Ocurrió un error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/merge_excel', methods=['POST'])
def merge_excel():
    if 'teorico_file' not in request.files or 'record_file' not in request.files:
        return render_template('index.html', excel_result="Error: Por favor, sube ambos archivos.")

    teorico_file = request.files['teorico_file']
    record_file = request.files['record_file']
    excel_name = request.form.get('excel_name_merge')

    if teorico_file.filename == '' or record_file.filename == '' or excel_name == '':
        return render_template('index.html', excel_result="Error: Por favor, selecciona ambos archivos y especifica un nombre.")
    
    if not excel_name.endswith('.xlsx'):
        excel_name += '.xlsx'

    temp_teorico_path = os.path.join("temp", f"{uuid.uuid4()}_{teorico_file.filename}")
    temp_record_path = os.path.join("temp", f"{uuid.uuid4()}_{record_file.filename}")
    os.makedirs(os.path.dirname(temp_teorico_path), exist_ok=True)

    teorico_file.save(temp_teorico_path)
    record_file.save(temp_record_path)

    try:
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
        return render_template('index.html', excel_result=f"Ocurrió un error al combinar los archivos: {str(e)}")
    finally:
        if os.path.exists(temp_teorico_path):
            os.remove(temp_teorico_path)
        if os.path.exists(temp_record_path):
            os.remove(temp_record_path)

if __name__ == '__main__':
    app.run(debug=True)