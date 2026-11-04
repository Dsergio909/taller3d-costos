"""Regla de oro: el repo público nunca tiene datos reales del taller.

Falla si:
- aparece un CSV sin la columna origen_datos o con una fila que no diga «ficticio»;
- aparece cualquier archivo dentro de una carpeta datos_reales/;
- .gitignore deja de excluir datos_reales/, registro/ o .env;
- hay claves, tokens, teléfonos, correos, IPs de la casa o rutas personales del PC;
- un flujo de n8n trae credenciales guardadas;
- el .pbix lee de datos_reales/ en vez de datos/.
"""
from __future__ import annotations

import csv
import io
import json
import re
import unittest
import zipfile
from pathlib import Path

from comun import RAIZ, archivos_del_repo

TEXTO = {".md", ".py", ".js", ".json", ".sql", ".yml", ".yaml", ".csv", ".txt", ".ps1", ".sh", ".tmdl",
         ".pbir", ".pbism", ".pbip", ".m", ".example", ".gitignore", ".gitattributes", ".svg", ".html"}

# Patrones que no deben aparecer en ningún archivo público.
PROHIBIDOS = {
    "ruta personal de Windows": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]", re.I),
    "carpeta de Drive": re.compile(r"Mi unidad|My Drive", re.I),
    "correo": re.compile(r"[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+\.[A-Za-z]{2,}"),
    "teléfono celular de Colombia": re.compile(r"(?<![\d.,$])(?:\+?57[\s-]?)?3\d{2}[\s-]?\d{3}[\s-]?\d{4}(?![\d.,])"),
    "token de bot de Telegram": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "clave de API": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{35})"),
    "IP de una red de la casa": re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
}


def _es_texto(p: Path) -> bool:
    return p.suffix.lower() in TEXTO or p.name in {".gitignore", ".gitattributes", ".env.example", "LICENSE"}


class Privacidad(unittest.TestCase):
    def setUp(self):
        self.archivos = archivos_del_repo()

    def test_no_hay_carpeta_datos_reales(self):
        malos = [p for p in self.archivos if "datos_reales" in p.relative_to(RAIZ).parts]
        self.assertEqual(malos, [], "Hay archivos de datos_reales/ que se subirían al repo")

    def test_todo_csv_esta_marcado_ficticio(self):
        csvs = [p for p in self.archivos if p.suffix.lower() == ".csv"]
        self.assertGreater(len(csvs), 0)
        for p in csvs:
            with open(p, encoding="utf-8", newline="") as f:
                filas = list(csv.DictReader(f))
            nombre = p.relative_to(RAIZ)
            self.assertTrue(filas, f"{nombre} está vacío")
            self.assertIn("origen_datos", filas[0], f"{nombre} no tiene la columna origen_datos")
            malas = [i for i, fila in enumerate(filas, 2) if fila["origen_datos"] != "ficticio"]
            self.assertEqual(malas, [], f"{nombre}: filas sin la marca «ficticio» (líneas {malas[:5]})")

    def test_gitignore_protege_lo_privado(self):
        reglas = (RAIZ / ".gitignore").read_text(encoding="utf-8").split()
        for regla in ("datos_reales/", "registro/", ".env", ".n8n_local/"):
            self.assertIn(regla, reglas, f".gitignore debe excluir {regla}")

    def test_no_se_sube_el_env(self):
        self.assertFalse([p for p in self.archivos if p.name == ".env"], "El archivo .env no se sube")
        ejemplo = RAIZ / ".env.example"
        if ejemplo.exists():
            for linea in ejemplo.read_text(encoding="utf-8").splitlines():
                if "=" in linea and not linea.lstrip().startswith("#"):
                    clave, valor = linea.split("=", 1)
                    if any(s in clave.upper() for s in ("PASSWORD", "TOKEN", "KEY", "SECRET")):
                        self.assertEqual(valor.strip(), "", f".env.example trae un valor en {clave}")

    def test_sin_claves_telefonos_ni_rutas(self):
        este = Path(__file__).resolve()
        hallazgos = []
        for p in self.archivos:
            if p.resolve() == este or not _es_texto(p):
                continue
            texto = p.read_text(encoding="utf-8", errors="ignore")
            for nombre, patron in PROHIBIDOS.items():
                for m in patron.finditer(texto):
                    hallazgos.append(f"{p.relative_to(RAIZ)}: {nombre} → {m.group(0)[:40]}")
        self.assertEqual(hallazgos, [], "\n".join(hallazgos))

    def test_flujos_sin_credenciales(self):
        for p in (RAIZ / "flujos").glob("*.json"):
            flujo = json.loads(p.read_text(encoding="utf-8"))
            for n in flujo["nodes"]:
                self.assertNotIn("credentials", n, f"{p.name}: el nodo «{n['name']}» trae credenciales")

    def test_pbix_es_la_version_ficticia(self):
        """El .pbix guarda los datos adentro, así que se revisa lo que sí se puede leer de él.

        Ojo: Power BI 2.159 guarda las consultas de Power Query dentro del modelo comprimido
        (DataModel), que no se puede leer sin Power BI. Por eso se revisa:
        - si trae la parte DataMashup (versiones viejas), que no lea datos_reales;
        - que tenga las mismas páginas del proyecto PBIP del repo (que sí lee datos\\, ver test_powerbi);
        - que cada página tenga la tarjeta «Origen de los datos», que dice «DATOS REALES · no publicar»
          si alguien cargó datos reales: así se ve en el .pbix, el PDF y las capturas.
        """
        paginas_pbip = {p.name for p in (RAIZ / "powerbi" / "proyecto" / "taller3d-costos.Report" /
                                         "definition" / "pages").iterdir() if p.is_dir()}
        for p in [p for p in self.archivos if p.suffix.lower() == ".pbix"]:
            with zipfile.ZipFile(p) as z:
                nombres = z.namelist()
                if "DataMashup" in nombres:
                    crudo = z.read("DataMashup")
                    largo = int.from_bytes(crudo[4:8], "little")
                    with zipfile.ZipFile(io.BytesIO(crudo[8:8 + largo])) as paquete:
                        m = paquete.read("Formulas/Section1.m").decode("utf-8", "ignore")
                    self.assertNotIn("datos_reales", m.lower(), f"{p.name} apunta a datos_reales")
                visuales: dict[str, list[str]] = {}
                for n in nombres:
                    partes = n.split("/")
                    if n.startswith("Report/definition/pages/") and n.endswith("visual.json"):
                        visuales.setdefault(partes[3], []).append(z.read(n).decode("utf-8", "ignore"))
            self.assertEqual(set(visuales), paginas_pbip, f"{p.name} no tiene las mismas páginas del proyecto")
            for pagina, textos in visuales.items():
                self.assertTrue(any('"Origen de los datos"' in t for t in textos),
                                f"{p.name}: la página {pagina} no muestra el aviso del origen de los datos")


if __name__ == "__main__":
    unittest.main()
