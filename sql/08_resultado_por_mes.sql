-- 08 · Mes a mes: ventas, gastos de caja y cambio contra el mes anterior (LAG)
-- Ojo: los gastos son lo que salió de la caja ese mes (resina por litro, filamento por
-- kilo, pauta, empaques). No es lo mismo que el costo por pieza: ahí no entran la
-- publicidad ni las herramientas, y sí entran la mano de obra y el desgaste.
-- Con datos reales puede haber un mes con gastos y sin ventas (o al revés). Por eso se arma
-- primero la lista completa de meses y las ventas y los gastos se pegan con LEFT JOIN y 0:
-- así ningún mes desaparece y el LAG siempre compara contra el mes de verdad anterior.

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
),
limites AS (                    -- primer y último mes con pedidos o gastos
    SELECT MIN(mes) AS primero, MAX(mes) AS ultimo
    FROM (SELECT mes FROM ventas UNION SELECT mes FROM caja)
),
meses(mes) AS (                 -- todos los meses entre los dos, sin saltos
    SELECT primero FROM limites
    UNION ALL
    SELECT strftime('%Y-%m', date(m.mes || '-01', '+1 month'))
    FROM meses AS m, limites AS l
    WHERE m.mes < l.ultimo
),
juntos AS (
    SELECT
        m.mes,
        COALESCE(v.pedidos, 0)             AS pedidos,
        COALESCE(v.ventas_sin_comision, 0) AS ventas_sin_comision,
        COALESCE(c.gastos, 0)              AS gastos
    FROM meses AS m
    LEFT JOIN ventas AS v USING (mes)
    LEFT JOIN caja   AS c USING (mes)
)
SELECT
    mes,
    pedidos,
    ROUND(ventas_sin_comision, 0)                                       AS ventas_sin_comision,
    gastos,
    ROUND(ventas_sin_comision - gastos, 0)                              AS resultado_caja,
    -- si el mes anterior no vendió nada, el cambio en % no existe (queda vacío)
    ROUND((ventas_sin_comision - LAG(ventas_sin_comision) OVER (ORDER BY mes))
          / NULLIF(LAG(ventas_sin_comision) OVER (ORDER BY mes), 0) * 100, 1) AS pct_ventas_vs_mes_anterior
FROM juntos
ORDER BY mes;
