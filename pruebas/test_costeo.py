"""La fórmula de costo da lo mismo en Python, SQL, el CSV y el JavaScript del flujo de n8n."""
from __future__ import annotations

import csv
import json
import unittest

from comun import DATOS, NODE, correr_node

import cargar_sqlite
import costeo

COMPONENTES = ["material", "insumos", "energia", "maquina", "mano_obra", "fallas", "costo_total"]


class Costeo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = costeo.leer_tarifas(DATOS)
        cls.canales = costeo.leer_canales(DATOS)
        cls.piezas = costeo.leer_piezas(DATOS)
        cls.py = {p["id_pieza"]: costeo.costo_unitario(p, cls.t) for p in cls.piezas}
        cls.con = cargar_sqlite.conectar(DATOS)

    def test_un_caso_a_mano(self):
        """Ficha de juego (R01), calculada a mano con las tarifas ficticias.

        material 1,2 ml x 1,3 x 150 = 234 · insumos (6.000 + 2.000 + 1.000 + 1.000) / 40 = 250
        luz 1,5 h x 0,1 kW x 1.000 / 40 = 3,75 · máquina 1,5 x 400 / 40 = 15
        mano de obra (15/40 + 3) min / 60 x 15.000 = 843,75 · fallas 10 % = 134,65 → 1.481,15
        """
        c = self.py["R01"]
        self.assertAlmostEqual(c["material"], 234.0)
        self.assertAlmostEqual(c["insumos"], 250.0)
        self.assertAlmostEqual(c["energia"], 3.75)
        self.assertAlmostEqual(c["maquina"], 15.0)
        self.assertAlmostEqual(c["mano_obra"], 843.75)
        self.assertAlmostEqual(c["costo_total"], 1481.15)

    def test_python_igual_a_sql(self):
        filas = self.con.execute(f"SELECT id_pieza, {', '.join(COMPONENTES)} FROM v_costo_pieza").fetchall()
        self.assertEqual(len(filas), len(self.piezas))
        for fila in filas:
            for nombre, valor in zip(COMPONENTES, fila[1:]):
                self.assertAlmostEqual(valor, self.py[fila[0]][nombre], places=6, msg=f"{fila[0]} {nombre}")

    def test_python_igual_al_csv(self):
        with open(DATOS / "costo_por_pieza.csv", encoding="utf-8", newline="") as f:
            for fila in csv.DictReader(f):
                self.assertAlmostEqual(float(fila["costo_total"]), self.py[fila["id_pieza"]]["costo_total"], places=2)

    def test_precio_sugerido_python_igual_a_sql(self):
        _cols, filas = cargar_sqlite.correr(self.con, cargar_sqlite.SQL / "03_precio_y_margen.sql")
        self.assertEqual(len(filas), len(self.piezas) * len(self.canales))
        for id_pieza, _n, _t, canal, _pl, _c, _m, precio_sql, _r in filas:
            esperado = costeo.precio_sugerido(self.py[id_pieza]["costo_total"], self.t, self.canales[canal])
            self.assertEqual(precio_sql, esperado, f"{id_pieza} {canal}")

    @unittest.skipUnless(NODE, "Node.js no está instalado")
    def test_javascript_del_flujo_igual_a_python(self):
        js = correr_node("""
            const c = require('./flujos/costeo.js'); const fs = require('fs');
            const t = c.tablaTarifas(c.leerCsv(fs.readFileSync('datos/tarifas.csv', 'utf8')));
            const canales = Object.fromEntries(c.leerCsv(fs.readFileSync('datos/canales.csv', 'utf8'))
              .map((k) => [k.canal, Number(k.comision_pct)]));
            const salida = {};
            for (const p of c.leerCsv(fs.readFileSync('datos/piezas.csv', 'utf8'))) {
              salida[p.id_pieza] = { costo: c.costoUnitario(p, t),
                cot: Object.fromEntries(Object.keys(canales).map((k) => [k, c.cotizar(p, 7, k, t, canales)])) };
            }
            console.log(JSON.stringify(salida));
        """)
        for id_pieza, r in js.items():
            for nombre in COMPONENTES:
                self.assertAlmostEqual(r["costo"][nombre], self.py[id_pieza][nombre], places=6)
            pieza = next(p for p in self.piezas if p["id_pieza"] == id_pieza)
            for canal, cot in r["cot"].items():
                esperado = costeo.cotizar(pieza, 7, canal, self.t, self.canales)
                for k, v in esperado.items():
                    self.assertAlmostEqual(cot[k], v, places=6, msg=f"{id_pieza} {canal} {k}")

    def test_entradas_malas(self):
        pieza = dict(self.piezas[0])
        with self.assertRaises(ValueError):
            costeo.cotizar(pieza, 0, "TikTok", self.t, self.canales)
        with self.assertRaises(ValueError):
            costeo.cotizar(pieza, 2, "Fax", self.t, self.canales)
        with self.assertRaises(ValueError):
            costeo.costo_unitario({**pieza, "piezas_por_placa": 0}, self.t)
        with self.assertRaises(ValueError):
            costeo.costo_unitario({**pieza, "tecnologia": "Láser"}, self.t)
        with self.assertRaises(ValueError):
            costeo.precio_sugerido(1000, {**self.t, "margen_objetivo": 0.95}, 0.10)

    def test_el_precio_sugerido_cumple_el_margen(self):
        for p in self.piezas:
            for canal in self.canales:
                cot = costeo.cotizar(p, 1, canal, self.t, self.canales)
                self.assertGreaterEqual(cot["margen_pct"] + 1e-9, self.t["margen_objetivo"], f"{p['id_pieza']} {canal}")
                self.assertEqual(cot["precio_unitario"] % self.t["redondeo_precio"], 0)


if __name__ == "__main__":
    unittest.main()
