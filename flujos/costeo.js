// Costeo de una pieza impresa en 3D: la misma fórmula de scripts/costeo.py.
// Este código va dentro del nodo «Calcular cotización» del flujo de n8n
// (scripts/armar_flujo.py lo copia tal cual) y las pruebas lo comparan con Python y SQL.

function leerCsv(texto) {
  // CSV sencillo con comillas dobles (como los que escribe Python).
  const filas = [];
  let fila = [], campo = '', comillas = false;
  const t = texto.replace(/^﻿/, '');
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (comillas) {
      if (c === '"' && t[i + 1] === '"') { campo += '"'; i++; }
      else if (c === '"') comillas = false;
      else campo += c;
    } else if (c === '"') comillas = true;
    else if (c === ',') { fila.push(campo); campo = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && t[i + 1] === '\n') i++;
      fila.push(campo); campo = '';
      if (fila.length > 1 || fila[0] !== '') filas.push(fila);
      fila = [];
    } else campo += c;
  }
  if (campo !== '' || fila.length) { fila.push(campo); filas.push(fila); }
  const [encabezado, ...resto] = filas;
  return resto.map((f) => Object.fromEntries(encabezado.map((h, i) => [h, f[i]])));
}

function tablaTarifas(filas) {
  const t = {};
  for (const f of filas) t[f.parametro] = Number(f.valor);
  return t;
}

function costoUnitario(pieza, t) {
  const cantidad = Number(pieza.material_cantidad);
  const horas = Number(pieza.horas_placa);
  const ppp = Number(pieza.piezas_por_placa);
  const acabado = Number(pieza.minutos_acabado);
  if (!(ppp > 0) || !(cantidad >= 0) || !(horas >= 0) || !(acabado >= 0)) {
    throw new Error('Datos de la pieza fuera de rango');
  }
  let material, insumosPlaca, potencia, maquinaHora, tasa;
  if (pieza.tecnologia === 'Resina') {
    material = cantidad * (1 + t.resina_soportes_pct) * t.resina_precio_litro / 1000;
    insumosPlaca = t.alcohol_ml_por_placa * t.alcohol_precio_litro / 1000
      + t.guantes_pares_por_placa * t.guantes_precio_par
      + t.papel_por_placa
      + t.fep_precio / t.fep_placas_vida;
    [potencia, maquinaHora, tasa] = [t.resina_potencia_w, t.resina_maquina_hora, t.resina_tasa_fallas];
  } else if (pieza.tecnologia === 'FDM') {
    material = cantidad * (1 + t.fdm_purga_pct) * t.filamento_precio_kg / 1000;
    insumosPlaca = t.fdm_insumos_por_placa;
    [potencia, maquinaHora, tasa] = [t.fdm_potencia_w, t.fdm_maquina_hora, t.fdm_tasa_fallas];
  } else {
    throw new Error('Tecnología desconocida: ' + pieza.tecnologia);
  }
  const insumos = insumosPlaca / ppp;
  const energia = horas * potencia / 1000 * t.energia_precio_kwh / ppp;
  const maquina = horas * maquinaHora / ppp;
  const manoObra = (t.preparacion_min_por_placa / ppp + acabado) / 60 * t.mano_obra_hora;
  const base = material + insumos + energia + maquina + manoObra;
  const fallas = base * tasa;
  return {
    material, insumos, energia, maquina, mano_obra: manoObra, fallas,
    costo_total: material + insumos + energia + maquina + manoObra + fallas,
  };
}

function precioSugerido(costo, t, comision) {
  const divisor = 1 - t.margen_objetivo - (comision || 0);
  if (divisor <= 0) throw new Error('Margen más comisión no pueden sumar 100 % o más');
  const paso = t.redondeo_precio;
  // Se quita el ruido de coma flotante antes del techo (igual efecto que en Python).
  return Math.ceil(Number((costo / divisor / paso).toFixed(9))) * paso;
}

function cotizar(pieza, cantidad, canal, t, canales) {
  if (!Number.isInteger(cantidad) || cantidad < 1) throw new Error('La cantidad debe ser un entero mayor que cero');
  if (!(canal in canales)) throw new Error('Canal desconocido: ' + canal);
  const c = costoUnitario(pieza, t);
  const comision = canales[canal];
  const precioUnitario = precioSugerido(c.costo_total, t, comision);
  const total = precioUnitario * cantidad;
  const costoTotal = c.costo_total * cantidad;
  const comisionValor = total * comision;
  return {
    costo_unitario: c.costo_total,
    precio_unitario: precioUnitario,
    cantidad,
    total,
    comision: comisionValor,
    ganancia: total - costoTotal - comisionValor,
    margen_pct: (total - costoTotal - comisionValor) / total,
  };
}

if (typeof module !== 'undefined') {
  module.exports = { leerCsv, tablaTarifas, costoUnitario, precioSugerido, cotizar };
}
