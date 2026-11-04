-- 06 · ¿Cuánto deja cada canal después de costos y comisiones?
-- Ganancia = ventas netas - costo de las piezas - comisión del canal (pedidos entregados).

WITH lineas AS (
    SELECT
        p.canal,
        d.precio_unitario * d.cantidad * (1 - d.descuento_pct)   AS venta_neta,
        c.costo_total * d.cantidad                               AS costo
    FROM pedidos AS p
    JOIN pedido_detalle AS d USING (id_pedido)
    JOIN v_costo_pieza AS c USING (id_pieza)
    WHERE p.estado = 'Entregado'
)
SELECT
    l.canal,
    ROUND(SUM(l.venta_neta), 0)                                         AS ventas_netas,
    ROUND(SUM(l.costo), 0)                                              AS costo_piezas,
    ROUND(SUM(l.venta_neta) * k.comision_pct, 0)                        AS comision,
    ROUND(SUM(l.venta_neta) * (1 - k.comision_pct) - SUM(l.costo), 0)   AS ganancia,
    ROUND((SUM(l.venta_neta) * (1 - k.comision_pct) - SUM(l.costo))
          / SUM(l.venta_neta) * 100, 1)                                 AS margen_pct
FROM lineas AS l
JOIN canales AS k USING (canal)
GROUP BY l.canal, k.comision_pct
ORDER BY ganancia DESC;
