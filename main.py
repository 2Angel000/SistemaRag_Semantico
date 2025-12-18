from app.sistema_rag import SistemaRAGCalificaciones
from app.generador_formatos import GeneradorFormatosCalificaciones

def main():

    # Para usar PostgreSQL:
    sistema = SistemaRAGCalificaciones(usar_postgres=True)

    # sistema = SistemaRAGCalificaciones("data/datos_estudiantes.json")
    generador = GeneradorFormatosCalificaciones(sistema)

    print("SISTEMA RAG PARA CALIFICACIONES - CLI")
    matricula = input("Ingresa la matrícula para generar formato: ")
    resultado = generador.generar_formato_calificaciones(matricula)
    print(resultado)


if __name__ == "__main__":
    main()
