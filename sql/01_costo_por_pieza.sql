-- 01 · ¿Cuánto cuesta de verdad cada pieza?
-- La misma fórmula de scripts/costeo.py, en SQL.
-- Lo que cuesta por placa (lavado, luz, máquina, preparar) se divide por las
-- piezas que caben en la placa. Al final se reparte lo que se pierde en placas que salen mal.

DROP VIEW IF EXISTS v_costo_pieza;
CREATE VIEW v_costo_pieza AS
WITH t AS (                       -- tarifas en una sola fila (de largo a ancho)
    SELECT
        MAX(CASE WHEN parametro = 'resina_precio_litro'       THEN valor END) AS resina_precio_litro,
        MAX(CASE WHEN parametro = 'resina_soportes_pct'       THEN valor END) AS resina_soportes_pct,
        MAX(CASE WHEN parametro = 'alcohol_ml_por_placa'      THEN valor END) AS alcohol_ml_por_placa,
        MAX(CASE WHEN parametro = 'alcohol_precio_litro'      THEN valor END) AS alcohol_precio_litro,
        MAX(CASE WHEN parametro = 'guantes_pares_por_placa'   THEN valor END) AS guantes_pares_por_placa,
        MAX(CASE WHEN parametro = 'guantes_precio_par'        THEN valor END) AS guantes_precio_par,
        MAX(CASE WHEN parametro = 'papel_por_placa'           THEN valor END) AS papel_por_placa,
        MAX(CASE WHEN parametro = 'fep_precio'                THEN valor END) AS fep_precio,
        MAX(CASE WHEN parametro = 'fep_placas_vida'           THEN valor END) AS fep_placas_vida,
        MAX(CASE WHEN parametro = 'resina_potencia_w'         THEN valor END) AS resina_potencia_w,
        MAX(CASE WHEN parametro = 'resina_maquina_hora'       THEN valor END) AS resina_maquina_hora,
        MAX(CASE WHEN parametro = 'resina_tasa_fallas'        THEN valor END) AS resina_tasa_fallas,
        MAX(CASE WHEN parametro = 'filamento_precio_kg'       THEN valor END) AS filamento_precio_kg,
        MAX(CASE WHEN parametro = 'fdm_purga_pct'             THEN valor END) AS fdm_purga_pct,
        MAX(CASE WHEN parametro = 'fdm_insumos_por_placa'     THEN valor END) AS fdm_insumos_por_placa,
        MAX(CASE WHEN parametro = 'fdm_potencia_w'            THEN valor END) AS fdm_potencia_w,
        MAX(CASE WHEN parametro = 'fdm_maquina_hora'          THEN valor END) AS fdm_maquina_hora,
        MAX(CASE WHEN parametro = 'fdm_tasa_fallas'           THEN valor END) AS fdm_tasa_fallas,
        MAX(CASE WHEN parametro = 'energia_precio_kwh'        THEN valor END) AS energia_precio_kwh,
        MAX(CASE WHEN parametro = 'mano_obra_hora'            THEN valor END) AS mano_obra_hora,
        MAX(CASE WHEN parametro = 'preparacion_min_por_placa' THEN valor END) AS preparacion_min_por_placa
    FROM tarifas
),
partes AS (
    SELECT
        p.id_pieza, p.nombre, p.categoria, p.tecnologia, p.precio_lista,
        CASE p.tecnologia
            WHEN 'Resina' THEN p.material_cantidad * (1 + t.resina_soportes_pct) * t.resina_precio_litro / 1000.0
            WHEN 'FDM'    THEN p.material_cantidad * (1 + t.fdm_purga_pct) * t.filamento_precio_kg / 1000.0
        END AS material,          -- otra tecnología queda vacía (NULL), no se cobra como FDM.
                                  -- además el esquema (00) no deja cargarla, igual que Python y JS dan error
        CASE p.tecnologia
            WHEN 'Resina' THEN (t.alcohol_ml_por_placa * t.alcohol_precio_litro / 1000.0
                                + t.guantes_pares_por_placa * t.guantes_precio_par
                                + t.papel_por_placa
                                + t.fep_precio / t.fep_placas_vida) / p.piezas_por_placa
            WHEN 'FDM'    THEN t.fdm_insumos_por_placa * 1.0 / p.piezas_por_placa
        END AS insumos,
        p.horas_placa * (CASE p.tecnologia WHEN 'Resina' THEN t.resina_potencia_w WHEN 'FDM' THEN t.fdm_potencia_w END)
            / 1000.0 * t.energia_precio_kwh / p.piezas_por_placa AS energia,
        p.horas_placa * (CASE p.tecnologia WHEN 'Resina' THEN t.resina_maquina_hora WHEN 'FDM' THEN t.fdm_maquina_hora END)
            / p.piezas_por_placa AS maquina,
        (t.preparacion_min_por_placa * 1.0 / p.piezas_por_placa + p.minutos_acabado) / 60.0 * t.mano_obra_hora
            AS mano_obra,
        CASE p.tecnologia WHEN 'Resina' THEN t.resina_tasa_fallas WHEN 'FDM' THEN t.fdm_tasa_fallas END AS tasa_fallas
    FROM piezas AS p
    CROSS JOIN t
)
SELECT
    id_pieza, nombre, categoria, tecnologia, precio_lista,
    material, insumos, energia, maquina, mano_obra,
    -- si 1 de cada 10 placas sale mal, para tener 9 buenas se pagan 10: costo base / (1 - tasa)
    (material + insumos + energia + maquina + mano_obra) * tasa_fallas / (1 - tasa_fallas) AS fallas,
    (material + insumos + energia + maquina + mano_obra) / (1 - tasa_fallas)               AS costo_total
FROM partes;

-- Resultado: una fila por pieza, del costo más alto al más bajo.
SELECT
    id_pieza,
    nombre,
    tecnologia,
    ROUND(costo_total, 0)                    AS costo_unitario,
    ROUND(material / costo_total * 100, 1)   AS pct_material,
    ROUND(mano_obra / costo_total * 100, 1)  AS pct_mano_obra,
    precio_lista
FROM v_costo_pieza
ORDER BY costo_total DESC;
