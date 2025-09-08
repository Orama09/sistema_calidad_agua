from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
import psycopg2
from sqlalchemy import create_engine

# Inicializar app Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_por_defecto")  # Mejor usar variable de entorno

# DATABASE_URL proporcionada por Railway
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Validación para evitar crash
if not DATABASE_URL:
    raise RuntimeError("La variable de entorno DATABASE_URL no está configurada")

# Ajuste para SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Conexión básica con psycopg2
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Engine para Pandas
engine = create_engine(DATABASE_URL)

# ----------------- RUTAS -----------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/mision-vision')
def mision_vision():
    return render_template('mision_vision.html')

@app.route('/cargar-datos', methods=['GET', 'POST'])
def cargar_datos():
    datos = None

    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                data = pd.read_excel(file) if file.filename.endswith('.xlsx') else pd.read_csv(file)
                if not data.empty:
                    data.to_sql('calidad_agua', engine, if_exists='replace', index=False)
                    flash('Datos cargados exitosamente', 'success')
                else:
                    flash('El archivo está vacío.', 'error')
            except Exception as e:
                flash(f'Error al cargar los datos: {e}', 'error')
        return redirect(url_for('cargar_datos'))

    # Recuperar datos desde PostgreSQL si existe la tabla
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='calidad_agua');")
        if cur.fetchone()[0]:
            cur.execute("SELECT * FROM calidad_agua")
            datos = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f'Error al recuperar los datos: {e}', 'error')

    return render_template('cargar_datos.html', datos=datos)

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

@app.route('/graficos')
def graficos():
    return render_template('graficos.html')

# No se necesita if __name__ == '__main__' en Railway, Gunicorn lo maneja
