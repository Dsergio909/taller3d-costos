"""El flujo de n8n está al día, usa la misma fórmula y maneja errores."""
from __future__ import annotations

import csv
import json
import unittest

from comun import DATOS, NODE, RAIZ, correr_node

import armar_flujo

FLUJOS = RAIZ / "flujos"


def cargar(nombre: str) -> dict:
    return json.loads((FLUJOS / nombre).read_text(encoding="utf-8"))


def nodo(flujo: dict, nombre: str) -> dict:
    return next(n for n in flujo["nodes"] if n["name"] == nombre)


class Flujo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cot = cargar("cotizacion.json")
        cls.err = cargar("aviso_errores.json")
        cls.costeo_js = (FLUJOS / "costeo.js").read_text(encoding="utf-8")

    def test_json_al_dia_con_el_script(self):
        with open(DATOS / "piezas.csv", encoding="utf-8", newline="") as f:
            piezas = list(csv.DictReader(f))
        self.assertEqual(self.cot, json.loads(json.dumps(armar_flujo.flujo_cotizacion(piezas, self.costeo_js))),
                         "flujos/cotizacion.json está desactualizado: corre scripts/armar_flujo.py")
        self.assertEqual(self.err, json.loads(json.dumps(armar_flujo.flujo_errores())))

    def test_diagrama_al_dia(self):
        import diagrama_flujo
        actual = (FLUJOS / "diagrama_cotizacion.svg").read_text(encoding="utf-8")
        self.assertEqual(actual, diagrama_flujo.dibujar(self.cot), "corre scripts/diagrama_flujo.py")
        for n in self.cot["nodes"]:
            self.assertIn(n["name"].split()[0], actual)

    def test_usa_la_misma_formula(self):
        self.assertIn(self.costeo_js, nodo(self.cot, "Calcular cotización")["parameters"]["jsCode"])

    def test_lee_los_mismos_csv_del_tablero(self):
        selector = nodo(self.cot, "Leer tarifas y catálogo")["parameters"]["fileSelector"]
        self.assertIn("{tarifas,piezas,canales}.csv", selector)
        config = {a["name"]: a["value"] for a in
                  nodo(self.cot, "Configuración")["parameters"]["assignments"]["assignments"]}
        self.assertEqual(config["carpeta_datos"], "datos")

    def test_conexiones_validas(self):
        for flujo in (self.cot, self.err):
            nombres = {n["name"] for n in flujo["nodes"]}
            self.assertEqual(len(nombres), len(flujo["nodes"]), "nombres de nodo repetidos")
            for origen, salidas in flujo["connections"].items():
                self.assertIn(origen, nombres)
                for salida in salidas["main"]:
                    for destino in salida:
                        self.assertIn(destino["node"], nombres)

    def test_manejo_de_errores(self):
        ia = nodo(self.cot, "Redactar con IA local (Ollama)")
        self.assertTrue(ia["retryOnFail"])
        self.assertEqual(ia["maxTries"], 3)
        self.assertEqual(ia["onError"], "continueErrorOutput")
        salidas = self.cot["connections"][ia["name"]]["main"]
        self.assertEqual(salidas[1][0]["node"], "Plantilla sin IA", "si Ollama falla, sigue con la plantilla")
        self.assertEqual(self.cot["settings"]["errorWorkflow"], self.err["id"])
        self.assertEqual(self.err["nodes"][0]["type"], "n8n-nodes-base.errorTrigger")
        for flujo in (self.cot, self.err):
            for n in flujo["nodes"]:
                if n["type"] == "n8n-nodes-base.readWriteFile" and n["parameters"].get("operation") == "write":
                    self.assertTrue(n["parameters"]["options"]["append"], f"{n['name']} debe agregar, no reemplazar")

    def test_el_dueno_aprueba_antes_de_guardar(self):
        espera = nodo(self.cot, "Aprobación del dueño")
        self.assertEqual(espera["type"], "n8n-nodes-base.wait")
        self.assertEqual(espera["parameters"]["resume"], "form")
        opciones = [o["option"] for o in espera["parameters"]["formFields"]["values"][0]["fieldOptions"]["values"]]
        self.assertEqual(opciones, ["Aprobar", "Corregir", "Rechazar"])
        self.assertEqual(self.cot["connections"]["Aprobación del dueño"]["main"][0][0]["node"], "Armar registro")

    # --- El código de los nodos, corrido en Node con datos de prueba ---------------------------

    def _correr_nodo(self, nombre: str, entradas: list[dict], previos: dict[str, dict]) -> list[dict]:
        codigo = nodo(self.cot, nombre)["parameters"]["jsCode"]
        envoltura = f"""
            const entradas = {json.dumps(entradas, ensure_ascii=False)};
            const previos = {json.dumps(previos, ensure_ascii=False)};
            const $input = {{ all: () => entradas.map((json) => ({{ json }})), first: () => ({{ json: entradas[0] }}) }};
            const $ = (n) => ({{ first: () => ({{ json: previos[n] }}) }});
            const $execution = {{ id: 'prueba', resumeFormUrl: 'http://localhost/form-waiting/prueba' }};
            (async () => {{ {codigo} }})().then((r) => console.log(JSON.stringify(r.map((i) => i.json))));
        """
        return correr_node(envoltura)

    def _filas_csv(self) -> list[dict]:
        filas = []
        for nombre in ("tarifas", "piezas", "canales"):
            with open(DATOS / f"{nombre}.csv", encoding="utf-8", newline="") as f:
                filas += list(csv.DictReader(f))
        return filas

    def _pedido(self, **cambios) -> dict:
        p = {"origen": "webhook", "cliente": "Cliente de prueba", "canal": "Instagram", "id_pieza": "R03",
             "cantidad": 4, "a_medida": {}, "comentario": "", "carpeta_datos": "datos", "dias_entrega": "5"}
        p.update(cambios)
        return p

    @unittest.skipUnless(NODE, "Node.js no está instalado")
    def test_calcular_cotizacion(self):
        import costeo
        r = self._correr_nodo("Calcular cotización", self._filas_csv(), {"Configuración": self._pedido()})[0]
        self.assertTrue(r["ok"])
        esperado = costeo.cotizar(next(p for p in costeo.leer_piezas(DATOS) if p["id_pieza"] == "R03"), 4,
                                  "Instagram", costeo.leer_tarifas(DATOS), costeo.leer_canales(DATOS))
        self.assertEqual(r["precio_unitario"], esperado["precio_unitario"])
        self.assertEqual(r["total"], esperado["total"])
        self.assertEqual(r["origen_datos"], "ficticio")
        self.assertIn(r["total_texto"], r["prompt"])

    @unittest.skipUnless(NODE, "Node.js no está instalado")
    def test_pedidos_invalidos_no_llegan_a_la_ia(self):
        casos = {
            "cantidad cero": self._pedido(cantidad=0),
            "cantidad con decimales": self._pedido(cantidad=2.5),
            "pieza que no existe": self._pedido(id_pieza="Z99"),
            "canal raro": self._pedido(canal="Fax"),
            "a medida sin gramos": self._pedido(id_pieza="A medida", a_medida={"tecnologia": "FDM", "horas_placa": 2}),
        }
        for nombre, pedido in casos.items():
            r = self._correr_nodo("Calcular cotización", self._filas_csv(), {"Configuración": pedido})[0]
            self.assertFalse(r["ok"], nombre)
            self.assertTrue(r["motivo"], nombre)

    @unittest.skipUnless(NODE, "Node.js no está instalado")
    def test_pieza_a_medida(self):
        pedido = self._pedido(id_pieza="A medida", a_medida={"tecnologia": "FDM", "material_cantidad": 40, "horas_placa": 3})
        r = self._correr_nodo("Calcular cotización", self._filas_csv(), {"Configuración": pedido})[0]
        self.assertTrue(r["ok"])
        self.assertEqual(r["pieza"], "Pieza a medida")

    @unittest.skipUnless(NODE, "Node.js no está instalado")
    def test_control_de_cifras_de_la_ia(self):
        c = self._correr_nodo("Calcular cotización", self._filas_csv(), {"Configuración": self._pedido()})[0]
        bueno = (f"Hola, gracias por escribirnos. Las 4 miniaturas de 32 mm quedan en {c['precio_texto']} cada una, "
                 f"{c['total_texto']} en total, y te las entregamos en 5 días hábiles. Es impresión 3D en resina.")
        inventado = bueno + " El envío vale $10.000."
        sin_total = f"Hola, cada una vale {c['precio_texto']}."
        con_usuario = f"Hola andrea_92, " + bueno
        casos = [(bueno, True), (inventado, False), (sin_total, False), ("", False),
                 ("<think>calculo 99</think>" + bueno, True)]
        c_usuario = {**c, "cliente": "andrea_92"}
        r = self._correr_nodo("Revisar cifras del borrador", [{"response": con_usuario}], {"Calcular cotización": c_usuario})[0]
        self.assertTrue(r["ia_ok"], "los números del nombre del cliente no son cifras inventadas")
        for texto, ok in casos:
            r = self._correr_nodo("Revisar cifras del borrador", [{"response": texto}], {"Calcular cotización": c})[0]
            self.assertEqual(r["ia_ok"], ok, texto)
            if not ok:
                self.assertEqual(r["borrador"], c["plantilla"], "si falla el control, va la plantilla")

    @unittest.skipUnless(NODE, "Node.js no está instalado")
    def test_registro_con_cada_decision(self):
        c = self._correr_nodo("Calcular cotización", self._filas_csv(), {"Configuración": self._pedido()})[0]
        aviso = {**c, "borrador": c["plantilla"], "ia_ok": False, "nota_ia": "prueba"}
        casos = {"Aprobar": "Aprobado", "Corregir": "Corregido", "Rechazar": "Rechazado", None: "Sin respuesta en 24 h"}
        for decision, esperado in casos.items():
            formulario = {"Decisión": decision, "Texto corregido": "Texto, con coma y \"comillas\""} if decision else {}
            r = self._correr_nodo("Armar registro", [formulario],
                                  {"¿Pedido válido?": {"ok": True}, "Avisar al dueño": aviso})[0]
            self.assertEqual(r["decision"], esperado)
            fila = next(csv.reader([r["linea"]]))
            self.assertEqual(len(fila), len(armar_flujo.COLUMNAS_REGISTRO), "la línea CSV debe quedar bien armada")
        invalido = {**self._pedido(cantidad=0), "ok": False, "motivo": "Cantidad inválida", "origen_datos": "ficticio"}
        r = self._correr_nodo("Armar registro", [invalido], {"¿Pedido válido?": invalido, "Calcular cotización": invalido})[0]
        self.assertEqual(r["decision"], "Inválido")


if __name__ == "__main__":
    unittest.main()
