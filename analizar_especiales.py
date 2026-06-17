import pandas as pd

with open('q', 'r') as f:
    lines = f.readlines()

# Saltar header si existe
if lines and 'Orden' in lines[0]:
    lines = lines[1:]

print("Total registros:", len(lines))

# Parsear - columnas: row;Orden;DocDate;ItemCode;Tipo;InQty;OutQty;Neto;TransValue
registros = []
for line in lines:
    parts = [p.strip() for p in line.strip().split(';')]
    if len(parts) >= 9:
        registros.append({
            'orden': parts[1].replace(',',''),
            'docdate': parts[2],
            'item': parts[3],
            'tipo': parts[4].strip(),
            'inqty': float(parts[5].replace(',','')),
            'outqty': float(parts[6].replace(',','')),
            'neto': float(parts[7].replace(',','')),
            'valor': float(parts[8].replace(',',''))
        })

df = pd.DataFrame(registros)

print("\n" + "=" * 70)
print("1. DISTRIBUCIÓN POR TIPO")
print("=" * 70)
for tipo in df['tipo'].unique():
    sub = df[df['tipo'] == tipo]
    print(f"  {tipo}: {len(sub)} registros | In={sub['inqty'].sum():,.0f} | Out={sub['outqty'].sum():,.0f} | Neto={sub['neto'].sum():,.0f}")

print("\n" + "=" * 70)
print("2. NETO POR ORDEN (¿se compensan entradas y salidas?)")
print("=" * 70)

por_orden = df.groupby('orden').agg(
    total_in=('inqty', 'sum'),
    total_out=('outqty', 'sum'),
    neto_total=('neto', 'sum'),
    valor_total=('valor', 'sum'),
    n_entradas=('tipo', lambda x: (x == 'ENTRADA_PROD').sum()),
    n_salidas=('tipo', lambda x: (x == 'SALIDA_CONSUMO').sum())
).reset_index()

neto_cero = por_orden[abs(por_orden['neto_total']) < 0.01]
neto_positivo = por_orden[por_orden['neto_total'] > 0.01]
neto_negativo = por_orden[por_orden['neto_total'] < -0.01]

print(f"  Órdenes con neto ≈ 0 (RECOSTEO - entra/sale igual): {len(neto_cero)}")
print(f"  Órdenes con neto > 0 (genera stock neto):            {len(neto_positivo)}")
print(f"  Órdenes con neto < 0 (consume stock neto):           {len(neto_negativo)}")

if len(neto_cero) > 0:
    print("\n  === ÓRDENES RECOSTEO (neto ≈ 0) ===")
    for _, r in neto_cero.head(20).iterrows():
        print(f"    Orden {r['orden']}: In={r['total_in']:,.0f} Out={r['total_out']:,.0f} Neto={r['neto_total']:,.1f} Valor={r['valor_total']:,.2f} ({r['n_entradas']}E/{r['n_salidas']}S)")

if len(neto_positivo) > 0:
    print(f"\n  === ÓRDENES QUE GENERAN STOCK (neto > 0) - primeras 20 ===")
    for _, r in neto_positivo.head(20).iterrows():
        print(f"    Orden {r['orden']}: In={r['total_in']:,.0f} Out={r['total_out']:,.0f} Neto={r['neto_total']:,.0f} ({r['n_entradas']}E/{r['n_salidas']}S)")

if len(neto_negativo) > 0:
    print(f"\n  === ÓRDENES QUE CONSUMEN STOCK (neto < 0) - primeras 20 ===")
    for _, r in neto_negativo.head(20).iterrows():
        print(f"    Orden {r['orden']}: In={r['total_in']:,.0f} Out={r['total_out']:,.0f} Neto={r['neto_total']:,.0f} ({r['n_entradas']}E/{r['n_salidas']}S)")

print("\n" + "=" * 70)
print("3. DETALLE POR ORDEN - EJEMPLO DE CADA TIPO")
print("=" * 70)

# Mostrar 3 ejemplos de cada categoría
for label, subset in [("RECOSTEO (neto=0)", neto_cero), ("GENERA STOCK", neto_positivo), ("CONSUME STOCK", neto_negativo)]:
    if len(subset) > 0:
        print(f"\n  >>> {label}:")
        for orden in subset.head(3)['orden']:
            print(f"\n    Orden {orden}:")
            det = df[df['orden'] == orden].sort_values('tipo', ascending=False)
            for _, r in det.iterrows():
                print(f"      {r['tipo']:16s} Item={r['item']} In={r['inqty']:>10,.0f} Out={r['outqty']:>10,.0f} Neto={r['neto']:>10,.0f} Valor={r['valor']:>12,.2f}")

print("\n" + "=" * 70)
print("4. PRODUCTO 010000001 EN ÓRDENES ESPECIAL")
print("=" * 70)
prod001 = df[df['item'] == '010000001']
if len(prod001) > 0:
    for _, r in prod001.iterrows():
        print(f"  Orden {r['orden']}: {r['tipo']:16s} In={r['inqty']:,.0f} Out={r['outqty']:,.0f} Neto={r['neto']:,.0f} Valor={r['valor']:,.2f}")
else:
    print("  (no aparece en datos exportados)")

print("\n" + "=" * 70)
print("5. RESUMEN FINAL")
print("=" * 70)
total_ordenes = por_orden['orden'].nunique()
print(f"  Total órdenes analizadas:    {total_ordenes}")
print(f"  Total IN (entradas):         {df['inqty'].sum():>15,.2f}")
print(f"  Total OUT (salidas):         {df['outqty'].sum():>15,.2f}")
print(f"  NETO GLOBAL:                 {df['neto'].sum():>15,.2f}")
print(f"  NETO VALOR:                  {df['valor'].sum():>15,.2f}")
