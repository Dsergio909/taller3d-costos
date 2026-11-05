"""Cada cifra del README sale de los datos: si cambian los datos o el texto, esta prueba avisa."""
from __future__ import annotations

import unittest

from comun import DATOS, RAIZ

import cargar_sqlite
import costeo

SQL = cargar_sqlite.SQL


def es_pct(x: float) -> str:
    return f"{x:.1f}".replace(".", ",") + " %"


def en_pct(x: float) -> str:
    return f"{x:.1f}%"


def es_pesos(x: float) -> str:
    return "$" + f"{round(x):,}".replace(",", ".")


def en_pesos(x: float) -> str:
    return f"COP {round(x):,}"


class CifrasDelReadme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        texto = (RAIZ / "README.md").read_text(encoding="utf-8")
        cls.es, cls.en = texto.split('<a id="english"></a>')
        cls.con = cargar_sqlite.conectar(DATOS)

    def filas(self, archivo: str) -> list[dict]:
        cols, filas = cargar_sqlite.correr(self.con, SQL / archivo)
        return [dict(zip(cols, f)) for f in filas]

    def esta(self, es: str, en: str):
        self.assertTrue(es in self.es, f"el README en español no dice «{es}»")
        self.assertTrue(en in self.en, f"el README en inglés no dice «{en}»")

    def test_tamano_de_los_datos(self):
        n = lambda t: self.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: E731
        self.esta(f"{n('piezas')} piezas, {n('pedidos')} pedidos de 2025, {n('gastos')} gastos, {n('clientes')} clientes",
                  f"{n('piezas')} parts, {n('pedidos')} orders from 2025, {n('gastos')} expenses, {n('clientes')} customers")

    def test_numero_de_pruebas(self):
        cargador = unittest.TestLoader()
        total = cargador.discover(str(RAIZ / "pruebas"), top_level_dir=str(RAIZ / "pruebas")).countTestCases()
        self.esta(f"{total} pruebas", f"{total} tests")

    def test_resina_frente_a_fdm(self):
        f = {r["tecnologia"]: r for r in self.filas("02_resina_vs_fdm.sql")}
        self.esta(es_pct(f["Resina"]["pct_mano_obra"]), en_pct(f["Resina"]["pct_mano_obra"]))
        self.esta(es_pct(f["Resina"]["pct_material"]), en_pct(f["Resina"]["pct_material"]))
        self.esta(es_pct(f["FDM"]["pct_material"]), en_pct(f["FDM"]["pct_material"]))

    def test_repuesto_a_medida(self):
        t, canales = costeo.leer_tarifas(DATOS), costeo.leer_canales(DATOS)
        pieza = next(p for p in costeo.leer_piezas(DATOS) if p["nombre"] == "Repuesto a medida")
        c = costeo.costo_unitario(pieza, t)["costo_total"]
        lista = float(pieza["precio_lista"])
        self.esta(es_pct((lista - c) / lista * 100), en_pct((lista - c) / lista * 100))
        tiktok = (lista * (1 - canales["TikTok"]) - c) / lista * 100
        self.esta(es_pct(tiktok), en_pct(tiktok))
        sugerido = costeo.precio_sugerido(c, t, canales["WhatsApp"])
        self.esta(es_pesos(sugerido), en_pesos(sugerido))
        self.esta(es_pesos(lista), en_pesos(lista))
        vendidas = self.con.execute(
            "SELECT SUM(cantidad) FROM pedido_detalle JOIN pedidos USING (id_pedido) "
            "WHERE estado = 'Entregado' AND id_pieza = ?", (pieza["id_pieza"],)).fetchone()[0]
        self.esta(f"({vendidas} unidades)", f"({vendidas} units)")

    def test_canales(self):
        canal = {r["canal"]: r for r in self.filas("05_pedidos_por_canal.sql")}
        ganancia = {r["canal"]: r for r in self.filas("06_ganancia_por_canal.sql")}
        total = sum(r["ventas_netas"] for r in canal.values())
        w = canal["WhatsApp"]
        self.esta(es_pct(w["ventas_netas"] / total * 100), en_pct(w["ventas_netas"] / total * 100))
        self.esta(f"{w['pedidos']} de {sum(r['pedidos'] for r in canal.values())} pedidos",
                  f"{w['pedidos']} out of {sum(r['pedidos'] for r in canal.values())} orders")
        self.esta(es_pesos(w["ticket_promedio"]), en_pesos(w["ticket_promedio"]))
        # se mide dentro del mismo canal (sql/05): el texto tiene que decirlo
        self.esta(f"el {round(w['pct_clientes_que_vuelven'])} % de sus clientes vuelve a comprar por WhatsApp",
                  f"{round(w['pct_clientes_que_vuelven'])}% of its customers buy again through WhatsApp")
        self.esta(es_pct(ganancia["WhatsApp"]["margen_pct"]), en_pct(ganancia["WhatsApp"]["margen_pct"]))
        self.assertEqual(min(ganancia, key=lambda k: ganancia[k]["margen_pct"]), "WhatsApp", "WhatsApp ya no es el de menor margen")
        self.assertEqual(max(ganancia, key=lambda k: ganancia[k]["ganancia"]), "WhatsApp", "WhatsApp ya no es el que más deja")

    def test_que_pasa_si(self):
        e = {r["escenario"]: r["ganancia"] for r in self.filas("07_que_pasa_si.sql")}
        for nombre in ("Como va", "Subo 10 % y vendo 10 % menos", "Bajo 10 % y vendo 20 % más"):
            self.esta(es_pesos(e[nombre]), en_pesos(e[nombre]))
        # La diferencia se calcula sin redondear (igual que la tarjeta «Diferencia» del tablero).
        sin_redondeo = self.con.execute(
            "SELECT SUM(d.cantidad * 0.9 * (d.precio_unitario * (1 - d.descuento_pct) * 1.1 * (1 - k.comision_pct) - c.costo_total))"
            " - SUM(d.cantidad * (d.precio_unitario * (1 - d.descuento_pct) * (1 - k.comision_pct) - c.costo_total))"
            " FROM pedidos p JOIN pedido_detalle d USING (id_pedido) JOIN v_costo_pieza c USING (id_pieza)"
            " JOIN canales k USING (canal) WHERE p.estado = 'Entregado'").fetchone()[0]
        dif = sin_redondeo
        self.esta("+" + es_pesos(dif), "+" + en_pesos(dif))

    def test_gastos(self):
        total = self.con.execute("SELECT SUM(valor) FROM gastos").fetchone()[0]
        por = dict(self.con.execute("SELECT categoria, SUM(valor) FROM gastos GROUP BY 1").fetchall())
        for cat in ("Energía",):
            self.esta(es_pct(por[cat] / total * 100), en_pct(por[cat] / total * 100))

    def test_ganancia_por_hora(self):
        f = {r["nombre"]: r for r in self.filas("09_ganancia_por_hora_de_impresora.sql")}
        aretes, org = f["Aretes (par)"], f["Organizador de escritorio"]
        self.assertEqual(aretes["puesto_por_hora"], 1, "los aretes ya no son los que más dejan por hora")
        self.esta(es_pesos(aretes["ganancia_por_hora"]), en_pesos(aretes["ganancia_por_hora"]))
        self.esta(es_pesos(org["ganancia_por_hora"]), en_pesos(org["ganancia_por_hora"]))
        self.esta(es_pesos(org["ganancia_por_pieza"]), en_pesos(org["ganancia_por_pieza"]))
        piezas = {p["nombre"]: p for p in costeo.leer_piezas(DATOS)}
        self.esta(f"caben {piezas['Aretes (par)']['piezas_por_placa']} en una placa",
                  f"{piezas['Aretes (par)']['piezas_por_placa']} fit on one plate")
        self.esta(f"ocupa la FDM {float(piezas['Organizador de escritorio']['horas_placa']):g} horas",
                  f"FDM printer busy for {float(piezas['Organizador de escritorio']['horas_placa']):g} hours")

    def test_consultas_sql(self):
        n = len(list((q for q in SQL.glob("[0-9][0-9]_*.sql") if not q.name.startswith("00"))))
        self.esta(f"{n} consultas numeradas", f"{n} numbered and commented queries")

    def test_tasas_de_falla(self):
        t = costeo.leer_tarifas(DATOS)
        self.esta(f"{t['resina_tasa_fallas']:.0%}".replace("%", " %") + " en resina", f"{t['resina_tasa_fallas']:.0%} in resin")
        self.esta(f"{t['fdm_tasa_fallas']:.0%}".replace("%", " %") + " en FDM", f"{t['fdm_tasa_fallas']:.0%} in FDM")


if __name__ == "__main__":
    unittest.main()
