"""Los datos ficticios son siempre los mismos y cuadran con totales conocidos."""
from __future__ import annotations

import csv
import filecmp
import tempfile
import unittest
from pathlib import Path

from comun import DATOS

import generar_datos_ficticios as gen


def leer(nombre: str) -> list[dict]:
    with open(DATOS / f"{nombre}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class Datos(unittest.TestCase):
    def test_el_generador_da_los_mismos_archivos(self):
        """Semilla fija: regenerar da archivos idénticos a los del repo."""
        with tempfile.TemporaryDirectory() as tmp:
            gen.generar(Path(tmp))
            nuevos = sorted(p.name for p in Path(tmp).glob("*.csv"))
            self.assertEqual(nuevos, sorted(p.name for p in DATOS.glob("*.csv")))
            for nombre in nuevos:
                self.assertTrue(filecmp.cmp(Path(tmp) / nombre, DATOS / nombre, shallow=False),
                                f"datos/{nombre} no coincide con el generador: córrelo de nuevo")

    def test_totales_conocidos(self):
        self.assertEqual(len(leer("pedidos")), 549)
        self.assertEqual(len(leer("pedido_detalle")), 718)
        self.assertEqual(len(leer("gastos")), 77)
        self.assertEqual(len(leer("clientes")), 320)
        self.assertEqual(len(leer("piezas")), 17)
        self.assertEqual(len(leer("canales")), 3)
        entregados = {p["id_pedido"] for p in leer("pedidos") if p["estado"] == "Entregado"}
        ventas = sum(float(d["precio_unitario"]) * int(d["cantidad"]) * (1 - float(d["descuento_pct"]))
                     for d in leer("pedido_detalle") if d["id_pedido"] in entregados)
        self.assertAlmostEqual(ventas, 25_654_750, places=2)
        self.assertEqual(sum(float(g["valor"]) for g in leer("gastos")), 9_622_500)

    def test_integridad(self):
        piezas = {p["id_pieza"] for p in leer("piezas")}
        pedidos = {p["id_pedido"] for p in leer("pedidos")}
        clientes = {c["id_cliente"] for c in leer("clientes")}
        canales = {c["canal"] for c in leer("canales")}
        for d in leer("pedido_detalle"):
            self.assertIn(d["id_pieza"], piezas)
            self.assertIn(d["id_pedido"], pedidos)
        for p in leer("pedidos"):
            self.assertIn(p["id_cliente"], clientes)
            self.assertIn(p["canal"], canales)
            self.assertTrue(p["fecha"].startswith("2025-"))

    def test_sin_datos_personales(self):
        """Los clientes son solo un código y una ciudad."""
        self.assertEqual(set(leer("clientes")[0]), {"id_cliente", "ciudad", "origen_datos"})

    def test_no_escribe_en_datos_reales(self):
        import subprocess, sys
        r = subprocess.run([sys.executable, str(Path(gen.__file__)), "--salida", "x/datos_reales"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
