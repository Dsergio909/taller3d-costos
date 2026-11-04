"""Dibuja el flujo de cotización como imagen SVG a partir de flujos/cotizacion.json.

Así el diagrama nunca queda viejo: sale del mismo JSON que se importa en n8n.
Uso: python scripts/diagrama_flujo.py   ->  flujos/diagrama_cotizacion.svg
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ANCHO, ALTO = 170, 58          # tamaño de cada caja
ESCALA_X, ESCALA_Y = 0.92, 0.9  # n8n separa los nodos 220 px; aquí un poco menos
AZUL, TEXTO, SUAVE, BORDE, FONDO = "#1a5fb4", "#1f2933", "#52606d", "#c3ccd5", "#f5f7f9"

# Qué tipo de paso es cada nodo (para la etiqueta pequeña de arriba)
TIPO = {
    "n8n-nodes-base.formTrigger": "Entrada", "n8n-nodes-base.webhook": "Entrada",
    "n8n-nodes-base.code": "Código", "n8n-nodes-base.set": "Configuración",
    "n8n-nodes-base.readWriteFile": "Archivo", "n8n-nodes-base.extractFromFile": "Archivo",
    "n8n-nodes-base.if": "Decisión", "n8n-nodes-base.httpRequest": "IA local",
    "n8n-nodes-base.wait": "Persona", "n8n-nodes-base.convertToFile": "Archivo",
}
DESTACADOS = {"Calcular cotización", "Redactar con IA local (Ollama)", "Revisar cifras del borrador",
              "Aprobación de Sergio", "Aprobación del dueño"}


# Dónde va cada nodo en el dibujo (columna, fila). Dos filas para que quepa en el README.
LAYOUT = {
    "Pedido por formulario": (0, 0), "Pedido por webhook": (0, 1),
    "Normalizar pedido": (1, 0.5), "Configuración": (2, 0.5), "Leer tarifas y catálogo": (3, 0.5),
    "CSV a filas": (4, 0.5), "Calcular cotización": (5, 0.5), "¿Pedido válido?": (6, 0.5),
    "Redactar con IA local (Ollama)": (1, 2.6), "Revisar cifras del borrador": (2, 2.15),
    "Plantilla sin IA": (2, 3.05), "Avisar a Sergio": (3, 2.6), "Avisar al dueño": (3, 2.6),
    "Aprobación de Sergio": (4, 2.6), "Aprobación del dueño": (4, 2.6),
    "Pendiente: a archivo": (4, 3.6), "Pendiente: guardar": (5, 3.6),
    "Armar registro": (5, 2.6), "Registro: a archivo": (6, 2.6), "Registro: guardar": (7, 2.6),
}
PASO_X, PASO_Y = 205, 82


def partir(texto: str, largo: int = 22) -> list[str]:
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + 1 > largo and actual:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    return lineas + [actual]


def dibujar(flujo: dict) -> str:
    nodos = {n["name"]: n for n in flujo["nodes"]}
    xs = [n["position"][0] for n in nodos.values()]
    ys = [n["position"][1] for n in nodos.values()]
    x0, y0 = min(xs), min(ys)
    pos = {k: ((40 + LAYOUT[k][0] * PASO_X, 80 + LAYOUT[k][1] * PASO_Y) if k in LAYOUT else
               (40 + (n["position"][0] - x0) * ESCALA_X, 80 + (n["position"][1] - y0) * ESCALA_Y))
           for k, n in nodos.items()}
    w = int(max(p[0] for p in pos.values()) + ANCHO + 40)
    h = int(max(p[1] for p in pos.values()) + ALTO + 60)
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="Segoe UI, -apple-system, Helvetica, Arial, sans-serif">',
        f'<rect width="{w}" height="{h}" fill="{FONDO}"/>',
        '<defs><marker id="f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{SUAVE}"/></marker></defs>',
        f'<text x="40" y="36" font-size="18" font-weight="600" fill="{TEXTO}">{escape(flujo["name"])}</text>',
        f'<text x="40" y="56" font-size="12" fill="{SUAVE}">Flujo de n8n. Las líneas punteadas son el camino '
        'cuando algo falla o el pedido no es válido.</text>',
    ]
    for origen, salidas in flujo["connections"].items():
        for i, salida in enumerate(salidas["main"]):
            for destino in salida:
                (ax, ay), (bx, by) = pos[origen], pos[destino["node"]]
                x1, y1 = ax + ANCHO, ay + ALTO / 2 + (8 if len(salidas["main"]) > 1 and i else 0)
                x2, y2 = bx, by + ALTO / 2
                if by > ay + ALTO and bx <= ax + ANCHO:  # baja a la otra fila: sale por abajo, entra por arriba
                    x1, y1 = ax + ANCHO / 2, ay + ALTO
                    x2, y2 = bx + ANCHO / 2, by
                    medio_y = (y1 + y2) / 2
                    punteada = ' stroke-dasharray="5 4"' if i == 1 else ""
                    partes.append(f'<path d="M{x1:.0f},{y1:.0f} C{x1:.0f},{medio_y:.0f} {x2:.0f},{medio_y:.0f} {x2:.0f},{y2:.0f}" '
                                  f'fill="none" stroke="{SUAVE}" stroke-width="1.4"{punteada} marker-end="url(#f)"/>')
                    continue
                medio = (x1 + x2) / 2
                punteada = ' stroke-dasharray="5 4"' if i == 1 else ""
                partes.append(f'<path d="M{x1:.0f},{y1:.0f} C{medio:.0f},{y1:.0f} {medio:.0f},{y2:.0f} {x2:.0f},{y2:.0f}" '
                              f'fill="none" stroke="{SUAVE}" stroke-width="1.4"{punteada} marker-end="url(#f)"/>')
    for nombre, n in nodos.items():
        x, y = pos[nombre]
        destacado = nombre in DESTACADOS
        partes.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{ANCHO}" height="{ALTO}" rx="4" fill="#ffffff" '
                      f'stroke="{AZUL if destacado else BORDE}" stroke-width="{1.6 if destacado else 1}"/>')
        partes.append(f'<text x="{x + 10:.0f}" y="{y + 16:.0f}" font-size="10" fill="{AZUL if destacado else SUAVE}">'
                      f'{escape(TIPO.get(n["type"], "Paso").upper())}</text>')
        for j, linea in enumerate(partir(nombre)[:2]):
            partes.append(f'<text x="{x + 10:.0f}" y="{y + 33 + j * 15:.0f}" font-size="12.5" fill="{TEXTO}">'
                          f'{escape(linea)}</text>')
    partes.append("</svg>")
    return "\n".join(partes) + "\n"


def main() -> None:
    flujo = json.loads((RAIZ / "flujos" / "cotizacion.json").read_text(encoding="utf-8"))
    destino = RAIZ / "flujos" / "diagrama_cotizacion.svg"
    destino.write_text(dibujar(flujo), encoding="utf-8", newline="\n")
    print("Escrito", destino.relative_to(RAIZ))


if __name__ == "__main__":
    main()
