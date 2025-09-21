import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth
from utils import cargar_datos, agregar_movimiento, borrar_movimiento, calcular_saldos

# ----------------------------
# CONFIGURAR USUARIOS
# ----------------------------
usuarios = ["fran", "novia"]
nombres = ["Francisco", "Novia"]
contrasenas = ["1234", "abcd"]

# Hashear cada contraseña
hashed_pw = [stauth.Hasher().hash(pw) for pw in contrasenas]

# Formato requerido por la librería
credentials = {
    "usernames": {
        usuarios[0]: {"name": nombres[0], "password": hashed_pw[0]},
        usuarios[1]: {"name": nombres[1], "password": hashed_pw[1]}
    }
}

# Crear autenticador
authenticator = stauth.Authenticate(
    credentials,
    "cookie_gastos",  # nombre de cookie
    "clave_firma",    # clave secreta
    cookie_expiry_days=1
)

# ----------------------------
# LOGIN
# ----------------------------
nombre, auth_status, usuario = authenticator.login(location="main")

if auth_status is False:
    st.error("❌ Usuario o contraseña incorrectos")
elif auth_status is None:
    st.warning("⚠️ Ingresá usuario y contraseña")
else:
    # Login correcto
    st.set_page_config(page_title="Gestor de gastos en pareja", layout="centered")
    st.title("💸 Gestor de gastos en pareja")
    st.write(f"Bienvenido/a **{nombre}** 👋")

    authenticator.logout("Cerrar sesión", "sidebar")

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
