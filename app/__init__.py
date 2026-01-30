import os
from sentence_transformers import SentenceTransformer
from db_postgres import obtener_estudiantes_desde_db
from .sistema_rag import SistemaRAGCalificaciones


class SistemaRAGCalificaciones:
    def __init__(self, ruta_datos: str | None = None, usar_postgres: bool = False):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        if usar_postgres:
            print("Cargando datos desde PostgreSQL...")
            self.datos = obtener_estudiantes_desde_db()
        else:
            if ruta_datos is None:
                ruta_datos = os.path.join(base_dir, "datos_estudiantes.json")
            self.datos = self.cargar_datos(ruta_datos)

        print("Cargando modelo de embeddings (esto puede tardar unos segundos)...")
        try:
            self.embedding_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
            print("Modelo de embeddings cargado.")
        except Exception as e:
            print(f"Error al cargar el modelo de embeddings: {e}")
            self.embedding_model = None

        if self.embedding_model:
            self.conocimiento_procesado, self.corpus_embeddings = self.procesar_conocimiento()
        else:
            conocimiento, _ = self.procesar_conocimiento()
            self.conocimiento_procesado, self.corpus_embeddings = conocimiento, None
