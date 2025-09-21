# app.py - fallback login sin forzar recarga (versión corregida)
import streamlit as st
import streamlit_authenticator as stauth
from utils import cargar_datos, agregar_movimiento, borrar_movimiento, calcular_saldos

# ----------------------------
# Configuración de página
# ----------------------------
st.set_page_config(page_title="Gestor de gastos en pareja", layout="centered")

# ----------------------------
# Credenciales (cambiá en producción)
# ----------------------------
usuarios = ["fran", "novia"]
nombres = ["Francisco", "Novia"]
contrasenas = ["1234", "abcd"]  # SOLO para pruebas / fallback

# Intentamos crear hashes (si stauth está disponible y funciona)
try:
    hashed_pw = [stauth.Hasher().hash(pw) for pw in contrasenas]
    credentials = {
        "usernames": {
            usuarios[0]: {"name": nombres[0], "password": hashed_pw[0]},
            usuarios[1]: {"name": nombres[1], "password": hashed_pw[1]},
        }
    }
    use_stauth = True
except Exception:
    credentials = {}
    use_stauth = False

# ----------------------------
# Creamos el autenticador si es posible
# ----------------------------
authenticator = None
if use_stauth:
    try:
        authenticator = stauth.Authenticate(
            credentials,
            "cookie_gastos",
            "clave_firma",
            cookie_expiry_days=1
        )
    except Exception:
        authenticator = None
        use_stauth = False

# ----------------------------
# Helper: recargar de forma segura (usa st.query_params cuando esté disponible)
# ----------------------------
def safe_rerun():
    """
    Intenta recargar la app. Usa st.experimental_rerun si existe,
    si no usa st.query_params o las funciones experimentales antiguas.
    Si todo falla, pide refrescar manualmente.
    """
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        pass

    try:
        if hasattr(st, "query_params"):
            params = st.query_params or {}
            current = 0
            if params.get("_refresh"):
                try:
                    current = int(params.get("_refresh")[0])
                except Exception:
                    current = 0
            new = dict(params)
            new["_refresh"] = [str(current ^ 1)]
            try:
                st.query_params = new
                st.stop()
                return
            except Exception:
                pass
    except Exception:
        pass

    try:
        if hasattr(st, "experimental_get_query_params") and hasattr(st, "experimental_set_query_params"):
            params = st.experimental_get_query_params() or {}
            current = 0
            if params.get("_refresh"):
                try:
                    current = int(params.get("_refresh")[0])
                except Exception:
                    current = 0
            try:
                st.experimental_set_query_params(_refresh=str(current ^ 1))
                st.stop()
                return
            except Exception:
                pass
    except Exception:
        pass

    st.warning("No se pudo recargar automáticamente — por favor refrescá la página manualmente para ver los cambios.")

# ----------------------------
# Función: fallback login (form propio) - **no fuerza recarga**
# ----------------------------
def fallback_login_form():
    """
    Muestra un formulario simple de login si la librería falla.
    Guarda estado en st.session_state['logged_in'], ['username'], ['name'].
    No fuerza rerun; permite que el mismo flujo continúe y muestre la app.
    """
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if st.session_state.get("logged_in"):
        return True

    st.info("Usando login alternativo (fallback). Ingresá usuario y contraseña de prueba.")
    with st.form("fallback_login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar")
    if submit:
        if u in usuarios and p == contrasenas[usuarios.index(u)]:
            # Seteamos sesión y devolvemos True (no forzamos recarga)
            st.session_state["logged_in"] = True
            st.session_state["username"] = u
            st.session_state["name"] = nombres[usuarios.index(u)]
            st.success("Login correcto (fallback).")
            return True
        else:
            st.error("Usuario o contraseña incorrectos (fallback).")
    return st.session_state.get("logged_in", False)

# ----------------------------
# Intento principal de login usando streamlit-authenticator (si disponible)
# ----------------------------
auth_status = None
logged_in = False
username = None
nombre = None

