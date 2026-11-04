"""Prueba de punta a punta del flujo de cotización contra tu n8n local.

Antes: n8n corriendo (scripts/iniciar_n8n.ps1 o docker compose), los dos flujos importados
y activos. Ollama es opcional: si no responde, el flujo usa la plantilla y la prueba lo acepta.

Qué hace:
1. Manda 4 pedidos al webhook: uno inválido, uno del catálogo, uno a medida y otro del catálogo.
2. Espera a que cada uno pida aprobación y la responde: Aprobar, Corregir (con tildes) y Rechazar.
3. Revisa en registro/cotizaciones.csv que cada pedido quedó con su decisión, el precio que
   calcula scripts/costeo.py y la marca «ficticio», y que registro/errores.csv no creció.

Uso:  python scripts/probar_flujo_n8n.py   (o --url http://localhost:5679)
Solo usa la librería estándar.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import costeo  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
REGISTRO = RAIZ / "registro"


def filas(nombre: str) -> list[dict]:
    ruta = REGISTRO / nombre
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def post_json(url: str, cuerpo: dict) -> int:
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status


def post_formulario(url: str, campos: dict[str, str]) -> int:
    """Envía el formulario de aprobación como lo hace el navegador (multipart, UTF-8)."""
    limite = uuid.uuid4().hex
    partes = []
    for nombre, valor in campos.items():
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n')
    cuerpo = ("".join(partes) + f"--{limite}--\r\n").encode("utf-8")
    req = urllib.request.Request(url, data=cuerpo, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={limite}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status


def esperar(condicion, segundos: int, que: str):
    fin = time.time() + segundos
    while time.time() < fin:
        valor = condicion()
        if valor:
            return valor
        time.sleep(2)
    raise SystemExit(f"FALLÓ: no pasó «{que}» en {segundos} s")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default="http://localhost:5679")
    a = ap.parse_args()
    webhook = a.url + "/webhook/cotizar-taller3d"
    t, canales = costeo.leer_tarifas(RAIZ / "datos"), costeo.leer_canales(RAIZ / "datos")
    piezas = {p["id_pieza"]: p for p in costeo.leer_piezas(RAIZ / "datos")}
    errores_antes = len(filas("errores.csv"))
    marca = f"prueba-{int(time.time())}"
    correccion = "Hola, gracias por escribirnos. Las imprimimos y te las entregamos en 5 días hábiles. ¿Te las separamos?"

    casos = [
        # (cliente, pedido, decisión, decisión esperada en el registro)
        (f"{marca}-a", {"canal": "TikTok", "id_pieza": "F01", "cantidad": 0}, None, "Inválido"),
        (f"{marca}-b", {"canal": "WhatsApp", "id_pieza": "R04", "cantidad": 2}, ("Aprobar", ""), "Aprobado"),
        (f"{marca}-c", {"canal": "Instagram", "id_pieza": "A medida", "cantidad": 1, "tecnologia": "FDM",
                        "material_cantidad": 40, "horas_placa": 3}, ("Corregir", correccion), "Corregido"),
        (f"{marca}-d", {"canal": "TikTok", "id_pieza": "R02", "cantidad": 3}, ("Rechazar", ""), "Rechazado"),
    ]
    resultados = []
    for cliente, pedido, decision, esperado in casos:
        print(f"→ {cliente}: {pedido['cantidad']} x {pedido['id_pieza']} por {pedido['canal']}")
        post_json(webhook, {"nombre": cliente, **pedido})
        if decision:
            pendiente = esperar(lambda: next((p for p in filas("pendientes.csv") if p["cliente"] == cliente), None),
                                240, f"aviso de aprobación de {cliente}")
            post_formulario(pendiente["enlace_aprobacion"], {"field-0": decision[0], "field-1": decision[1]})
        fila = esperar(lambda: next((r for r in filas("cotizaciones.csv") if r["cliente"] == cliente), None),
                       120, f"registro de {cliente}")
        ok = fila["decision"] == esperado and fila["origen_datos"] == "ficticio"
        if esperado != "Inválido":
            if pedido["id_pieza"] == "A medida":
                pz = {"tecnologia": pedido["tecnologia"], "material_cantidad": pedido["material_cantidad"],
                      "horas_placa": pedido["horas_placa"], "piezas_por_placa": 1,
                      "minutos_acabado": t["minutos_acabado_a_medida"]}
            else:
                pz = piezas[pedido["id_pieza"]]
            cot = costeo.cotizar(pz, pedido["cantidad"], pedido["canal"], t, canales)
            ok &= float(fila["precio_unitario"]) == cot["precio_unitario"] and float(fila["total"]) == cot["total"]
            print(f"   precio {fila['precio_unitario']} (Python {cot['precio_unitario']:.0f}) · IA: {fila['nota_ia']}")
        if decision and decision[0] == "Corregir":
            ok &= fila["mensaje_final"] == correccion
        print(f"   decisión: {fila['decision']} → {'bien' if ok else 'MAL'}")
        resultados.append(ok)
    nuevos_errores = len(filas("errores.csv")) - errores_antes
    print(f"\n{sum(resultados)} de {len(resultados)} pedidos bien · errores nuevos en el registro: {nuevos_errores}")
    return 0 if all(resultados) and nuevos_errores == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
