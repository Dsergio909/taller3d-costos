-- 00 · Esquema del taller (SQLite)
-- Las tablas son las mismas de los CSV de datos/ (o datos_reales/).
-- scripts/cargar_sqlite.py crea este esquema y carga los CSV.

DROP TABLE IF EXISTS tarifas;
CREATE TABLE tarifas (
    parametro     TEXT PRIMARY KEY,
    valor         REAL NOT NULL,
    unidad        TEXT,
    aplica_a      TEXT,
    descripcion   TEXT,
    origen_datos  TEXT NOT NULL
);

DROP TABLE IF EXISTS canales;
CREATE TABLE canales (
    canal         TEXT PRIMARY KEY,
    comision_pct  REAL NOT NULL CHECK (comision_pct >= 0 AND comision_pct < 1),
    descripcion   TEXT,
    origen_datos  TEXT NOT NULL
);

DROP TABLE IF EXISTS piezas;
CREATE TABLE piezas (
    id_pieza           TEXT PRIMARY KEY,
    nombre             TEXT NOT NULL,
    categoria          TEXT,
    tecnologia         TEXT NOT NULL CHECK (tecnologia IN ('Resina', 'FDM')),
    material_cantidad  REAL NOT NULL CHECK (material_cantidad >= 0),  -- ml (resina) o g (FDM)
    horas_placa        REAL NOT NULL CHECK (horas_placa >= 0),
    piezas_por_placa   INTEGER NOT NULL CHECK (piezas_por_placa > 0),
    minutos_acabado    REAL NOT NULL CHECK (minutos_acabado >= 0),
    precio_lista       REAL NOT NULL CHECK (precio_lista > 0),
    origen_datos       TEXT NOT NULL
);

DROP TABLE IF EXISTS clientes;
CREATE TABLE clientes (
    id_cliente    TEXT PRIMARY KEY,
    ciudad        TEXT,
    origen_datos  TEXT NOT NULL
);

DROP TABLE IF EXISTS pedidos;
CREATE TABLE pedidos (
    id_pedido     TEXT PRIMARY KEY,
    fecha         TEXT NOT NULL,          -- AAAA-MM-DD
    canal         TEXT NOT NULL REFERENCES canales (canal),
    id_cliente    TEXT NOT NULL REFERENCES clientes (id_cliente),
    estado        TEXT NOT NULL CHECK (estado IN ('Entregado', 'Cancelado', 'Devuelto')),
    origen_datos  TEXT NOT NULL
);

DROP TABLE IF EXISTS pedido_detalle;
CREATE TABLE pedido_detalle (
    id_pedido        TEXT NOT NULL REFERENCES pedidos (id_pedido),
    linea            INTEGER NOT NULL,
    id_pieza         TEXT NOT NULL REFERENCES piezas (id_pieza),
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario  REAL NOT NULL CHECK (precio_unitario > 0),
    descuento_pct    REAL NOT NULL CHECK (descuento_pct >= 0 AND descuento_pct < 1),
    origen_datos     TEXT NOT NULL,
    PRIMARY KEY (id_pedido, linea)
);

DROP TABLE IF EXISTS gastos;
CREATE TABLE gastos (
    id_gasto      TEXT PRIMARY KEY,
    fecha         TEXT NOT NULL,
    categoria     TEXT NOT NULL,
    concepto      TEXT,
    valor         REAL NOT NULL CHECK (valor >= 0),
    origen_datos  TEXT NOT NULL
);
