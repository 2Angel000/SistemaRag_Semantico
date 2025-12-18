import streamlit as st
from sistema_rag import SistemaRAGCalificaciones
from generador_formatos import GeneradorFormatosCalificaciones
import os


def main():
    st.title("Asistente RAG para Calificaciones")
    st.write("Sistema inteligente para consulta y generación de formatos de calificaciones")

    # === INICIALIZACIÓN DE SESSION STATE ===
    if "sistema_rag" not in st.session_state:
        st.session_state.sistema_rag = SistemaRAGCalificaciones()
    if "generador" not in st.session_state:
        st.session_state.generador = GeneradorFormatosCalificaciones(
            st.session_state.sistema_rag
        )
    if "consulta" not in st.session_state:
        st.session_state.consulta = ""

    # Sidebar con ejemplos
    st.sidebar.header("💡 Ejemplos de consultas")
    ejemplos = [
        "Calificaciones de María González",
        "Matrícula 2024002",
        "Generar formato para 2024001",
        "Asistencias de Carlos Rodríguez",
    ]

    for ejemplo in ejemplos:
        if st.sidebar.button(ejemplo):
            st.session_state.consulta = ejemplo

    # Interfaz principal
    consulta = st.text_input(
        "¿Qué información necesitas?",
        value=st.session_state.consulta,
        placeholder="Ej: Calificaciones de María González...",
    )

    if st.button("🔍 Consultar") and consulta:
        st.session_state.consulta = consulta  # guardar última consulta
        with st.spinner("Buscando información..."):
            respuesta = st.session_state.sistema_rag.consultar_sistema(consulta)

        st.success("Información encontrada:")
        st.markdown(respuesta)

        # Extraer matrícula
        tokens = consulta.replace(",", " ").split()
        matricula = next(
            (t for t in tokens if t.isdigit() and 7 <= len(t) <= 8),
            None
        )
        if matricula:
            st.session_state.matricula_para_generar = matricula

    # Botón para generar formato
    if "matricula_para_generar" in st.session_state:
        if st.button(f"📄 Generar Formato para {st.session_state.matricula_para_generar}"):
            with st.spinner("Generando documento Word..."):
                # AQUI EL CAMBIO: Recibimos dos variables
                mensaje, ruta_archivo = st.session_state.generador.generar_formato_calificaciones(
                    st.session_state.matricula_para_generar
                )

            # Mostramos el mensaje
            if "❌" in mensaje:
                st.error(mensaje)
            else:
                st.success(mensaje)

                # Si hay ruta, mostramos botón de descarga
                if ruta_archivo:
                    st.info(f"📂 Ruta del archivo en servidor: `{ruta_archivo}`")

                    with open(ruta_archivo, "rb") as file:
                        st.download_button(
                            label="⬇️ Descargar Reporte Word",
                            data=file,
                            file_name=os.path.basename(ruta_archivo),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

    # Sección de información del sistema
    with st.expander("ℹ️ Acerca de este sistema RAG"):
        st.markdown(
            """
        **¿Cómo funciona?**  
        1. **Recuperación (Retrieval)**: Busca información relevante en la base de conocimiento  
        2. **Aumentación (Augmented)**: Combina la información encontrada  
        3. **Generación (Generation)**: Crea respuestas útiles y formatos  

        **Tecnologías utilizadas:**  
        - Python para el procesamiento  
        - Búsqueda semántica simple  
        - Generación de documentos Word  
        - Interface con Streamlit  
        """
        )


if __name__ == "__main__":
    main()
