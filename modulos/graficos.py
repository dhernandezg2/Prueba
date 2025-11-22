import plotly.express as px

#Histogramas para los diferentes parametros
def Grafico_lineal_parametros(df, parametro):

    if df is None or df.empty:
        return None
    
    columna = parametro.lower()

    if columna not in df.columns:
        return None
    
    #Filtramos por fecha para ordenarlas
    if "fecha" in df.columns:
        df = df.sort_values("fecha")
        eje_x = "fecha"
    else:
        eje_x = df.index.name if df.index.name else "index"
    
    #Creamos el grafico de area suavizado (más estético)
    fig = px.area(
        df,
        x = eje_x,
        y = columna,
        markers= True,
        title = f"Evolución de {columna}",
        color_discrete_sequence = ["#00CC96"] # Un color verde/turquesa brillante que resalta sobre oscuro
    )

    fig.update_traces(
        line=dict(width=3, shape='spline'), # Línea curva suave
        marker=dict(size=8, symbol='circle', line=dict(width=2, color='white')), # Marcadores más bonitos
        fill='tozeroy' # Relleno hasta el eje Y
    )
    
    fig.update_layout(
        xaxis_title = "Fecha" if eje_x == "fecha" else "",
        yaxis_title = columna.capitalize(),
        template = "plotly_dark", # Tema oscuro para coincidir con el fondo
        paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente
        plot_bgcolor='rgba(0,0,0,0)', # Fondo del gráfico transparente
        hovermode="x unified", # Hover unificado para ver datos fácilmente
        font=dict(family="Inter, sans-serif", size=14)
    )

    return fig

#Mapa interactivo
def mapa_repostajes(df, vehiculo):

    if df is None or df.empty:
        return None
    
    #Validamos las columnas necesarias
    columnas_nec = {"vehiculo", "latitud", "longitud"}

    if not columnas_nec.issubset(set(df.columns)):
        return None
    
    df_vehiculo = df[df["vehiculo"].astype(str) == str(vehiculo)].copy()
    if df_vehiculo.empty:
        return None
    
    df_vehiculo = df_vehiculo.dropna(subset = ["latitud", "longitud"])
    if df_vehiculo.empty:
        return None
    
    if "fecha" in df_vehiculo.columns:
        df_vehiculo = df_vehiculo.sort_values("fecha")

    data = {}
    for campo in ["fecha", "direccion", "repostado", "consumo", "tipo_combustible", "tipo_vehiculo"]:

        if campo in df_vehiculo.columns:
            data[campo] = True

    #Inicializamos la visualizacion del mapa
    fig = px.scatter_mapbox(
        df_vehiculo,
        lat= "latitud",
        lon= "longitud",
        color= "repostado" if "repostado" in df_vehiculo.columns else None,
        size="repostado" if "repostado" in df_vehiculo.columns else None,
        hover_name= "direccion" if "direccion" in df_vehiculo.columns else None,
        hover_data= data if data else None,
        size_max=16,
        zoom=10,
        height=520,
        title = f"puntos de repostaje del vehiculo {vehiculo}"
    )

    fig.update_layout(
        mapbox_style = "open-street-map",
        margin = dict(r=0, t=50, l=0, b=0),
        coloraxis_colorbar=dict(title="Repostado" if "repostado" in df_vehiculo.columns else "")
    )

    return fig

def grafico_general_repostajes(df):
    """
    Genera un gráfico de barras mostrando el total repostado por tipo de vehículo.
    """
    if df is None or df.empty:
        return None
    
    # Verificar columnas necesarias
    if "repostado" not in df.columns:
        return None
        
    # Determinar columna de agrupación (tipo_vehiculo o vehiculo)
    if "tipo_vehiculo" in df.columns:
        col_grupo = "tipo_vehiculo"
        titulo = "Total Repostado por Tipo de Vehículo"
    elif "vehiculo" in df.columns:
        col_grupo = "vehiculo"
        titulo = "Total Repostado por Vehículo"
    else:
        return None

    # Agrupar y sumar
    df_agrupado = df.groupby(col_grupo)["repostado"].sum().reset_index()
    
    if df_agrupado.empty:
        return None

    # Crear gráfico de barras
    fig = px.bar(
        df_agrupado,
        x=col_grupo,
        y="repostado",
        title=titulo,
        color=col_grupo,
        text_auto='.2s',
        template="plotly_white"
    )
    
    fig.update_layout(
        xaxis_title=col_grupo.replace("_", " ").title(),
        yaxis_title="Total Repostado (Litros)",
        showlegend=False
    )
    
    return fig