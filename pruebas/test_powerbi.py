"""El proyecto de Power BI (PBIP) del repo está al día con el script y lee los datos ficticios."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from comun import RAIZ

import armar_powerbi

PROYECTO = RAIZ / "powerbi" / "proyecto"


class PowerBI(unittest.TestCase):
    def test_proyecto_al_dia_con_el_script(self):
        """Regenera el PBIP en una carpeta temporal y lo compara con el del repo."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with mock.patch.object(armar_powerbi, "RAIZ", tmp):
                (tmp / "scripts" / "powerbi_base").mkdir(parents=True)
                base = RAIZ / "scripts" / "powerbi_base" / "Fluent2-CY26SU10.json"
                (tmp / "scripts" / "powerbi_base" / base.name).write_bytes(base.read_bytes())
                destino = tmp / "powerbi" / "proyecto"
                armar_powerbi.escribir_modelo(destino, "datos")
                armar_powerbi.escribir_informe(destino)
            generados = sorted(p.relative_to(destino) for p in destino.rglob("*") if p.is_file())
            self.assertTrue(generados)
            for rel in generados:
                nuevo = (destino / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
                actual = (PROYECTO / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
                self.assertEqual(nuevo, actual, f"powerbi/proyecto/{rel} está desactualizado: corre scripts/armar_powerbi.py")

    def test_lee_datos_ficticios(self):
        expr = (PROYECTO / "taller3d-costos.SemanticModel" / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
        linea = next(l for l in expr.splitlines() if l.startswith("expression CarpetaDatos"))
        self.assertIn('\\datos\\"', linea)
        self.assertNotIn("datos_reales", linea)

    def test_medidas_documentadas(self):
        doc = (RAIZ / "dax" / "medidas.md").read_text(encoding="utf-8")
        for nombre, dax, *_ in armar_powerbi.MEDIDAS:
            self.assertIn(f"### {nombre}", doc)
            self.assertIn(dax, doc)

    def test_cada_pagina_avisa_el_origen_de_los_datos(self):
        paginas = PROYECTO / "taller3d-costos.Report" / "definition" / "pages"
        orden = json.loads((paginas / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
        self.assertEqual(len(orden), 4)
        for pid in orden:
            textos = [p.read_text(encoding="utf-8") for p in (paginas / pid / "visuals").rglob("visual.json")]
            self.assertTrue(any('"Origen de los datos"' in t for t in textos), f"la página {pid} no tiene el aviso")

    def test_formula_de_power_query_usa_todas_las_tarifas_de_costo(self):
        """Cada tarifa que usa costeo.py aparece en la consulta Piezas de Power Query."""
        import costeo, inspect
        fuente = inspect.getsource(costeo.costo_unitario)
        usadas = {p for p in armar_powerbi.PIEZAS_M.split("T[")[1:]}
        usadas = {u.split("]")[0] for u in usadas}
        for linea in fuente.splitlines():
            for trozo in linea.split('t["')[1:]:
                self.assertIn(trozo.split('"')[0], usadas)


if __name__ == "__main__":
    unittest.main()
