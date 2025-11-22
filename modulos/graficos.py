import plotly.express as px
import pydeck as pdk

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

#Mapa interactivo 3D con Pydeck
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
    
    # Configuración de la vista inicial (centrada en los datos)
    lat_center = df_vehiculo["latitud"].mean()
    lon_center = df_vehiculo["longitud"].mean()

    view_state = pdk.ViewState(
        latitude=lat_center,
        longitude=lon_center,
        zoom=15,  # Mayor zoom para ver más detalle
        pitch=60, # Inclinación más pronunciada para efecto 3D
        bearing=0
    )

    # Capa de puntos de repostaje con bordes para mejor visibilidad
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_vehiculo,
        get_position='[longitud, latitud]',
        get_color='[255, 50, 50, 220]', # Rojo intenso
        get_radius=60, # Radio en metros
        get_line_color=[255, 255, 255], # Borde blanco
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True
    )

    # Tooltip personalizado
    tooltip = {
        "html": "<b>Dirección:</b> {direccion}<br/><b>Repostado:</b> {repostado} L",
        "style": {"backgroundColor": "rgba(255,255,255,0.9)", "color": "#333", "border": "2px solid #ff3232"}
    }

    # Mapa claro y legible (Carto Positron)
    r = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    )

    return r

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