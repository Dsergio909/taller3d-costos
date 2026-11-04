"""Antes de subir algo: busca tus datos reales dentro de lo que iría al repo.

Solo corre en tu PC (en GitHub no existe datos_reales/). Compara datos_reales/ contra
todos los archivos que se subirían (los mismos que ve git) y avisa si aparece:
- el nombre de una pieza real o un código de cliente real;
- en los CSV públicos, una tarifa o un precio con el mismo valor exacto que el real
  (puede ser casualidad, pero conviene mirarlo);
- dentro del .pbix: cualquier nombre de pieza real (el .pbix guarda los datos adentro).

Uso:  python scripts/revisar_privacidad.py
"""
from __future__ import annotations

import csv
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REALES = RAIZ / "datos_reales"


def leer(nombre: str) -> list[dict]:
    ruta = REALES / f"{nombre}.csv"
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def archivos_publicos() -> list[Path]:
    salida = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=RAIZ, capture_output=True, check=True).stdout.decode("utf-8")
    return [RAIZ / r for r in salida.split("\0") if r and (RAIZ / r).is_file()]


def texto_de(p: Path) -> str:
    if p.suffix.lower() == ".pbix":
        partes = []
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                crudo = z.read(n)
                partes += [crudo.decode("utf-8", "ignore"), crudo.decode("utf-16-le", "ignore")]
        return "\n".join(partes)
    if p.suffix.lower() in {".png", ".jpg", ".pdf"}:
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    if not REALES.exists():
        print("No hay datos_reales/: no hay nada real que pueda filtrarse.")
        return 0
    nombres = {p["nombre"].strip() for p in leer("piezas") if len(p.get("nombre", "").strip()) >= 4}
    clientes = {c["id_cliente"].strip() for c in leer("clientes") if len(c.get("id_cliente", "").strip()) >= 4}
    valores_reales = {f["parametro"]: f["valor"].strip() for f in leer("tarifas")}
    precios_reales = {p["id_pieza"]: p["precio_lista"].strip() for p in leer("piezas")}
    hallazgos = []
    for p in archivos_publicos():
        texto = texto_de(p)
        rel = p.relative_to(RAIZ)
        for n in nombres:
            if n in texto:
                hallazgos.append(f"{rel}: aparece la pieza real «{n}»")
        for c in clientes:
            if c in texto and not c.startswith("CLI-"):
                hallazgos.append(f"{rel}: aparece el cliente real «{c}»")
        if p.suffix == ".csv" and p.name == "tarifas.csv":
            with open(p, encoding="utf-8-sig", newline="") as f:
                for fila in csv.DictReader(f):
                    real = valores_reales.get(fila["parametro"])
                    if real is not None and fila["valor"].strip() == real and fila["parametro"] not in (
                            "redondeo_precio",):
                        hallazgos.append(f"{rel}: {fila['parametro']} tiene el mismo valor que tu tarifa real ({real})")
    print(f"Revisé {len(archivos_publicos())} archivos públicos contra {len(nombres)} piezas, "
          f"{len(clientes)} clientes y {len(valores_reales)} tarifas reales.")
    if hallazgos:
        print(f"\n{len(hallazgos)} posible(s) filtración(es):")
        for h in hallazgos:
            print("  -", h)
        return 1
    print("Nada real en lo que se subiría.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
