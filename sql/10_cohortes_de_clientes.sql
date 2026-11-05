-- 10 · Cohortes: de los clientes nuevos de cada trimestre, ¿cuántos volvieron a comprar?
-- Cohorte = trimestre del primer pedido entregado.
-- Ojo con la trampa: un cliente que llegó en diciembre tuvo pocos días para volver antes de
-- que se acaben los datos. Para comparar parejo se mide «volvió en los primeros 90 días» y
-- solo se cuentan los clientes que tuvieron 90 días completos para hacerlo.
-- Los días promedio hasta volver usan la misma ventana: solo los que volvieron en esos 90 días.

WITH entregados AS (
    SELECT id_cliente, id_pedido, fecha, canal
    FROM pedidos
    WHERE estado = 'Entregado'
),
numerados AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY id_cliente ORDER BY fecha, id_pedido) AS n_compra,
        LEAD(fecha)  OVER (PARTITION BY id_cliente ORDER BY fecha, id_pedido) AS siguiente_fecha
    FROM entregados
),
primeras AS (
    SELECT
        id_cliente,
        canal AS canal_de_llegada,
        fecha AS primera_fecha,
        substr(fecha, 1, 4) || '-T' || ((CAST(substr(fecha, 6, 2) AS INTEGER) + 2) / 3) AS cohorte,
        julianday(siguiente_fecha) - julianday(fecha) AS dias_hasta_volver
    FROM numerados
    WHERE n_compra = 1
),
corte AS (                      -- último día con datos
    SELECT MAX(fecha) AS ultima_fecha FROM entregados
)
SELECT
    p.cohorte,
    COUNT(*)                                                                    AS clientes_nuevos,
    SUM(julianday(c.ultima_fecha) - julianday(p.primera_fecha) >= 90)          AS con_90_dias_para_mirar,
    SUM(julianday(c.ultima_fecha) - julianday(p.primera_fecha) >= 90
        AND p.dias_hasta_volver <= 90)                                          AS volvieron_en_90_dias,
    ROUND(100.0 * SUM(julianday(c.ultima_fecha) - julianday(p.primera_fecha) >= 90 AND p.dias_hasta_volver <= 90)
          / NULLIF(SUM(julianday(c.ultima_fecha) - julianday(p.primera_fecha) >= 90), 0), 1) AS pct_volvieron_en_90_dias,
    ROUND(AVG(CASE WHEN julianday(c.ultima_fecha) - julianday(p.primera_fecha) >= 90
                    AND p.dias_hasta_volver <= 90 THEN p.dias_hasta_volver END), 0) AS dias_promedio_si_volvio_en_90
FROM primeras AS p
CROSS JOIN corte AS c
GROUP BY p.cohorte
ORDER BY p.cohorte;
