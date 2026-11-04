-- 04 · Gastos del taller por mes y por categoría
-- Con el acumulado del año (funciones de ventana) y el peso de cada categoría en el mes.

WITH por_mes AS (
    SELECT
        substr(fecha, 1, 7) AS mes,
        categoria,
        SUM(valor)          AS gasto
    FROM gastos
    GROUP BY 1, 2
)
SELECT
    mes,
    categoria,
    gasto,
    ROUND(gasto * 100.0 / SUM(gasto) OVER (PARTITION BY mes), 1)      AS pct_del_mes,
    SUM(gasto) OVER (PARTITION BY categoria ORDER BY mes)             AS acumulado_categoria,
    -- ORDER BY mes sin ROWS: suma todos los meses hasta el actual, completo
    SUM(gasto) OVER (ORDER BY mes)                                    AS acumulado_año
FROM por_mes
ORDER BY mes, gasto DESC;
