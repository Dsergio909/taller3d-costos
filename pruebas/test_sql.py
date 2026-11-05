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

    def test_mes_a_mes_no_pierde_meses(self):
        """Con datos reales puede haber un mes sin ventas o sin gastos: no debe desaparecer."""
        con = cargar_sqlite.conectar(DATOS)
        con.execute("UPDATE pedidos SET estado = 'Cancelado' WHERE substr(fecha, 1, 7) = '2025-06'")
        con.execute("DELETE FROM gastos WHERE substr(fecha, 1, 7) = '2025-03'")
        cols, filas = cargar_sqlite.correr(con, SQL / "08_resultado_por_mes.sql")
        meses = {f[0]: dict(zip(cols, f)) for f in filas}
        normal = {m["mes"]: m for m in self.correr("08_resultado_por_mes.sql")}
        self.assertEqual(list(meses), [f"2025-{m:02d}" for m in range(1, 13)], "faltan meses o están en desorden")
        junio, julio, marzo = meses["2025-06"], meses["2025-07"], meses["2025-03"]
        self.assertEqual((junio["pedidos"], junio["ventas_sin_comision"]), (0, 0))
        self.assertEqual(junio["gastos"], normal["2025-06"]["gastos"])
        self.assertAlmostEqual(junio["pct_ventas_vs_mes_anterior"], -100.0)  # contra mayo, no contra otro mes
        self.assertIsNone(julio["pct_ventas_vs_mes_anterior"], "no hay % de cambio contra un mes sin ventas")
        self.assertEqual(marzo["gastos"], 0)
        self.assertEqual(marzo["ventas_sin_comision"], normal["2025-03"]["ventas_sin_comision"])
        con.close()

    def test_tecnologia_desconocida_no_se_cobra_como_fdm(self):
        """Python y JS dan error con una tecnología rara; en SQL el esquema no la deja cargar."""
        import sqlite3
        con = cargar_sqlite.conectar(DATOS)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("UPDATE piezas SET tecnologia = 'SLS' WHERE id_pieza = 'F01'")
        # y si alguien quita esa regla del esquema, la vista deja el costo vacío en vez de cobrarla como FDM
        con.execute("PRAGMA ignore_check_constraints = ON")
        con.execute("UPDATE piezas SET tecnologia = 'SLS' WHERE id_pieza = 'F01'")
        costo = con.execute("SELECT costo_total FROM v_costo_pieza WHERE id_pieza = 'F01'").fetchone()[0]
        self.assertIsNone(costo)
        con.close()

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
            if f["dias_promedio_si_volvio_en_90"] is not None:  # misma ventana pareja de 90 días
                self.assertLessEqual(f["dias_promedio_si_volvio_en_90"], 90)
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
