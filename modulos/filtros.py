import pandas as pd

# Filtra el dataframe por un rango de valores numéricos
def filtro_rango(df, columna, rango):
    if df is None or not columna or columna not in df.columns:
        return df if df is not None else None
    
    min_valor, max_valor = rango
    
    # Convierte el valor a numérico sin modificar el dataframe original
    serie_numerica = pd.to_numeric(df[columna], errors="coerce")
    
    return df[(serie_numerica >= min_valor) & (serie_numerica <= max_valor)]


# Filtra el dataframe según el tipo de vehículo
def filtro_tipo_vehiculo(df, tipos_vehiculo):
    if df is None or not tipos_vehiculo:
        return df
    
    return df[df["tipo_vehiculo"].isin(tipos_vehiculo)]


# Filtra el dataframe según el tipo de combustible
def filtro_tipo_combustible(df, tipos_combustible):
    if df is None or not tipos_combustible:
        return df
    
    return df[df["tipo_combustible"].isin(tipos_combustible)]


# Filtra el dataframe según la provincia
def filtro_provincia(df, provincia):
    if df is None or not provincia:
        return df
    
    if "provincia" not in df.columns:
        return df
    
    return df[df["provincia"].isin(provincia)]


# Filtra el dataframe según el rango de fechas
def filtro_fechas(df, fechas):
    if df is None or not fechas or "fecha" not in df.columns:
        return df
    
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    
    if len(fechas) == 2:
        fecha_inicio, fecha_fin = fechas
        return df[(df["fecha"].dt.date >= fecha_inicio) & (df["fecha"].dt.date <= fecha_fin)]
    elif len(fechas) == 1:
        fecha_unica = fechas[0]
        return df[df["fecha"].dt.date == fecha_unica]
    
    return df


# Aplica todos los filtros al dataframe
def aplicar_filtros(df, tipos_vehiculo=None, tipos_combustible=None, provincia=None, rangos=None, fechas=None):
    if df is None:
        return None
    
    datos_filtrados = df.copy()
    
    # Aplica los filtros individuales
    datos_filtrados = filtro_tipo_vehiculo(datos_filtrados, tipos_vehiculo)
    datos_filtrados = filtro_tipo_combustible(datos_filtrados, tipos_combustible)
    datos_filtrados = filtro_provincia(datos_filtrados, provincia)
    
    # Aplica los filtros dinámicos
    if rangos:
        for columna, (min_valor, max_valor) in rangos.items():
            if columna.lower() in datos_filtrados.columns:
                datos_filtrados = filtro_rango(datos_filtrados, columna.lower(), (min_valor, max_valor))
    
    # Aplica el filtro por fechas
    datos_filtrados = filtro_fechas(datos_filtrados, fechas)
    
    return datos_filtrados