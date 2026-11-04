-- 02 · Resina frente a FDM: ¿en qué se va la plata en cada tecnología?
-- Usa la vista v_costo_pieza (01). Suma las piezas del catálogo de cada tecnología.

SELECT
    tecnologia,
    COUNT(*)                                                     AS piezas_en_catalogo,
    ROUND(AVG(costo_total), 0)                                   AS costo_promedio,
    ROUND(SUM(material)  / SUM(costo_total) * 100, 1)            AS pct_material,
    ROUND(SUM(insumos)   / SUM(costo_total) * 100, 1)            AS pct_insumos,
    ROUND(SUM(energia + maquina) / SUM(costo_total) * 100, 1)    AS pct_luz_y_maquina,
    ROUND(SUM(mano_obra) / SUM(costo_total) * 100, 1)            AS pct_mano_obra,
    ROUND(SUM(fallas)    / SUM(costo_total) * 100, 1)            AS pct_fallas,
    ROUND(AVG(1 - costo_total / precio_lista) * 100, 1)          AS margen_bruto_promedio_pct
FROM v_costo_pieza
GROUP BY tecnologia
ORDER BY tecnologia DESC;
