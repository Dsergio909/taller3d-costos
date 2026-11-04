"""Utilidades compartidas por las pruebas."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
sys.path.insert(0, str(RAIZ / "scripts"))

NODE = shutil.which("node")


def archivos_del_repo() -> list[Path]:
    """Lo que está o estaría en el repo: archivos con seguimiento + nuevos no ignorados.

    Si no hay git (por ejemplo, alguien bajó el .zip), recorre la carpeta sin
    .git ni las carpetas que .gitignore deja por fuera.
    """
    try:
        salida = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=RAIZ, capture_output=True, check=True,
        ).stdout.decode("utf-8")
        rutas = [RAIZ / r for r in salida.split("\0") if r]
        return [r for r in rutas if r.is_file()]
    except (OSError, subprocess.CalledProcessError):
        fuera = {".git", "datos_reales", "registro", ".n8n_local", "__pycache__", "node_modules"}
        return [p for p in RAIZ.rglob("*") if p.is_file() and not (fuera & set(p.relative_to(RAIZ).parts))]


def correr_node(codigo: str) -> object:
    """Corre JavaScript en Node y devuelve lo que imprima como JSON."""
    r = subprocess.run([NODE, "-e", codigo], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise AssertionError("Node falló:\n" + r.stderr)
    return json.loads(r.stdout)
