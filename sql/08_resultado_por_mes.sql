-- 08 · Mes a mes: ventas, gastos de caja y cambio contra el mes anterior (LAG)
-- Ojo: los gastos son lo que salió de la caja ese mes (resina por litro, filamento por
-- kilo, pauta, empaques). No es lo mismo que el costo por pieza: ahí no entran la
-- publicidad ni las herramientas, y sí entran la mano de obra y el desgaste.

WITH ventas AS (
    SELECT
        substr(p.fecha, 1, 7) AS mes,
        SUM(d.precio_unitario * d.cantidad * (1 - d.descuento_pct) * (1 - k.comision_pct)) AS ventas_sin_comision,
        COUNT(DISTINCT p.id_pedido) AS pedidos
    FROM pedidos AS p
    JOIN pedido_detalle AS d USING (id_pedido)
    JOIN canales AS k USING (canal)
    WHERE p.estado = 'Entregado'
    GROUP BY 1
),
caja AS (
    SELECT substr(fecha, 1, 7) AS mes, SUM(valor) AS gastos
    FROM gastos
    GROUP BY 1
)
SELECT
    v.mes,
    v.pedidos,
    ROUND(v.ventas_sin_comision, 0)                                     AS ventas_sin_comision,
    c.gastos,
    ROUND(v.ventas_sin_comision - c.gastos, 0)                          AS resultado_caja,
    ROUND((v.ventas_sin_comision - LAG(v.ventas_sin_comision) OVER (ORDER BY v.mes))
          / LAG(v.ventas_sin_comision) OVER (ORDER BY v.mes) * 100, 1)  AS pct_ventas_vs_mes_anterior
FROM ventas AS v
JOIN caja AS c USING (mes)
ORDER BY v.mes;
