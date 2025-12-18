# sistema_rag.py
import os
import json
from sentence_transformers import SentenceTransformer, util
from db_postgres import obtener_estudiantes_desde_db


class SistemaRAGCalificaciones:
    def __init__(self, ruta_datos: str | None = None, usar_postgres: bool = False):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        if usar_postgres:
            # Carga desde PostgreSQL
            print("Cargando datos desde PostgreSQL...")
            self.datos = obtener_estudiantes_desde_db()
        else:
            # Ruta por defecto: app/datos_estudiantes.json
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

    def cargar_datos(self, ruta):
        print(f"Intentando cargar datos desde: {ruta}")
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except FileNotFoundError:
            print("Error: Archivo de datos no encontrado")
            return {"estudiantes": []}

    def obtener_estatus_por_promedio(self, promedio_general: float) -> str:
        return "Aprobado" if promedio_general >= 70.0 else "Reprobado"

    def procesar_conocimiento(self):
        conocimiento = []
        corpus_sentences = []

        for estudiante in self.datos.get("estudiantes", []):
            fragmento_estudiante = {
                "matricula": estudiante["matricula"],
                "nombre": estudiante["nombre_completo"],
                "carrera": estudiante["carrera"],
                "promedio_general": estudiante["promedio_general"],
                "contenido": (
                    f"Estudiante: {estudiante['nombre_completo']} - Matrícula: {estudiante['matricula']} "
                    f"- Carrera: {estudiante['carrera']} - Promedio: {estudiante['promedio_general']}"
                ),
                "materias": estudiante["materias"],
                "tipo": "datos_estudiante",
            }
            conocimiento.append(fragmento_estudiante)
            corpus_sentences.append(fragmento_estudiante["contenido"])

            for materia in estudiante["materias"]:
                fragmento_materia = {
                    "matricula": estudiante["matricula"],
                    "materia": materia["nombre"],
                    "contenido": (
                        f"Materia: {materia['nombre']} - Calificaciones: "
                        f"P1:{materia['calificacion_parcial1']}, "
                        f"P2:{materia['calificacion_parcial2']}, "
                        f"P3:{materia['calificacion_parcial3']} - "
                        f"Asistencias: {materia['asistencias']} - "
                        f"Faltas: {materia['faltas']}"
                    ),
                    "detalles_materia": materia,
                    "tipo": "datos_materia",
                }
                conocimiento.append(fragmento_materia)
                corpus_sentences.append(fragmento_materia["contenido"])

        if self.embedding_model:
            corpus_embeddings = self.embedding_model.encode(
                corpus_sentences,
                convert_to_tensor=True,
            )
            for i, frag in enumerate(conocimiento):
                frag["embedding"] = corpus_embeddings[i]
        else:
            corpus_embeddings = []

        return conocimiento, corpus_embeddings

    def buscar_informacion(self, consulta: str):
        consulta = consulta.lower()
        resultados = []

        for fragmento in self.conocimiento_procesado:
            if fragmento["tipo"] == "datos_estudiante":
                if any(
                    palabra in consulta
                    for palabra in [
                        fragmento["matricula"].lower(),
                        fragmento["nombre"].lower(),
                    ]
                ) and fragmento not in resultados:
                    resultados.append(fragmento)

            elif fragmento["tipo"] == "datos_materia":
                if any(
                    palabra in consulta
                    for palabra in [
                        fragmento["materia"].lower(),
                        "calificacion",
                        "asistencia",
                    ]
                ):
                    for estudiante_frag in self.conocimiento_procesado:
                        if (
                            estudiante_frag["tipo"] == "datos_estudiante"
                            and estudiante_frag["matricula"] == fragmento["matricula"]
                        ):
                            if any(
                                palabra in consulta
                                for palabra in [
                                    estudiante_frag["nombre"].lower(),
                                    estudiante_frag["matricula"].lower(),
                                ]
                            ) and fragmento not in resultados:
                                resultados.append(fragmento)
                            break

                    if not any(
                        palabra in consulta
                        for palabra in
                        [item["nombre_completo"].lower() for item in self.datos["estudiantes"]]
                        + [item["matricula"].lower() for item in self.datos["estudiantes"]]
                    ) and fragmento not in resultados:
                        resultados.append(fragmento)

        return resultados[:3]

    def buscar_informacion_semantica(self, consulta: str):
        if self.embedding_model is None or self.corpus_embeddings is None:
            return self.buscar_informacion(consulta)

        if len(self.corpus_embeddings) == 0:
            return self.buscar_informacion(consulta)

        query_embedding = self.embedding_model.encode(
            consulta,
            convert_to_tensor=True,
        )
        cosine_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        top_results_indices = cosine_scores.argsort(descending=True)[:3]
        relevant_fragments = [self.conocimiento_procesado[i] for i in top_results_indices]
        return relevant_fragments

    def generar_respuesta(self, consulta, contexto):
        if not contexto:
            return "No encontré información para responder tu consulta."

        respuesta = "**Información encontrada:**\n\n"

        for item in contexto:
            if item["tipo"] == "datos_estudiante":
                promedio = item.get("promedio_general", 0)
                estatus = self.obtener_estatus_por_promedio(promedio)

                respuesta += f"**Estudiante:** {item['nombre']}\n"
                respuesta += f"**Matrícula:** {item['matricula']}\n"
                respuesta += f"**Carrera:** {item['carrera']}\n"
                respuesta += f"**Promedio general:** {promedio}\n"
                respuesta += f"**Estatus:** {estatus}\n"
                return respuesta

        added_materias = set()
        for item in contexto:
            if item["tipo"] == "datos_materia":
                materia_key = (item["matricula"], item["materia"])
                if materia_key not in added_materias:
                    calif_final = self.calcular_promedio_materia(item["detalles_materia"])
                    respuesta += f"**Materia:** {item['materia']}\n"
                    respuesta += (
                        f"**Calificaciones:** P1: {item['detalles_materia']['calificacion_parcial1']}, "
                        f"P2: {item['detalles_materia']['calificacion_parcial2']}, "
                        f"P3: {item['detalles_materia']['calificacion_parcial3']}\n"
                    )
                    respuesta += f"**Promedio:** {calif_final}\n"
                    respuesta += f"**Asistencias:** {item['detalles_materia']['asistencias']}/47\n"
                    respuesta += f"**Faltas:** {item['detalles_materia']['faltas']}\n\n"
                    added_materias.add(materia_key)

        return respuesta

    def calcular_promedio_materia(self, materia):
        return round(
            (
                materia["calificacion_parcial1"]
                + materia["calificacion_parcial2"]
                + materia["calificacion_parcial3"]
            ) / 3,
            1,
        )

    def obtener_estudiante_por_matricula(self, matricula):
        for estudiante in self.datos["estudiantes"]:
            if estudiante["matricula"] == matricula:
                return estudiante
        return None

    def obtener_estudiante_por_nombre(self, nombre_buscado):
        nombre_buscado_lower = nombre_buscado.lower()
        for estudiante in self.datos["estudiantes"]:
            if nombre_buscado_lower in estudiante["nombre_completo"].lower():
                return estudiante
        return None

    def consultar_sistema(self, pregunta, use_semantic_search=True):
        tokens = pregunta.replace(",", " ").split()
        matricula = next((t for t in tokens if t.isdigit() and 7 <= len(t) <= 8), None)

        if matricula:
            estudiante = self.obtener_estudiante_por_matricula(matricula)
            if estudiante:
                contexto = [{
                    "tipo": "datos_estudiante",
                    "matricula": estudiante["matricula"],
                    "nombre": estudiante["nombre_completo"],
                    "carrera": estudiante["carrera"],
                    "promedio_general": estudiante["promedio_general"],
                    "materias": estudiante["materias"],
                }]
                return self.generar_respuesta(pregunta, contexto)

        if use_semantic_search:
            contexto = self.buscar_informacion_semantica(pregunta)
        else:
            contexto = self.buscar_informacion(pregunta)

        return self.generar_respuesta(pregunta, contexto)
