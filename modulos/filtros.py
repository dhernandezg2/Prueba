import pandas as pd

#funcion que filtra la barra de rango dinamicamente.
def filtro_rango(df,columna,rango):

    if df is None:
        return None
    
    #Si la no hay columna o esta no coincide con la del datashet
    if not columna or columna not in df.columns:
        return df

    #valores del rango
    valor_min, valor_max = rango

    #Aseguramos que sea de tipo numerico
    df[columna] = pd.to_numeric(df[columna], errors= "coerce")

    #Apñicamos el filtro.
    return df[(df[columna] >= valor_min) & (df[columna] <= valor_max)]


#Filtra el dataframe segun el tipo de vehiculo
def filtro_tipo_vehiculo(df, tipos_vehiculo):

    if df is None:
        return None
    
    #Si no se selecciona ningun vehículo
    if not tipos_vehiculo:
        return df
    
    return df[df["tipo_vehiculo"].isin(tipos_vehiculo)]


#Filtra el dataframe segun el tipo de combustible
def filtro_tipo_combustible(df,tipos_combustible):

    if df is None:
        return None
    
    #Si no se selecciona ningun combustible
    if not tipos_combustible:
        return df
    
    return df[df["tipo_combustible"].isin(tipos_combustible)]


#Filtra el dataframe segun la direccion
def filtro_direccion(df, lugar):

    if df is None:
        return None
    
    #Si no se selecciona ninguna direccion
    if not lugar:
        return df
    
    return df[df["direccion"].isin(lugar)]


#Filtra el dataframe segun el rango de fechas
def filtro_fechas(df, fechas):
    if df is None or not fechas:
        return df
    
    # Aseguramos que la columna fecha sea datetime
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        
        # Si fechas es una tupla/lista con inicio y fin
        if len(fechas) == 2:
            inicio, fin = fechas
            return df[(df["fecha"].dt.date >= inicio) & (df["fecha"].dt.date <= fin)]
        # Si solo se selecciona un día (a veces pasa en streamlit si no seleccionas rango completo)
        elif len(fechas) == 1:
            dia = fechas[0]
            return df[df["fecha"].dt.date == dia]
            
    return df


#Filtros juntos
def aplicar_filtros(df,tipos_vehiculo = None,tipos_combustible = None,lugar = None, parametro = None, rango = None, fechas = None):
    
    if df is None:
        return None
     
    df_filtrado = df.copy()

    #Filtramos por vehiculo
    if tipos_vehiculo:
         df_filtrado = filtro_tipo_vehiculo(df_filtrado, tipos_vehiculo)

    #Filtramos por combustible
    if tipos_combustible:
         df_filtrado = filtro_tipo_combustible(df_filtrado, tipos_combustible)

    #Filtramos por direccion
    if lugar:
         df_filtrado = filtro_direccion(df_filtrado, lugar)

    #Aplicamos la funcion de rangos dinamicos
    if parametro and rango:
        columna = parametro.lower()
        df_filtrado = filtro_rango(df_filtrado, columna, rango)
        
    #Filtramos por fechas
    if fechas:
        df_filtrado = filtro_fechas(df_filtrado, fechas)

    return df_filtrado