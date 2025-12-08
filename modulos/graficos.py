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
def mapa_repostajes(df, vehiculo, estilo="Claro"):

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

    # Capas del mapa
    layers = []

    # Si es satélite (ahora llamado "Oscuro" por el usuario), añadimos la capa de imágenes satelitales como base
    if estilo == "Oscuro":
        satellite_layer = pdk.Layer(
            "TileLayer",
            data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            min_zoom=0,
            max_zoom=19,
            tileSize=256,
            render_sub_layers=True,
            refinement_strategy="no-overlap" # Estrategia para evitar errores de renderizado
        )
        layers.append(satellite_layer)
        map_style = None # No usamos estilo base de mapbox/carto
    else:
        # Por defecto Claro (Carto Positron)
        map_style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

    # Capa de puntos de repostaje (siempre encima)
    points_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_vehiculo,
        get_position='[longitud, latitud]',
        get_color='[255, 50, 50, 220]', # Rojo intenso
        get_radius=20, # Radio en metros (más pequeño)
        get_line_color=[255, 255, 255], # Borde blanco
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True
    )
    layers.append(points_layer)

    # Tooltip personalizado
    tooltip = {
        "html": "<b>Dirección:</b> {direccion}<br/><b>Repostado:</b> {repostado} L",
        "style": {"backgroundColor": "rgba(255,255,255,0.9)", "color": "#333", "border": "2px solid #ff3232"}
    }

    # Creamos el objeto Deck
    r = pdk.Deck(
        map_style=map_style,
        initial_view_state=view_state,
        layers=layers,
        tooltip=tooltip
    )

    return r

def grafico_general_repostajes(df, indices_adestacar=None):
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
    
    # Ordenar por valor descendente para consistencia visual y de índices
    df_agrupado = df_agrupado.sort_values(by="repostado", ascending=False)

    # Crear gráfico de tarta (pie chart)
    fig = px.pie(
        df_agrupado,
        values="repostado",
        names=col_grupo,
        title=titulo,
        hole=0.4, # Donut chart para estética moderna
        color_discrete_sequence=px.colors.qualitative.Vivid # Colores vibrantes
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label'
    )
    
    # Aplicar efecto de "pull" (resaltado) si hay índices seleccionados
    if indices_adestacar:
        # Creamos una lista de 0s (no pull) y 0.2 (pull) según si el índice está en la selección
        # Los índices de Plotly corresponden al orden en el dataframe graficado
        pull_values = [0.2 if i in indices_adestacar else 0 for i in range(len(df_agrupado))]
        fig.update_traces(pull=pull_values)
    
    fig.update_layout(
        template="plotly_dark", # Tema oscuro para coincidir con el fondo de estrellas
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def grafico_top_vehiculos(df, metrica="repostado", n=5):
    """
    Genera un gráfico de barras horizontal con el top N de vehículos según la métrica.
    """
    if df is None or df.empty:
        return None
    
    metrica = metrica.lower()
    if metrica not in df.columns or "vehiculo" not in df.columns:
        return None

    # Agrupar por vehículo y sumar la métrica
    df_top = df.groupby("vehiculo")[metrica].sum().reset_index()
    
    # Ordenar descendente y coger los top N
    df_top = df_top.sort_values(metrica, ascending=False).head(n)
    
    # Ordenar ascendente para que en el gráfico horizontal el mayor salga arriba (Plotly lo dibuja de abajo a arriba)
    df_top = df_top.sort_values(metrica, ascending=True)

    titulo = f"Top {n} Vehículos por {metrica.capitalize()}"
    color_scale = "Viridis" if metrica == "repostado" else "Magma"

    fig = px.bar(
        df_top,
        x=metrica,
        y="vehiculo",
        orientation='h',
        title=titulo,
        text_auto='.2s',
        color=metrica,
        color_continuous_scale=color_scale
    )

    fig.update_layout(
        xaxis_title=metrica.capitalize(),
        yaxis_title="Vehículo",
        template="plotly_white",
        showlegend=False
    )

    return fig