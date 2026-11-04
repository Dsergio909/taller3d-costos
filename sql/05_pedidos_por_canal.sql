-- 05 · Pedidos por canal
-- Ventas netas = precio x cantidad x (1 - descuento), solo pedidos entregados.

WITH lineas AS (
    SELECT
        p.id_pedido, p.canal, p.id_cliente, p.estado,
        d.cantidad,
        d.precio_unitario * d.cantidad * (1 - d.descuento_pct) AS venta_neta
    FROM pedidos AS p
    JOIN pedido_detalle AS d USING (id_pedido)
),
por_pedido AS (
    SELECT id_pedido, canal, id_cliente, estado, SUM(cantidad) AS unidades, SUM(venta_neta) AS venta
    FROM lineas
    GROUP BY 1, 2, 3, 4
),
compras_cliente AS (            -- cuántos pedidos entregados tiene cada cliente en cada canal
    SELECT canal, id_cliente, COUNT(*) AS pedidos
    FROM por_pedido
    WHERE estado = 'Entregado'
    GROUP BY 1, 2
)
SELECT
    pp.canal,
    COUNT(*)                                                                    AS pedidos,
    SUM(CASE WHEN pp.estado = 'Entregado' THEN 1 ELSE 0 END)                    AS entregados,
    ROUND(AVG(CASE WHEN pp.estado <> 'Entregado' THEN 1.0 ELSE 0 END) * 100, 1) AS pct_cancelado_o_devuelto,
    SUM(CASE WHEN pp.estado = 'Entregado' THEN pp.unidades END)                 AS unidades,
    ROUND(SUM(CASE WHEN pp.estado = 'Entregado' THEN pp.venta END), 0)          AS ventas_netas,
    ROUND(AVG(CASE WHEN pp.estado = 'Entregado' THEN pp.venta END), 0)          AS ticket_promedio,
    (SELECT ROUND(AVG(CASE WHEN cc.pedidos > 1 THEN 1.0 ELSE 0 END) * 100, 1)
       FROM compras_cliente AS cc WHERE cc.canal = pp.canal)                    AS pct_clientes_que_vuelven
FROM por_pedido AS pp
GROUP BY pp.canal
ORDER BY ventas_netas DESC;
