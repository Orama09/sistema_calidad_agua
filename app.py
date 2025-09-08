from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
import psycopg2
from sqlalchemy import create_engine

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Railway provee la variable DATABASE_URL automáticamente
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Railway usa postgres:// pero SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Conexión básica con psycopg2
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Engine para usar con Pandas (guardar DataFrames en PostgreSQL)
engine = create_engine(DATABASE_URL)

# Ruta de inicio
@app.route('/')
def home():
    return render_template('home.html')

# Ruta de misión y visión
@app.route('/mision-vision')
def mision_vision():
    return render_template('mision_vision.html')

# Ruta para cargar datos
@app.route('/cargar-datos', methods=['GET', 'POST'])
def cargar_datos():
    datos = None  # Variable para almacenar los datos desde la base de datos

    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                # Leer el archivo (puede ser .xlsx o .csv)
                data = pd.read_excel(file) if file.filename.endswith('.xlsx') else pd.read_csv(file)

                if not data.empty:
                    # Guardar los datos en PostgreSQL con Pandas + SQLAlchemy
                    data.to_sql('calidad_agua', engine, if_exists='replace', index=False)
                    flash('Datos cargados exitosamente', 'success')
                else:
                    flash('El archivo está vacío.', 'error')
            except Exception as e:
                flash(f'Error al cargar los datos: {e}', 'error')
        return redirect(url_for('cargar_datos'))

    # Recuperar datos desde PostgreSQL si la tabla existe
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='calidad_agua');")
        table_exists = cur.fetchone()[0]

        if table_exists:
            cur.execute("SELECT * FROM calidad_agua")
            datos = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        flash(f'Error al recuperar los datos: {e}', 'error')

    return render_template('cargar_datos.html', datos=datos)

# Ruta para eliminar la tabla
@app.route('/eliminar-tabla', methods=['POST'])
def eliminar_tabla():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS calidad_agua")
        conn.commit()
        cur.close()
        conn.close()
        flash('Tabla eliminada exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar la tabla: {e}', 'error')

    return redirect(url_for('cargar_datos'))

# Ruta para mostrar gráficos de Tableau
@app.route('/graficos')
def graficos():
    return render_template('graficos.html')

if __name__ == '__main__':
    app.run(debug=True)

