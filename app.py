from flask import Flask, request, render_template, send_file
import PyPDF2
import re
import pandas as pd
import os
import uuid

app = Flask(__name__)

# Directorio para archivos temporales
TEMP_DIR = 'temp'

# Si el directorio no existe, lo crea
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Función para extraer texto de un PDF
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

    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{pdf_file.filename}")
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    pdf_file.save(temp_path)

    try:
        pdf_text = extract_text_from_pdf(temp_path)
        location_matches = re.findall(r"Location details\s+(\d+)", pdf_text)
        vaciado_matches = re.findall(r"CIG_Vaciado\s+([^\s]+)", pdf_text)
        mezclado_matches = re.findall(r"CIG_Tipo_Mezclado\s+([^\s]+)", pdf_text)
        fecha_vaciado_matches = re.findall(r"CIG_Fecha_Vaciado\s+([^\s]+)", pdf_text)
        
        # CORRECCIÓN: Extraer el campo CIG_Ensayo_Comp
        ensayo_comp_matches = re.findall(r"CIG_Ensayo_Comp\s+([^\s]+)", pdf_text)

        if location_matches and vaciado_matches and mezclado_matches and fecha_vaciado_matches and ensayo_comp_matches:
            data = {
                "Location details": location_matches,
                "CIG_Vaciado": vaciado_matches,
                "CIG_Tipo_Mezclado": mezclado_matches,
                "CIG_Fecha_Vaciado": fecha_vaciado_matches,
                "CIG_Ensayo_Comp": ensayo_comp_matches  # AGREGAR ESTE CAMPO
            }
            
            # Verificar que todos los arrays tengan la misma longitud
            min_length = min(len(location_matches), len(vaciado_matches), len(mezclado_matches), 
                            len(fecha_vaciado_matches), len(ensayo_comp_matches))
            
            # Recortar todos los arrays a la misma longitud
            data = {key: values[:min_length] for key, values in data.items()}
            
            df = pd.DataFrame(data)
            output_excel_path = os.path.join(TEMP_DIR, excel_name)
            df.to_excel(output_excel_path, index=False)
            
            return send_file(output_excel_path, as_attachment=True, download_name=excel_name)
        else:
            # Para debugging, muestra qué campos se encontraron
            found_fields = {
                "Location details": len(location_matches) if location_matches else 0,
                "CIG_Vaciado": len(vaciado_matches) if vaciado_matches else 0,
                "CIG_Tipo_Mezclado": len(mezclado_matches) if mezclado_matches else 0,
                "CIG_Fecha_Vaciado": len(fecha_vaciado_matches) if fecha_vaciado_matches else 0,
                "CIG_Ensayo_Comp": len(ensayo_comp_matches) if ensayo_comp_matches else 0
            }
            return render_template('index.html', pdf_result=f"Error: No se encontraron todos los datos en el PDF. Campos encontrados: {found_fields}")
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

    temp_teorico_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{teorico_file.filename}")
    temp_record_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{record_file.filename}")
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
        
        output_excel_path = os.path.join(TEMP_DIR, excel_name)
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