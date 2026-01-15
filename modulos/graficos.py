import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import pandas as pd

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

    # Calcular porcentaje fijo relativo al total del dataframe (la vista actual)
    # Esto asegura que si se ocultan segmentos o se hace pop-out, el porcentaje mostrado es el original
    total_repostado = df_agrupado["repostado"].sum()
    df_agrupado["porcentaje_fijo"] = df_agrupado["repostado"] / total_repostado

    # Crear gráfico de tarta (pie chart)
    fig = px.pie(
        df_agrupado,
        values="repostado",
        names=col_grupo,
        title=titulo,
        hole=0.4, # Donut chart para estética moderna
        color_discrete_sequence=px.colors.qualitative.Vivid, # Colores vibrantes
        custom_data=["porcentaje_fijo"] # Pasamos el porcentaje fijo como dato personalizado
    )
    
    fig.update_traces(
        textposition='inside', 
        # Usamos texttemplate para mostrar la etiqueta y el porcentaje fijo formateado
        # %{label} es el nombre del segmento
        # %{customdata[0]:.1%} formatea el primer elemento de custom_data como porcentaje con 1 decimal
        texttemplate='%{label}<br>%{customdata[0]:.1%}' 
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
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    return fig


def grafico_barras_temporal(df, col_fecha, col_metrica, periodo='M', titulo="Evolución Temporal"):
    """
    Genera un gráfico de barras agrupado por tiempo (Mes 'M' o Semana 'W').
    """
    if df is None or df.empty:
        return None
    
    if col_fecha not in df.columns or col_metrica not in df.columns:
        return None

    # Aseguramos formato fecha
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])

    # Agrupamos
    if periodo == 'W':
        freq_alias = 'W-MON'
    elif periodo == 'M':
        freq_alias = 'MS'
    else: # periodo == 'Y' o 'A'
        freq_alias = 'Y' # 'YE' en pandas nuevos, 'Y' en viejos. Usamos 'Y' por compatibilidad o 'YE' si avisa warning.
    
    df_agrupado = df.groupby(pd.Grouper(key=col_fecha, freq=freq_alias))[col_metrica].sum().reset_index()

    if df_agrupado.empty:
        return None
        
    # Transformaciones a string para eje X categorical (asegura etiquetas en todas las barras)
    if periodo == 'Y':
        df_agrupado[col_fecha] = df_agrupado[col_fecha].dt.year.astype(str)
    elif periodo == 'M':
        # Ordenamos por fecha antes de convertir a string para garantizar orden cronológico
        df_agrupado = df_agrupado.sort_values(col_fecha)
        df_agrupado[col_fecha] = df_agrupado[col_fecha].dt.strftime('%b %Y')

    fig = px.bar(
        df_agrupado,
        x=col_fecha,
        y=col_metrica,
        title=titulo,
        text_auto='.2s',
        color_discrete_sequence=["#00CC96"] 
    )

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=col_metrica.capitalize(),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        bargap=0.2
    )

    # Mejorar eje X
    if periodo == 'W':
         # Semanal (mantenemos fecha continua para semanas)
         fig.update_xaxes(dtick=604800000.0 * 4) 
    # Para periodo == 'Y' o 'M' (Categorical), Plotly maneja etiquetas automáticas para cada barra.

    return fig

def grafico_tarta_distribucion(df, columna, titulo):
    """
    Gráfico circular genérico para distribuciones.
    """
    if df is None or df.empty or columna not in df.columns:
        return None

    if "repostado" in df.columns:
        df_counts = df.groupby(columna)["repostado"].sum().reset_index(name='valor')
    else:
        df_counts = df.groupby(columna).size().reset_index(name='valor')
    
    if df_counts.empty:
        return None

    fig = px.pie(
        df_counts,
        names=columna,
        values='valor',
        title=titulo,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True
    )
    return fig

def grafico_dia_semana(df, col_fecha):
    """
    Gráfico circular indicando el día de la semana de repostaje.
    """
