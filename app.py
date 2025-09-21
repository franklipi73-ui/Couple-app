import streamlit as st
import pandas as pd
from utils import cargar_datos, agregar_movimiento, borrar_movimiento, calcular_saldos

st.set_page_config(page_title="Gestor de gastos en pareja", layout="centered")

st.title("💸 Gestor de gastos en pareja")
st.write("Control de ingresos y gastos compartidos.")

# ----------------------------
# Agregar nuevo movimiento
# ----------------------------
st.subheader("➕ Agregar ingreso o gasto")
with st.form("nuevo_movimiento"):
    persona = st.selectbox("Persona", ["Vos", "Tu novia"])
    tipo = st.radio("Tipo", ["Ingreso", "Gasto"])
    monto = st.number_input("Monto", min_value=0.0, format="%.2f")
    descripcion = st.text_input("Descripción (opcional)")
    submit = st.form_submit_button("Agregar")

if submit and monto > 0:
    agregar_movimiento(persona, tipo, monto, descripcion)
    st.success("✅ Movimiento agregado.")

# ----------------------------
# Mostrar historial con opción de borrar
# ----------------------------
st.subheader("📜 Historial")
df = cargar_datos()

if len(df) > 0:
    for i, row in df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{row['Persona']}** - {row['Tipo']} - ${row['Monto']:.2f} - {row['Descripción']}")
        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                borrar_movimiento(i)
                st.experimental_rerun()
else:
    st.info("Todavía no hay movimientos cargados.")

# ----------------------------
# Mostrar saldos
# ----------------------------
st.subheader("📊 Saldos")
saldos, total = calcular_saldos()
for persona, saldo in saldos.items():
    st.write(f"**{persona}:** {saldo:.2f}")
st.write(f"### 💰 Total conjunto: {total:.2f}")
