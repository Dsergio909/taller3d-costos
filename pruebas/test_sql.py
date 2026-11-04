"""Las consultas corren y sus resultados cuadran entre sí y con los CSV."""
from __future__ import annotations

import unittest

from comun import DATOS

import cargar_sqlite

SQL = cargar_sqlite.SQL


class ConsultasSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = cargar_sqlite.conectar(DATOS)

    def correr(self, nombre: str) -> list[dict]:
        cols, filas = cargar_sqlite.correr(self.con, SQL / nombre)
        return [dict(zip(cols, f)) for f in filas]

    def test_todas_corren(self):
        archivos = sorted((q for q in SQL.glob("[0-9][0-9]_*.sql") if not q.name.startswith("00")))
        self.assertEqual(len(archivos), 10)
        for ruta in archivos:
            _c, filas = cargar_sqlite.correr(self.con, ruta)
            self.assertGreater(len(filas), 0, ruta.name)

    def test_pedidos_por_canal_suman_el_total(self):
        filas = self.correr("05_pedidos_por_canal.sql")
        self.assertEqual(sum(f["pedidos"] for f in filas), 549)
        self.assertAlmostEqual(sum(f["ventas_netas"] for f in filas), 25_654_750, delta=2)

    def test_ganancia_por_canal_igual_al_escenario_actual(self):
        ganancia_canales = sum(f["ganancia"] for f in self.correr("06_ganancia_por_canal.sql"))
        actual = next(f for f in self.correr("07_que_pasa_si.sql") if f["escenario"] == "Como va")
        self.assertAlmostEqual(ganancia_canales, actual["ganancia"], delta=3)

    def test_gastos_cuadran(self):
        filas = self.correr("04_gastos_por_mes.sql")
        total = self.con.execute("SELECT SUM(valor) FROM gastos").fetchone()[0]
        self.assertAlmostEqual(sum(f["gasto"] for f in filas), total)
        self.assertEqual(len({f["mes"] for f in filas}), 12)
        diciembre = [f for f in filas if f["mes"] == "2025-12"]
        self.assertAlmostEqual(diciembre[0]["acumulado_año"], total)

    def test_mes_a_mes_cuadra_con_canales(self):
        meses = self.correr("08_resultado_por_mes.sql")
        canales = self.correr("06_ganancia_por_canal.sql")
        self.assertEqual(len(meses), 12)
        self.assertAlmostEqual(sum(m["ventas_sin_comision"] for m in meses),
                               sum(c["ventas_netas"] - c["comision"] for c in canales), delta=15)
        self.assertIsNone(meses[0]["pct_ventas_vs_mes_anterior"])

    def test_ganancia_por_hora(self):
        filas = self.correr("09_ganancia_por_hora_de_impresora.sql")
        self.assertEqual(len(filas), 17)
        import costeo
        t = costeo.leer_tarifas(DATOS)
        piezas = {p["id_pieza"]: p for p in costeo.leer_piezas(DATOS)}
        for f in filas:  # ganancia por hora = (precio - costo) / (horas de placa / piezas por placa)
            p = piezas[f["id_pieza"]]
            esperado = ((float(p["precio_lista"]) - costeo.costo_unitario(p, t)["costo_total"])
                        / (float(p["horas_placa"]) / float(p["piezas_por_placa"])))
            self.assertAlmostEqual(f["ganancia_por_hora"], esperado, delta=0.6, msg=f["id_pieza"])
        self.assertEqual(filas[0]["puesto_por_hora"], 1)
        self.assertEqual([f["ganancia_por_hora"] for f in filas], sorted((f["ganancia_por_hora"] for f in filas), reverse=True))

    def test_cohortes(self):
        filas = self.correr("10_cohortes_de_clientes.sql")
        con_compras = self.con.execute(
            "SELECT COUNT(DISTINCT id_cliente) FROM pedidos WHERE estado = 'Entregado'").fetchone()[0]
        self.assertEqual(sum(f["clientes_nuevos"] for f in filas), con_compras, "cada cliente cae en una sola cohorte")
        for f in filas:
            self.assertLessEqual(f["volvieron_en_90_dias"], f["con_90_dias_para_mirar"])
            self.assertLessEqual(f["con_90_dias_para_mirar"], f["clientes_nuevos"])
        self.assertLess(filas[-1]["con_90_dias_para_mirar"], filas[-1]["clientes_nuevos"],
                        "el último trimestre no tiene 90 días completos: no se cuenta como si no volvieran")

    def test_resina_y_fdm(self):
        filas = {f["tecnologia"]: f for f in self.correr("02_resina_vs_fdm.sql")}
        self.assertEqual(set(filas), {"Resina", "FDM"})
        for f in filas.values():
            suma = f["pct_material"] + f["pct_insumos"] + f["pct_luz_y_maquina"] + f["pct_mano_obra"] + f["pct_fallas"]
            self.assertAlmostEqual(suma, 100, delta=0.3)


if __name__ == "__main__":
    unittest.main()