if authenticator is not None:
    # Llamamos login con varias firmas posibles (manejo robusto)
    try:
        auth_status = authenticator.login(name="Login", location="main")
    except TypeError:
        try:
            auth_status = authenticator.login(location="main")
        except Exception:
            auth_status = None
    except Exception:
        auth_status = None

    # Normalizar respuesta
    if isinstance(auth_status, (bool, type(None))):
        if auth_status is True:
            username = getattr(authenticator, "username", None)
            try:
                nombre = authenticator.credentials["usernames"][username]["name"]
            except Exception:
                nombre = None
            logged_in = True
        elif auth_status is False:
            logged_in = False
        else:
            logged_in = False
    else:
        if isinstance(auth_status, tuple):
            if len(auth_status) == 3:
                nombre, status, username = auth_status
                auth_status = status
                logged_in = bool(status)
            else:
                logged_in = False
        elif isinstance(auth_status, dict):
            status = auth_status.get("authenticated") or auth_status.get("authentication_status") or None
            auth_status = status
            logged_in = bool(status)
        else:
            logged_in = False

# Si authenticator no existe o no permitió logueo, usamos fallback
if not logged_in:
    if st.session_state.get("logged_in", False):
        logged_in = True
        username = st.session_state.get("username")
        nombre = st.session_state.get("name")
    else:
        if authenticator is None or auth_status is None:
            # aquí usamos el fallback que NO fuerza recarga
            logged_in = fallback_login_form()
            if logged_in:
                username = st.session_state.get("username")
                nombre = st.session_state.get("name")

# ----------------------------
# Si no está logueado: mostrar mensaje y detener ejecución (ya mostramos UI de login)
# ----------------------------
if not logged_in:
    if auth_status is False:
        st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# ----------------------------
# Usuario logueado: interfaz principal
# ----------------------------
if not nombre and username:
    try:
        nombre = authenticator.credentials["usernames"][username]["name"]
    except Exception:
        nombre = username

st.title("💸 Gestor de gastos en pareja")
st.write(f"Bienvenido/a **{nombre}** 👋")

# Logout: intentamos usar la función del authenticator, si no existe, limpiamos session_state
logout_done = False
if authenticator is not None:
    try:
        authenticator.logout(name="Cerrar sesión", location="sidebar")
        logout_done = True
    except TypeError:
        try:
            authenticator.logout("Cerrar sesión")
            logout_done = True
        except Exception:
            logout_done = False

if not logout_done:
    if st.sidebar.button("Cerrar sesión (fallback)"):
        st.session_state["logged_in"] = False
        st.session_state.pop("username", None)
        st.session_state.pop("name", None)
        safe_rerun()
        st.info("Sesión cerrada. Refresca la página si sigue apareciendo logueado.")
        st.stop()

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
        safe_rerun()
    else:
        st.error("El monto debe ser mayor a 0.")

# ----------------------------
# Historial con borrar
# ----------------------------
st.subheader("📜 Historial")
df = cargar_datos()
if df.empty:
    st.info("Todavía no hay movimientos cargados.")
else:
    for idx, row in df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            desc = f" - {row.get('Descripción', '')}" if row.get("Descripción", "") else ""
            st.write(f"**ID {idx}** — {row.get('Persona', '')} • {row.get('Tipo', '')} • ${float(row.get('Monto', 0.0)):.2f}{desc}")
        with col2:
            if st.button("🗑️", key=f"delete_{idx}"):
                borrar_movimiento(idx)
                safe_rerun()
                st.info("Movimiento borrado. Refresca la página si el historial no se actualiza.")
                st.stop()

# ----------------------------
# Saldos
# ----------------------------
st.subheader("📊 Saldos")
saldos, total = calcular_saldos()
if saldos:
    for p, s in saldos.items():
        st.write(f"**{p}:** ${s:.2f}")
else:
    st.write("No hay saldos para mostrar.")
st.write(f"### 💰 Total conjunto: ${total:.2f}")
