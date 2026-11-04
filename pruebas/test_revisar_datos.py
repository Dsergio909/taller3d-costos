"""El revisor de datos arregla los CSV que guarda Excel y atrapa los errores típicos al editar a mano."""
from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from comun import DATOS

import revisar_datos


def como_excel(origen: Path, destino: Path) -> None:
    """Guarda los CSV como lo haría Excel en español: ; , coma decimal, fecha dd/mm/aaaa, BOM y CRLF."""
    destino.mkdir(parents=True, exist_ok=True)
    for p in origen.glob("*.csv"):
        with open(p, encoding="utf-8", newline="") as f:
            filas = list(csv.reader(f))

        def celda(c: str) -> str:
            if len(c) == 10 and c[4] == "-" and c[7] == "-":
                return f"{c[8:]}/{c[5:7]}/{c[:4]}"
            return c.replace(".", ",") if c.replace(".", "", 1).replace("-", "", 1).isdigit() else c

        with open(destino / p.name, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f, delimiter=";", lineterminator="\r\n").writerows([[celda(c) for c in fila] for fila in filas])


def editar(carpeta: Path, archivo: str, cambio) -> None:
    ruta = carpeta / archivo
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    cols = list(filas[0])
    filas = cambio(filas, cols) or filas
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


class RevisarDatos(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copia(self, nombre: str = "datos") -> Path:
        destino = self.tmp / nombre
        shutil.copytree(DATOS, destino)
        return destino

    def test_diccionario_completo(self):
        from comun import RAIZ
        texto = (RAIZ / "docs" / "diccionario_de_datos.md").read_text(encoding="utf-8")
        for tabla, columnas in revisar_datos.ESQUEMA.items():
            self.assertIn(f"## {tabla}.csv", texto)
            for col in columnas:
                self.assertIn(f"`{col}`", texto, f"falta {tabla}.{col} en el diccionario")
        for t in revisar_datos.TARIFAS_NECESARIAS:
            self.assertIn(f"`{t}`", texto, f"falta la tarifa {t} en el diccionario")

    def test_datos_del_repo_estan_bien(self):
        errores, cambios = revisar_datos.revisar(DATOS)
        self.assertEqual((errores, cambios), ([], []))

    def test_arregla_csv_de_excel_sin_cambiar_ningun_valor(self):
        excel = self.tmp / "datos"
        como_excel(DATOS, excel)
        errores, cambios = revisar_datos.revisar(excel)
        self.assertEqual(errores, [])
        self.assertTrue(cambios, "debe notar el formato de Excel")
        errores, _ = revisar_datos.revisar(excel, arreglar=True)
        self.assertEqual(errores, [])
        for p in DATOS.glob("*.csv"):
            if p.stem in revisar_datos.OPCIONALES:
                continue
            self.assertEqual((excel / p.name).read_bytes(), p.read_bytes(), f"{p.name} quedó distinto")
            self.assertTrue((excel / "_originales" / p.name).exists(), "guarda los originales antes de arreglar")

    def test_datos_reales_deben_decir_real(self):
        reales = self.copia("datos_reales")
        errores, _ = revisar_datos.revisar(reales)
        self.assertTrue(any("debe ser «real»" in e for e in errores))

    def test_porcentaje_escrito_como_numero_entero(self):
        d = self.copia()
        editar(d, "tarifas.csv", lambda filas, _c: [f | ({"valor": "40"} if f["parametro"] == "margen_objetivo" else {})
                                                    for f in filas])
        errores, _ = revisar_datos.revisar(d)
        self.assertTrue(any("margen_objetivo" in e and "fracción" in e for e in errores), errores)

    def test_canal_que_no_existe(self):
        d = self.copia()
        editar(d, "pedidos.csv", lambda filas, _c: [filas[0] | {"canal": "Facebook"}] + filas[1:])
        errores, _ = revisar_datos.revisar(d)
        self.assertTrue(any("canal" in e and "Facebook" in e for e in errores), errores)

    def test_columna_borrada_y_tarifa_faltante(self):
        d = self.copia()
        editar(d, "tarifas.csv", lambda filas, _c: [f for f in filas if f["parametro"] != "mano_obra_hora"])
        errores, _ = revisar_datos.revisar(d)
        self.assertTrue(any("mano_obra_hora" in e for e in errores), errores)
        d2 = self.copia("otra/datos")
        texto = (d2 / "gastos.csv").read_text(encoding="utf-8").replace("valor,", "monto,", 1)
        (d2 / "gastos.csv").write_text(texto, encoding="utf-8", newline="\n")
        errores, _ = revisar_datos.revisar(d2)
        self.assertTrue(any("gastos.csv: faltan columnas" in e for e in errores), errores)

    def test_parametro_repetido(self):
        d = self.copia()
        editar(d, "tarifas.csv", lambda filas, _c: filas + [filas[0] | {"valor": "999"}])
        errores, _ = revisar_datos.revisar(d)
        self.assertTrue(any("repetido" in e and "resina_precio_litro" in e for e in errores), errores)

    def test_texto_donde_va_un_numero(self):
        d = self.copia()
        editar(d, "piezas.csv", lambda filas, _c: [filas[0] | {"horas_placa": "dos"}] + filas[1:])
        errores, _ = revisar_datos.revisar(d, arreglar=True)
        self.assertTrue(any("horas_placa" in e for e in errores), errores)
        self.assertFalse((d / "_originales").exists(), "con errores no toca los archivos")


if __name__ == "__main__":
    unittest.main()