def grafico_dia_semana(df, col_fecha):
    """
    Gráfico de barras indicando el día de la semana de repostaje (Lunes a Domingo).
    """
    if df is None or df.empty or col_fecha not in df.columns:
        return None
    
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])
    
    if df.empty:
        return None

    # Obtener índice de día de semana (0=Lunes, 6=Domingo)
    df['dia_index'] = df[col_fecha].dt.dayofweek
    
    # Agrupar
    # Decidir si sumamos repostado o contamos frecuencia. 
    # Para ser consistente con lo anterior, si hay repostado sumamos, si no contamos.
    if "repostado" in df.columns:
        df_ag = df.groupby('dia_index')["repostado"].sum().reset_index()
        y_col = "repostado"
        ylabel = "Total Repostado"
    else:
        df_ag = df.groupby('dia_index').size().reset_index(name='conteo')
        y_col = "conteo"
        ylabel = "Cantidad de Repostajes"

    # Asegurar orden 0-6 llenando huecos si faltan días?
    # Mejor mostrar solo lo que hay pero ordenado.
    
    dias_map = {0:"Lunes", 1:"Martes", 2:"Miércoles", 3:"Jueves", 4:"Viernes", 5:"Sábado", 6:"Domingo"}
    df_ag["dia_nombre"] = df_ag["dia_index"].map(dias_map)
    
    # Ordenar explícitamente por índice para garantizar Lunes -> Domingo
    df_ag = df_ag.sort_values("dia_index")
    
    if df_ag.empty:
        return None

    fig = px.bar(
        df_ag,
        x="dia_nombre",
        y=y_col,
        title="Repostajes por Día de la Semana",
        text_auto='.2s',
        color_discrete_sequence=["#AB63FA"] # Un color distinto, ej. violeta
    )
    
    fig.update_layout(
        xaxis_title="Día",
        yaxis_title=ylabel,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig

def grafico_lineal_consumo(df, col_fecha, col_consumo="consumo"):
    """
    Gráfico lineal indicando si el consumo va a más o menos.
    """
    if df is None or df.empty:
        return None
    
    target_col = col_consumo
    if target_col not in df.columns:
        return None
    
    if col_fecha not in df.columns:
        return None
    
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha, target_col])
    df = df.sort_values(col_fecha)
    
    if df.empty:
        return None

    fig = px.line(
        df, 
        x=col_fecha, 
        y=target_col, 
        markers=True,
        title=f"Evolución del {target_col.capitalize()}",
        color_discrete_sequence=["#EF553B"]
    )
    
    if len(df) > 2:
        try:
            trend = px.scatter(df, x=col_fecha, y=target_col, trendline="ols").data[1]
            trend.line.color = 'white'
            trend.line.dash = 'dot'
            fig.add_trace(trend)
        except Exception:
            pass

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Fecha",
        yaxis_title=target_col.capitalize()
    )
    return fig

def grafico_comparativo_modelo(df_total, vehiculo_sel, col_fecha, col_metrica, col_modelo):
    """
    Comparativa: Vehículo Seleccionado vs Media del Modelo.
    """
    if df_total is None or df_total.empty:
        return None
    
    target_modelo = col_modelo
    if target_modelo not in df_total.columns:
        if "tipo_vehiculo" in df_total.columns:
            target_modelo = "tipo_vehiculo"
        else:
            return None

    # 1. Obtener datos del vehículo seleccionado
    df_v = df_total[df_total["vehiculo"].astype(str) == str(vehiculo_sel)]
    if df_v.empty:
        return None
    
    modelo_val = df_v.iloc[0][target_modelo]
    
    # 2. Obtener datos de TODO el modelo (incluyendo o excluyendo el vehículo? usualmente incluyendo para "media del segmento")
    df_modelo = df_total[df_total[target_modelo] == modelo_val].copy()
    
    if df_modelo.empty:
        return None

    if col_fecha not in df_modelo.columns:
        return None

    # Estandarizar fechas
    df_modelo[col_fecha] = pd.to_datetime(df_modelo[col_fecha], errors='coerce')
    df_modelo = df_modelo.dropna(subset=[col_fecha])
    
    df_v = df_v.copy()
    df_v[col_fecha] = pd.to_datetime(df_v[col_fecha], errors='coerce')
    df_v = df_v.dropna(subset=[col_fecha])

    # 3. Calcular métrica mensual (agrupación 'MS')
    freq = 'MS'
    
    # Datos vehículo seleccionado
    df_sel_ag = df_v.groupby(pd.Grouper(key=col_fecha, freq=freq))[col_metrica].sum().reset_index()
    
    # Datos Modelo: Calcular "Promedio Mensual por Vehículo"
    # Primero sumamos por [Mes, Vehículo] para obtener el total de CADA coche en CADA mes
    df_mod_per_veh = df_modelo.groupby([pd.Grouper(key=col_fecha, freq=freq), "vehiculo"])[col_metrica].sum().reset_index()
    
    # Ahora promediamos esos totales por mes -> Esto nos da "Cuánto reposta/recorre en promedio un coche de este modelo al mes"
    df_mod_ag = df_mod_per_veh.groupby(col_fecha)[col_metrica].mean().reset_index()
    
    # Crear Gráfico
    fig = go.Figure()
    
    # Traza: Media del Modelo
    if not df_mod_ag.empty:
        fig.add_trace(go.Scatter(
            x=df_mod_ag[col_fecha],
            y=df_mod_ag[col_metrica],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=2, dash='dash'), 
            name=f"Media {modelo_val}",
            hovertemplate = 'Media: %{y:.1f}<extra></extra>' # Tooltip más limpio
        ))
        
    # Traza: Vehículo Seleccionado
    if not df_sel_ag.empty:
        fig.add_trace(go.Scatter(
            x=df_sel_ag[col_fecha],
            y=df_sel_ag[col_metrica],
            mode='lines+markers',
            line=dict(color='#00CC96', width=4),
            marker=dict(size=8, color='#00CC96', line=dict(width=2, color='white')),
            name=f"{vehiculo_sel}",
            hovertemplate = 'Vehículo: %{y:.1f}<extra></extra>'
        ))

    fig.update_layout(
         title=f"Comparativa {col_metrica.capitalize()} vs Media Modelo ({modelo_val})",
         template="plotly_dark",
         paper_bgcolor='rgba(0,0,0,0)',
         plot_bgcolor='rgba(0,0,0,0)',
         xaxis_title="Fecha",
         yaxis_title=col_metrica.capitalize(),
         hovermode="x unified",
         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig