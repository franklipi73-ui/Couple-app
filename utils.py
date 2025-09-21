import pandas as pd
import os

DATA_FILE = "gastos.csv"

def cargar_datos():
    """Carga el CSV (lo crea si no existe) y devuelve un DataFrame."""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Persona", "Tipo", "Monto", "Descripción"])
        df.to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE)

def guardar_datos(df):
    """Guarda el DataFrame en el CSV."""
    df.to_csv(DATA_FILE, index=False)

def agregar_movimiento(persona, tipo, monto, descripcion=""):
    """Agrega un movimiento y devuelve el DataFrame actualizado."""
    df = cargar_datos()
    nuevo = pd.DataFrame([[persona, tipo, float(monto), descripcion]],
                         columns=["Persona", "Tipo", "Monto", "Descripción"])
    df = pd.concat([df, nuevo], ignore_index=True)
    guardar_datos(df)
    return df

def borrar_movimiento(indice):
    """Borra el movimiento por índice (si existe) y devuelve el DataFrame actualizado."""
    df = cargar_datos()
    if indice in df.index:
        df = df.drop(index=indice)
        # opcional: reasignar índices (para mantener índices 0..n-1)
        df = df.reset_index(drop=True)
        guardar_datos(df)
    return df

def calcular_saldos():
    """Calcula saldo por persona y total. Devuelve (dict_saldos, total)."""
    df = cargar_datos()
    if df.empty:
        return {}, 0.0
    # Asegurar tipo numérico
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0)
    ingresos = df[df["Tipo"] == "Ingreso"].groupby("Persona")["Monto"].sum()
    gastos = df[df["Tipo"] == "Gasto"].groupby("Persona")["Monto"].sum()
    saldo_persona = ingresos.subtract(gastos, fill_value=0)
    saldo_total = float(saldo_persona.sum())
    # convertir a float simples
    saldos_dict = {k: float(v) for k, v in saldo_persona.to_dict().items()}
    return saldos_dict, saldo_total
