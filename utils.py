import pandas as pd
import os

DATA_FILE = "gastos.csv"

def cargar_datos():
    """Carga el archivo CSV, o lo crea si no existe."""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Persona", "Tipo", "Monto", "Descripción"])
        df.to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE)

def guardar_datos(df):
    """Guarda el DataFrame en el archivo CSV."""
    df.to_csv(DATA_FILE, index=False)

def agregar_movimiento(persona, tipo, monto, descripcion=""):
    """Agrega un ingreso o gasto."""
    df = cargar_datos()
    nuevo = pd.DataFrame([[persona, tipo, monto, descripcion]],
                         columns=["Persona", "Tipo", "Monto", "Descripción"])
    df = pd.concat([df, nuevo], ignore_index=True)
    guardar_datos(df)
    return df

def borrar_movimiento(indice):
    """Elimina un movimiento según índice."""
    df = cargar_datos()
    if indice in df.index:
        df = df.drop(index=indice)
        guardar_datos(df)
    return df

def calcular_saldos():
    """Devuelve un dict con saldo por persona y total."""
    df = cargar_datos()
    ingresos = df[df["Tipo"] == "Ingreso"].groupby("Persona")["Monto"].sum()
    gastos = df[df["Tipo"] == "Gasto"].groupby("Persona")["Monto"].sum()
    saldo_persona = ingresos.subtract(gastos, fill_value=0)
    saldo_total = saldo_persona.sum()
    return saldo_persona.to_dict(), saldo_total
