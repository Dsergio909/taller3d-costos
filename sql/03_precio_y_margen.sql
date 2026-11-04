-- 03 · Precio y margen por pieza y por canal
-- Margen = (precio - costo - comisión del canal) / precio.
-- El precio sugerido busca el margen objetivo de tarifas.csv después de la comisión,
-- redondeado hacia arriba al múltiplo de «redondeo_precio» (igual que costeo.py).

WITH obj AS (
    SELECT
        MAX(CASE WHEN parametro = 'margen_objetivo' THEN valor END) AS margen_objetivo,
        MAX(CASE WHEN parametro = 'redondeo_precio' THEN valor END) AS redondeo
    FROM tarifas
),
margenes AS (
    SELECT
        c.id_pieza,
        c.nombre,
        c.tecnologia,
        k.canal,
        c.precio_lista,
        c.costo_total,
        (c.precio_lista * (1 - k.comision_pct) - c.costo_total) / c.precio_lista AS margen,
        -- cuántos «pasos» de redondeo (por ejemplo, de 500 pesos) cubre el precio exacto
        ROUND(c.costo_total / (1 - obj.margen_objetivo - k.comision_pct) / obj.redondeo, 9) AS pasos,
        obj.redondeo
    FROM v_costo_pieza AS c
    CROSS JOIN canales AS k
    CROSS JOIN obj
),
con_precio AS (
    -- techo en SQLite (no trae CEIL en todas las versiones): parte entera + 1 si sobra algo
    SELECT *, (CAST(pasos AS INTEGER) + (pasos > CAST(pasos AS INTEGER))) * redondeo AS precio_sugerido
    FROM margenes
)
SELECT
    id_pieza,
    nombre,
    tecnologia,
    canal,
    precio_lista,
    ROUND(costo_total, 0)                                    AS costo_unitario,
    ROUND(margen * 100, 1)                                   AS margen_pct,
    precio_sugerido,
    RANK() OVER (PARTITION BY canal ORDER BY margen ASC)     AS puesto_de_menor_margen
FROM con_precio
ORDER BY canal, margen;
