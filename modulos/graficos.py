import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import pandas as pd

#Mapa interactivo 3D con Pydeck
def mapa_repostajes(df, vehiculo, estilo="Claro"):

    if df is None or df.empty:
        return None
    
    #Validamos las columnas necesarias
    columnas_necesarias = {"vehiculo", "latitud", "longitud"}

    if not columnas_necesarias.issubset(set(df.columns)):
        return None
    
    df_vehiculo = df[df["vehiculo"].astype(str) == str(vehiculo)].copy()
    if df_vehiculo.empty:
        return None
    
    df_vehiculo = df_vehiculo.dropna(subset = ["latitud", "longitud"])
    if df_vehiculo.empty:
        return None
    
    # Configuración de la vista inicial centrada en los datos
    lat_center = df_vehiculo["latitud"].mean()
    lon_center = df_vehiculo["longitud"].mean()

    view_state = pdk.ViewState(
        latitude=lat_center,
        longitude=lon_center,
        zoom=15,
        pitch=60,
        bearing=0
    )

    # Capas del mapa
    layers = []

    # Si es "Oscuro", añadimos la capa de imágenes satelitales como base
    if estilo == "Oscuro":
        satellite_layer = pdk.Layer(
            "TileLayer",
            data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            min_zoom=0,
            max_zoom=19,
            tileSize=256,
            render_sub_layers=True,
            refinement_strategy="no-overlap"
        )
        layers.append(satellite_layer)
        map_style = None
    else:
        # Por defecto Claro
        map_style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

    # Capa de puntos de repostaje
    points_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_vehiculo,
        get_position='[longitud, latitud]',
        get_color='[255, 50, 50, 220]', #Color del punto de repostaje.
        get_radius=20, #Radio del punto de repostaje.
        get_line_color=[255, 255, 255], #Color del borde del punto de repostaje.
        line_width_min_pixels=2, 
        pickable=True,
        auto_highlight=True
    )
    layers.append(points_layer)

    #Tooltip personalizado
    tooltip = {
        "html": "<b>Dirección:</b> {direccion}<br/><b>Repostado:</b> {repostado} L",
        "style": {"backgroundColor": "rgba(255,255,255,0.9)", "color": "#333", "border": "2px solid #ff3232"}
    }

    # Creamos el objeto
    mapa = pdk.Deck(
        map_style=map_style,
        initial_view_state=view_state,
        layers=layers,
        tooltip=tooltip
    )
    return mapa

"""
Genera un grafico de barras agrupado por tiempo.
"""
def grafico_barras_temporal(df, col_fecha, col_metrica, periodo='M', titulo="Evolución Temporal"):

    if df is None or df.empty:
        return None
    
    if col_fecha not in df.columns or col_metrica not in df.columns:
        return None

    # Aseguramos formato fecha
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])

    if periodo == 'W':
        frecuencia = 'W-MON'
    elif periodo == 'M':
        frecuencia = 'MS'
    else:
        frecuencia = 'Y' 
    
    datos_agrupados = df.groupby(pd.Grouper(key=col_fecha, freq=frecuencia))[col_metrica].sum().reset_index()

    if datos_agrupados.empty:
        return None
        
    if periodo == 'Y':
        datos_agrupados[col_fecha] = datos_agrupados[col_fecha].dt.year.astype(str)
    elif periodo == 'M':
        datos_agrupados = datos_agrupados.sort_values(col_fecha)
        datos_agrupados[col_fecha] = datos_agrupados[col_fecha].dt.strftime('%b %Y').str.lower()

    fig = px.bar(
        datos_agrupados,
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

    if periodo == 'W':
        fig.update_xaxes(dtick=604800000.0 * 4) 

    return fig

"""
Grafico circular indicando el día de la semana de repostaje.
"""
def grafico_tarta_distribucion(df, columna, titulo):

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

"""
Grafico de barras indicando el dia de la semana de repostaje.
"""
def grafico_dia_semana(df, col_fecha):

    if df is None or df.empty or col_fecha not in df.columns:
        return None
    
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])
    
    if df.empty:
        return None

    # Obtiene el índice del día de semana (0=Lunes, 6=Domingo)
    df['dia_index'] = df[col_fecha].dt.dayofweek
    
    # Si hay repostado sumamos, si no contamos.
    if "repostado" in df.columns:
        datos_agrupados = df.groupby('dia_index')["repostado"].sum().reset_index()
        columna_y = "repostado"
        etiqueta_y = "Total Repostado"
    else:
        datos_agrupados = df.groupby('dia_index').size().reset_index(name='conteo')
        columna_y = "conteo"
        etiqueta_y = "Cantidad de Repostajes"

    
    dias_semana = {0:"lunes", 1:"martes", 2:"miércoles", 3:"jueves", 4:"viernes", 5:"sábado", 6:"domingo"}
    datos_agrupados["dia_nombre"] = datos_agrupados["dia_index"].map(dias_semana)
    
    # Ordena por índice para garantizar el orden de lunes a domingo
    datos_agrupados = datos_agrupados.sort_values("dia_index")
    
    if datos_agrupados.empty:
        return None

    fig = px.bar(
        datos_agrupados,
        x="dia_nombre",
        y=columna_y,
        title="Repostajes por Día de la Semana",
        text_auto='.2s',
        color_discrete_sequence=["#AB63FA"]
    )
    
    fig.update_layout(
        xaxis_title="Día",
        yaxis_title=etiqueta_y,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig

"""
Grafico lineal indicando si el consumo va a más o menos.
"""
def grafico_lineal_consumo(df, col_fecha, col_consumo="consumo"):

    if df is None or df.empty:
        return None
    
    columna_consumo = col_consumo
    if columna_consumo not in df.columns:
        return None
    
    if col_fecha not in df.columns:
        return None
    
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha, columna_consumo])
    df = df.sort_values(col_fecha)
    
    if df.empty:
        return None

    fig = px.line(
        df, 
        x=col_fecha, 
        y=columna_consumo, 
        markers=True,
        title=f"Evolución del {columna_consumo.capitalize()}",
        color_discrete_sequence=["#EF553B"]
    )
    
    if len(df) > 2:
        try:
            tendencia = px.scatter(df, x=col_fecha, y=columna_consumo, trendline="ols").data[1]
            tendencia.line.color = 'white'
            tendencia.line.dash = 'dot'
            fig.add_trace(tendencia)
        except Exception:
            pass

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Fecha",
        yaxis_title=columna_consumo.capitalize()
    )
    return fig

