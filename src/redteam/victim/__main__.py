"""Chat interactivo con la víctima: python -m redteam.victim [--cliente C001] [--modelo mistral]"""

import argparse

from redteam.config import cargar_config
from redteam.victim import crear_asistente


def main() -> None:
    parser = argparse.ArgumentParser(description="Habla con el asistente de Albarizo.")
    parser.add_argument("--cliente", default="C001", help="Cliente con la sesión iniciada")
    parser.add_argument(
        "--modelo", default=None, help="Modelo de config.yaml (por defecto, 'modelo')"
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    config = cargar_config()
    asistente = crear_asistente(config, args.modelo)
    cliente = asistente.tienda.clientes[args.cliente]
    print(f"Modelo: {asistente.llm.name} · Cliente: {cliente['nombre']} ({args.cliente})")
    print("Escribe tu mensaje (línea vacía para salir).\n")

    # Se reenvía toda la conversación en cada turno para que el modelo tenga el historial.
    mensajes: list[str] = []
    while texto := input("tú> ").strip():
        mensajes.append(texto)
        turno = asistente.conversar(args.cliente, mensajes, seed=args.seed).turnos[-1]
        for ll in turno.llamadas:
            print(f"  [herramienta] {ll.nombre}({ll.argumentos}) -> {ll.resultado}")
        print(f"  [rag] {', '.join(turno.documentos)}")
        print(f"albi> {turno.respuesta}\n")


if __name__ == "__main__":
    main()
