import streamlit as st
import streamlit_authenticator as stauth
from utils import cargar_datos, agregar_movimiento, borrar_movimiento, calcular_saldos

# ----------------------------
# Configuración de página (debe ir antes de cualquier llamada a UI)
# ----------------------------
st.set_page_config(page_title="Gestor de gastos en pareja", layout="centered")

# ----------------------------
# CONFIGURAR USUARIOS (cambiá estos valores)
# ----------------------------
usuarios = ["fran", "novia"]
nombres = ["Francisco", "Novia"]
contrasenas = ["1234", "abcd"]  # para test; en producción usá hashes o YAML

# Hashear cada contraseña (streamlit-authenticator requiere hashes)
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
    "cookie_gastos",   # nombre de la cookie
    "clave_firma",     # clave secreta (cambiá por algo fuerte)
    cookie_expiry_days=1
)

# ----------------------------
# LOGIN
# ----------------------------
auth_status = authenticator.login(name="Login", location="main")

if auth_status is False:
    st.error("❌ Usuario o contraseña incorrectos")
elif auth_status is None:
    st.warning("⚠️ Ingresá usuario y contraseña")
else:
    # Login correcto: obtener nombre del usuario logueado
    username = authenticator.username  # ej. "fran"
    nombre = authenticator.credentials["usernames"][username]["name"]

    st.title("💸 Gestor de gastos en pareja")
    st.write(f"Bienvenido/a **{nombre}** 👋")

    # Botón para cerrar sesión en sidebar (usamos keywords para evitar conflictos de firma)
    authenticator.logout(name="Cerrar sesión", location="sidebar")

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

    if submit:
        if monto > 0:
            agregar_movimiento(persona, tipo, monto, descripcion)
            st.success("✅ Movimiento agregado.")
        else:
            st.error("El monto debe ser mayor a 0.")

    # ----------------------------
    # Mostrar historial con opción de borrar
    # ----------------------------
    st.subheader("📜 Historial")
    df = cargar_datos()

    if df.empty:
        st.info("Todavía no hay movimientos cargados.")
    else:
        # Mostrar en forma compacta con botones de borrar
        for idx, row in df.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                desc = f" - {row['Descripción']}" if row.get("Descripción", "") else ""
                st.write(f"**ID {idx}** — {row['Persona']} • {row['Tipo']} • ${float(row['Monto']):.2f}{desc}")
            with col2:
                if st.button("🗑️", key=f"delete_{idx}"):
                    borrar_movimiento(idx)
                    st.experimental_rerun()

    # ----------------------------
    # Mostrar saldos
    # ----------------------------
    st.subheader("📊 Saldos")
    saldos, total = calcular_saldos()
    if saldos:
        for p, s in saldos.items():
            st.write(f"**{p}:** ${s:.2f}")
    else:
        st.write("No hay saldos para mostrar.")
    st.write(f"### 💰 Total conjunto: ${total:.2f}")
