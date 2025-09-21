import streamlit as st
import pandas as pd
import os

# Archivo donde se guardan los datos
DATA_FILE = "gastos.csv"

# Si no existe el archivo, lo creamos vacío
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Persona", "Tipo", "Monto", "Descripción"])
    df.to_csv(DATA_FILE, index=False)

# Cargar datos existentes
df = pd.read_csv(DATA_FILE)

st.set_page_config(page_title="Gestor de gastos en pareja", layout="centered")

st.title("💸 Gestor de gastos en pareja")
st.write("Carguen ingresos y gastos para llevar el control entre los dos.")

# ----------------------------
# Formulario para nuevo movimiento
# ----------------------------
st.subheader("➕ Agregar ingreso o gasto")
with st.form("nuevo_movimiento"):
    persona = st.selectbox("Persona", ["Vos", "Tu novia"])
    tipo = st.radio("Tipo", ["Ingreso", "Gasto"])
    monto = st.number_input("Monto", min_value=0.0, format="%.2f")
    descripcion = st.text_input("Descripción (opcional)")
    submit = st.form_submit_button("Agregar")

if submit and monto > 0:
    nuevo = pd.DataFrame(
        [[persona, tipo, monto, descripcion]],
        columns=["Persona", "Tipo", "Monto", "Descripción"]
    )
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("✅ Movimiento agregado.")

# ----------------------------
# Mostrar historial y opción de borrar
# ----------------------------
st.subheader("📜 Historial")

if len(df) > 0:
    # Agregamos un índice para identificar cada fila
    df_reset = df.reset_index()
    df_reset["ID"] = df_reset["index"]
    st.dataframe(df_reset.drop(columns="index"))

    # Selección de fila a borrar
    borrar_id = st.selectbox("Seleccioná el ID a borrar", df_reset["ID"])
    if st.button("🗑️ Borrar movimiento"):
        df = df.drop(index=borrar_id)
        df.to_csv(DATA_FILE, index=False)
        st.success(f"✅ Movimiento con ID {borrar_id} borrado.")
        st.experimental_rerun()
else:
    st.info("Todavía no hay movimientos cargados.")

# ----------------------------
# Calcular saldos
# ----------------------------
ingresos = df[df["Tipo"] == "Ingreso"].groupby("Persona")["Monto"].sum()
gastos = df[df["Tipo"] == "Gasto"].groupby("Persona")["Monto"].sum()

saldo_persona = ingresos.subtract(gastos, fill_value=0)
saldo_total = saldo_persona.sum()

st.subheader("📊 Saldos")
for persona, saldo in saldo_persona.items():
    st.write(f"**{persona}:** {saldo:.2f}")

st.write(f"### 💰 Total conjunto: {saldo_total:.2f}")
