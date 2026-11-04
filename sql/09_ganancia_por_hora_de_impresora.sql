-- 09 · ¿Qué pieza deja más plata por cada hora de impresora?
-- La impresora es el cuello de botella del taller: si está ocupada con una pieza, no
-- imprime otra. Por eso importa la ganancia por hora de máquina, no solo el margen %.
-- Horas por pieza = horas de la placa / piezas que caben en la placa (la placa va llena).

WITH por_pieza AS (
    SELECT
        c.id_pieza,
        c.nombre,
        c.tecnologia,
        c.precio_lista - c.costo_total                        AS ganancia_unitaria,
        p.horas_placa * 1.0 / p.piezas_por_placa              AS horas_por_pieza
    FROM v_costo_pieza AS c
    JOIN piezas AS p USING (id_pieza)
)
SELECT
    id_pieza,
    nombre,
    tecnologia,
    ROUND(ganancia_unitaria, 0)                                               AS ganancia_por_pieza,
    ROUND(horas_por_pieza * 60, 1)                                            AS minutos_de_impresora,
    ROUND(ganancia_unitaria / horas_por_pieza, 0)                             AS ganancia_por_hora,
    RANK() OVER (ORDER BY ganancia_unitaria / horas_por_pieza DESC)           AS puesto_por_hora,
    RANK() OVER (ORDER BY ganancia_unitaria DESC)                             AS puesto_por_pieza,
    RANK() OVER (PARTITION BY tecnologia ORDER BY ganancia_unitaria / horas_por_pieza DESC) AS puesto_en_su_impresora
FROM por_pieza
ORDER BY ganancia_por_hora DESC;
