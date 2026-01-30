# db_postgres.py
import os
import psycopg2


def obtener_estudiantes_desde_db():
    """
    Conecta a PostgreSQL usando variables de entorno definidas en docker-compose.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),          # nombre del servicio en docker-compose
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "UAGro"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "13102000"),
    )

    cur = conn.cursor()

    # Ajusta nombres de tabla/columnas según tu esquema
    cur.execute("""
        SELECT
            matricula,
            nombre_completo,
            carrera,
            semestre,
            promedio_general,
            estatus
        FROM estudiantes;
    """)
    filas_estudiantes = cur.fetchall()

    estudiantes = []

    for fila in filas_estudiantes:
        matricula, nombre, carrera, semestre, promedio_general, estatus = fila

        cur.execute("""
            SELECT
                nombre,
            clave,
                calificacion_parcial1,
                calificacion_parcial2,
                calificacion_parcial3,
                asistencias,
                faltas
            FROM materias
            WHERE matricula_estudiante = %s;
        """, (matricula,))
        filas_materias = cur.fetchall()

        materias = []
        for m in filas_materias:
            materias.append({
                "nombre": m[0],
                "clave": m[1],
                "calificacion_parcial1": m[2],
                "calificacion_parcial2": m[3],
                "calificacion_parcial3": m[4],
                "asistencias": m[5],
                "faltas": m[6],
            })

        estudiantes.append({
            "matricula": matricula,
            "nombre_completo": nombre,
            "carrera": carrera,
            "semestre": semestre,
            "materias": materias,
            "promedio_general": float(promedio_general),
            "estatus": estatus,
        })

    cur.close()
    conn.close()

    # Misma estructura que tu datos_estudiantes.json
    return {"estudiantes": estudiantes}
