import pandas as pd

# 1. Rutas de los archivos
df_seguimiento = pd.read_excel("Seguimiento Concreto_2.xlsx", sheet_name="Concreto")
df_datos_pdf = pd.read_excel("Datos_del_PDF_2.xlsx", sheet_name="Sheet1")

# 2. Unir los DataFrames usando 'ID' y 'Location details' como clave
# Esto une las dos tablas donde el 'ID' del seguimiento coincide con el 'Location details' del PDF
df_combinado = pd.merge(
    df_seguimiento,
    df_datos_pdf,
    left_on="ID",  # <-- CAMBIO AQUÍ
    right_on="Location details",
    how="left"
)

# 3. Guardar el resultado en un nuevo archivo de Excel
output_excel_path = "Seguimiento_Concreto_Actualizado.xlsx"
df_combinado.to_excel(output_excel_path, index=False)

print(f"Archivo actualizado guardado en: {output_excel_path}")