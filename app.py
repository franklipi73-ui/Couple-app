# app.py - versión corregida: safe_rerun() en lugar de st.experimental_rerun()
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
# Helper: recargar de forma segura
# ----------------------------
def safe_rerun():
    """
    Intenta recargar la app. Primero usa st.experimental_rerun().
    Si no existe, intenta forzar un reload cambiando query params.
    Si eso tampoco está disponible, pide al usuario refrescar la página manualmente.
    """
    try:
        # preferido
        st.experimental_rerun()
    except Exception:
        # intentar método alternativo: toggle query param para forzar rerender
        try:
            # obtener params actuales (si la función existe)
            params = {}
            try:
                params = st.experimental_get_query_params()
            except Exception:
                params = {}
            # toggle helper param
            current = int(params.get("_refresh", ["0"])[0]) if params.get("_refresh") else 0
            new = {"_refresh": str(current ^ 1)}
            try:
                st.experimental_set_query_params(**new)
                # detener ejecución para que Streamlit recargue con nuevos params
                st.stop()
            except Exception:
                # si no se puede setear params, pedir refresh manual
                st.warning("Refresca la página manualmente para ver los cambios.")
                return
        except Exception:
            st.warning("Refresca la página manualmente para ver los cambios.")
            return

# ----------------------------
# Función: fallback login (form propio)
# ----------------------------
def fallback_login_form():
    """
    Muestra un formulario simple de login si la librería falla.
    Guarda estado en st.session_state['logged_in'], ['username'], ['name'].
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
            st.session_state["logged_in"] = True
            st.session_state["username"] = u
            st.session_state["name"] = nombres[usuarios.index(u)]
            st.success("Login correcto (fallback).")
            # tratamos de recargar la app; si no se puede, devolvemos True para continuar
            try:
                safe_rerun()
                return True
            except Exception:
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
    # Llamamos login con varias firmas posibles
    try:
        # intentar firma moderna con keywords
        auth_status = authenticator.login(name="Login", location="main")
    except TypeError:
        try:
            auth_status = authenticator.login(location="main")
        except Exception:
            # si falla al renderizar, dejamos auth_status en None para fallback
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
        st.session_stat_
