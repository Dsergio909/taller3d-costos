-- 07 · ¿Qué pasa si cambio el precio y vendo más o menos?
-- Toma lo vendido en el año (pedidos entregados) y lo recalcula con cada escenario:
-- precio x (1 + ajuste_precio) y cantidad x (1 + ajuste_cantidad).
-- Es el mismo cálculo de los parámetros «qué pasa si» del tablero.

WITH escenarios (escenario, ajuste_precio, ajuste_cantidad) AS (
    VALUES
        ('Como va',                       0.00,  0.00),
        ('Subo 10 % y vendo igual',       0.10,  0.00),
        ('Subo 10 % y vendo 10 % menos',  0.10, -0.10),
        ('Bajo 10 % y vendo 10 % más',   -0.10,  0.10),
        ('Bajo 10 % y vendo 20 % más',   -0.10,  0.20)
),
base AS (
    SELECT
        p.canal,
        d.cantidad,
        d.precio_unitario * (1 - d.descuento_pct) AS precio_neto,
        c.costo_total
    FROM pedidos AS p
    JOIN pedido_detalle AS d USING (id_pedido)
    JOIN v_costo_pieza AS c USING (id_pieza)
    WHERE p.estado = 'Entregado'
)
SELECT
    e.escenario,
    ROUND(SUM(b.precio_neto * (1 + e.ajuste_precio) * b.cantidad * (1 + e.ajuste_cantidad)), 0) AS ventas,
    ROUND(SUM(
        b.precio_neto * (1 + e.ajuste_precio) * (1 - k.comision_pct) * b.cantidad * (1 + e.ajuste_cantidad)
        - b.costo_total * b.cantidad * (1 + e.ajuste_cantidad)
    ), 0) AS ganancia
FROM escenarios AS e
CROSS JOIN base AS b
JOIN canales AS k USING (canal)
GROUP BY e.escenario, e.ajuste_precio, e.ajuste_cantidad
ORDER BY ganancia DESC;