"""
Comparativa: Vehículo Seleccionado vs Media del Modelo.
"""
def grafico_comparativo_modelo(df_total, vehiculo_sel, col_fecha, col_metrica, col_modelo):

    if df_total is None or df_total.empty:
        return None
    
    columna_modelo = col_modelo
    if columna_modelo not in df_total.columns:
        if "tipo_vehiculo" in df_total.columns:
            columna_modelo = "tipo_vehiculo"
        else:
            return None

    # 1. Obtiene los datos del vehículo seleccionado.
    datos_vehiculo = df_total[df_total["vehiculo"].astype(str) == str(vehiculo_sel)]
    if datos_vehiculo.empty:
        return None
    
    nombre_modelo = datos_vehiculo.iloc[0][columna_modelo]

    # 2. Obtiene los datos de todo el modelo y calcula la media mensual.
    datos_modelo = df_total[df_total[columna_modelo] == nombre_modelo].copy()
    
    if datos_modelo.empty:
        return None

    if col_fecha not in datos_modelo.columns:
        return None

    # Estandariza las fechas.
    datos_modelo[col_fecha] = pd.to_datetime(datos_modelo[col_fecha], errors='coerce')
    datos_modelo = datos_modelo.dropna(subset=[col_fecha])
    
    datos_vehiculo = datos_vehiculo.copy()
    datos_vehiculo[col_fecha] = pd.to_datetime(datos_vehiculo[col_fecha], errors='coerce')
    datos_vehiculo = datos_vehiculo.dropna(subset=[col_fecha])

    # 3. Calcula la métrica mensual. 
    frecuencia = 'MS'
    
    # Datos del vehículo seleccionado
    datos_vehiculo_agrupados = datos_vehiculo.groupby(pd.Grouper(key=col_fecha, freq=frecuencia))[col_metrica].sum().reset_index()
    
    # Primero sumamos por [Mes, Vehículo] para obtener el total de CADA coche en CADA mes
    datos_modelo_por_vehiculo = datos_modelo.groupby([pd.Grouper(key=col_fecha, freq=frecuencia), "vehiculo"])[col_metrica].sum().reset_index()
    
    # Ahora promediamos esos totales por mes dando como resultado el promedio mensual de repostajes del modelo
    datos_modelo_agrupados = datos_modelo_por_vehiculo.groupby(col_fecha)[col_metrica].mean().reset_index()
    
    # Crea el gráfico
    fig = go.Figure()
    
    #Datos de la media del modelo
    if not datos_modelo_agrupados.empty:
        fig.add_trace(go.Scatter(
            x=datos_modelo_agrupados[col_fecha],
            y=datos_modelo_agrupados[col_metrica],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=2, dash='dash'), 
            name=f"Media {nombre_modelo}",
            hovertemplate = 'Media: %{y:.1f}<extra></extra>'
        ))
        
    #Datos del vehículo seleccionado
    if not datos_vehiculo_agrupados.empty:
        fig.add_trace(go.Scatter(
            x=datos_vehiculo_agrupados[col_fecha],
            y=datos_vehiculo_agrupados[col_metrica],
            mode='lines+markers',
            line=dict(color='#00CC96', width=4),
            marker=dict(size=8, color='#00CC96', line=dict(width=2, color='white')),
            name=f"{vehiculo_sel}",
            hovertemplate = 'Vehículo: %{y:.1f}<extra></extra>'
        ))

    fig.update_layout(
         title=f"Comparativa {col_metrica.capitalize()} vs Media Modelo ({nombre_modelo})",
         template="plotly_dark",
         paper_bgcolor='rgba(0,0,0,0)',
         plot_bgcolor='rgba(0,0,0,0)',
         xaxis_title="Fecha",
         yaxis_title=col_metrica.capitalize(),
         hovermode="x unified",
         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig