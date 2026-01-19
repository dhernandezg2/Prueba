import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import pandas as pd

# Configuración común para layouts oscuros
def aplicar_estilo_oscuro(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# Gráfico de área para evolución de parámetros
def Grafico_lineal_parametros(df, parametro):
    if df is None or df.empty:
        return None
    
    columna = parametro.lower()
    if columna not in df.columns:
        return None
    
    # Determinar eje X (fecha o índice)
    if "fecha" in df.columns:
        df = df.sort_values("fecha")
        eje_x = "fecha"
    else:
        eje_x = df.index.name if df.index.name else "index"

    # Crear gráfico de área suavizado
    fig = px.area(
        df,
        x=eje_x,
        y=columna,
        markers=True,
        title=f"Evolución de {columna}",
        color_discrete_sequence=["#00CC96"]
    )

    fig.update_traces(
        line=dict(width=3, shape='spline'),
        marker=dict(size=8, symbol='circle', line=dict(width=2, color='white')),
        fill='tozeroy'
    )
    
    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        xaxis_title="Fecha" if eje_x == "fecha" else "",
        yaxis_title=columna.capitalize(),
        hovermode="x unified",
        font=dict(family="Inter, sans-serif", size=14)
    )
    return fig

# Mapa interactivo 3D de repostajes
def mapa_repostajes(df, vehiculo, estilo="Claro"):
    if df is None or df.empty:
        return None
    
    # Validar columnas necesarias
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
    latitud_centro = df_vehiculo["latitud"].mean()
    longitud_centro = df_vehiculo["longitud"].mean()

    vista_inicial = pdk.ViewState(
        latitude=latitud_centro,
        longitude=longitud_centro,
        zoom=15,
        pitch=60,
        bearing=0
    )

    # Configurar capas del mapa según el estilo
    capas = []
    
    if estilo == "Oscuro":
        capa_satelite = pdk.Layer(
            "TileLayer",
            data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            min_zoom=0,
            max_zoom=19,
            tileSize=256,
            render_sub_layers=True,
            refinement_strategy="no-overlap"
        )
        capas.append(capa_satelite)
        estilo_mapa = None
    else:
        estilo_mapa = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

    # Capa de puntos de repostaje
    capa_puntos = pdk.Layer(
        "ScatterplotLayer",
        data=df_vehiculo,
        get_position='[longitud, latitud]',
        get_color='[255, 50, 50, 220]',
        get_radius=20,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True
    )
    capas.append(capa_puntos)

    # Configurar tooltip
    tooltip = {
        "html": "<b>Dirección:</b> {direccion}<br/><b>Repostado:</b> {repostado} L",
        "style": {"backgroundColor": "rgba(255,255,255,0.9)", "color": "#333", "border": "2px solid #ff3232"}
    }

    # Crear mapa
    mapa = pdk.Deck(
        map_style=estilo_mapa,
        initial_view_state=vista_inicial,
        layers=capas,
        tooltip=tooltip
    )
    return mapa

def grafico_general_repostajes(df, indices_adestacar=None):
    """Gráfico de tarta mostrando el total repostado por tipo de vehículo."""
    if df is None or df.empty or "repostado" not in df.columns:
        return None
    # Determinar columna de agrupación (tipo_vehiculo o vehiculo)
    if "tipo_vehiculo" in df.columns:
        columna_grupo = "tipo_vehiculo"
        titulo = "Total Repostado por Tipo de Vehículo"
    elif "vehiculo" in df.columns:
        columna_grupo = "vehiculo"
        titulo = "Total Repostado por Vehículo"
    else:
        return None

    # Agrupar y sumar
    datos_agrupados = df.groupby(columna_grupo)["repostado"].sum().reset_index()
    
    if datos_agrupados.empty:
        return None
    
    # Ordenar por valor descendente
    datos_agrupados = datos_agrupados.sort_values(by="repostado", ascending=False)

    # Calcular porcentaje fijo relativo al total
    total_repostado = datos_agrupados["repostado"].sum()
    datos_agrupados["porcentaje_fijo"] = datos_agrupados["repostado"] / total_repostado

    # Crear gráfico de tarta
    fig = px.pie(
        datos_agrupados,
        values="repostado",
        names=columna_grupo,
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
        valores_pull = [0.2 if i in indices_adestacar else 0 for i in range(len(datos_agrupados))]
        fig.update_traces(pull=valores_pull)
    
    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def grafico_top_vehiculos(df, metrica="repostado", n=5):
    """Gráfico de barras horizontal con el top N de vehículos según la métrica."""
    if df is None or df.empty:
        return None
    
    metrica = metrica.lower()
    if metrica not in df.columns or "vehiculo" not in df.columns:
        return None

    # Agrupar por vehículo y sumar la métrica
    datos_top = df.groupby("vehiculo")[metrica].sum().reset_index()
    
    # Ordenar descendente y coger los top N
    datos_top = datos_top.sort_values(metrica, ascending=False).head(n)
    
    # Ordenar ascendente para que en el gráfico horizontal el mayor salga arriba
    datos_top = datos_top.sort_values(metrica, ascending=True)

    titulo = f"Top {n} Vehículos por {metrica.capitalize()}"
    color_scale = "Viridis" if metrica == "repostado" else "Magma"

    fig = px.bar(
        datos_top,
        x=metrica,
        y="vehiculo",
        orientation='h',
        title=titulo,
        text_auto='.2s',
        color=metrica,
        color_continuous_scale=color_scale
    )

    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        xaxis_title=metrica.capitalize(),
        yaxis_title="Vehículo",
        showlegend=False
    )
    return fig


def grafico_barras_temporal(df, col_fecha, col_metrica, periodo='M', titulo="Evolución Temporal"):
    """Gráfico de barras agrupado por tiempo (Mes 'M', Semana 'W' o Año 'Y')."""
    if df is None or df.empty:
        return None
    
    if col_fecha not in df.columns or col_metrica not in df.columns:
        return None

    # Preparar fechas
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])

    # Determinar frecuencia
    frecuencias = {'W': 'W-MON', 'M': 'MS', 'Y': 'Y'}
    frecuencia = frecuencias.get(periodo, 'MS')
    
    datos_agrupados = df.groupby(pd.Grouper(key=col_fecha, freq=frecuencia))[col_metrica].sum().reset_index()

    if datos_agrupados.empty:
        return None
    
    # Formatear fechas para el eje X
    if periodo == 'Y':
        datos_agrupados[col_fecha] = datos_agrupados[col_fecha].dt.year.astype(str)
    elif periodo == 'M':
        datos_agrupados = datos_agrupados.sort_values(col_fecha)
        datos_agrupados[col_fecha] = datos_agrupados[col_fecha].dt.strftime('%b %Y')

    fig = px.bar(
        datos_agrupados,
        x=col_fecha,
        y=col_metrica,
        title=titulo,
        text_auto='.2s',
        color_discrete_sequence=["#00CC96"] 
    )

    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=col_metrica.capitalize(),
        bargap=0.2
    )

    if periodo == 'W':
        fig.update_xaxes(dtick=604800000.0 * 4)

    return fig

def grafico_tarta_distribucion(df, columna, titulo):
    """Gráfico circular genérico para distribuciones."""
    if df is None or df.empty or columna not in df.columns:
        return None

    if "repostado" in df.columns:
        datos_conteo = df.groupby(columna)["repostado"].sum().reset_index(name='valor')
    else:
        datos_conteo = df.groupby(columna).size().reset_index(name='valor')
    
    if datos_conteo.empty:
        return None

    fig = px.pie(
        datos_conteo,
        names=columna,
        values='valor',
        title=titulo,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    aplicar_estilo_oscuro(fig)
    fig.update_layout(showlegend=True)
    return fig

def grafico_dia_semana(df, col_fecha):
    """Gráfico de barras por día de la semana (Lunes a Domingo)."""
    if df is None or df.empty or col_fecha not in df.columns:
        return None
    
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha])
    
    if df.empty:
        return None

    # Obtener índice de día de semana (0=Lunes, 6=Domingo)
    df['indice_dia'] = df[col_fecha].dt.dayofweek
    
    # Agrupar por día
    if "repostado" in df.columns:
        datos_agrupados = df.groupby('indice_dia')["repostado"].sum().reset_index()
        columna_y = "repostado"
        etiqueta_y = "Total Repostado"
    else:
        datos_agrupados = df.groupby('indice_dia').size().reset_index(name='conteo')
        columna_y = "conteo"
        etiqueta_y = "Cantidad de Repostajes"
    
    # Mapear índices a nombres de días
    dias_semana = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
    datos_agrupados["nombre_dia"] = datos_agrupados["indice_dia"].map(dias_semana)
    datos_agrupados = datos_agrupados.sort_values("indice_dia")
    
    if datos_agrupados.empty:
        return None

    fig = px.bar(
        datos_agrupados,
        x="nombre_dia",
        y=columna_y,
        title="Repostajes por Día de la Semana",
        text_auto='.2s',
        color_discrete_sequence=["#AB63FA"]
    )
    
    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        xaxis_title="Día",
        yaxis_title=etiqueta_y,
        showlegend=False
    )
    return fig

def grafico_lineal_consumo(df, col_fecha, col_consumo="consumo"):
    """Gráfico lineal de tendencia de consumo."""
    if df is None or df.empty:
        return None
    
    if col_consumo not in df.columns or col_fecha not in df.columns:
        return None
    
    df = df.copy()
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df = df.dropna(subset=[col_fecha, col_consumo])
    df = df.sort_values(col_fecha)
    
    if df.empty:
        return None

    fig = px.line(
        df,
        x=col_fecha,
        y=col_consumo,
        markers=True,
        title=f"Evolución del {col_consumo.capitalize()}",
        color_discrete_sequence=["#EF553B"]
    )
    
    # Añadir línea de tendencia
    if len(df) > 2:
        try:
            tendencia = px.scatter(df, x=col_fecha, y=col_consumo, trendline="ols").data[1]
            tendencia.line.color = 'white'
            tendencia.line.dash = 'dot'
            fig.add_trace(tendencia)
        except Exception:
            pass

    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=col_consumo.capitalize()
    )
    return fig

def grafico_comparativo_modelo(df_total, vehiculo_sel, col_fecha, col_metrica, col_modelo):
    """Comparativa: Vehículo seleccionado vs media del modelo."""
    if df_total is None or df_total.empty:
        return None
    
    columna_modelo = col_modelo
    if columna_modelo not in df_total.columns:
        if "tipo_vehiculo" in df_total.columns:
            columna_modelo = "tipo_vehiculo"
        else:
            return None

    # Obtener datos del vehículo seleccionado
    datos_vehiculo = df_total[df_total["vehiculo"].astype(str) == str(vehiculo_sel)]
    if datos_vehiculo.empty:
        return None
    
    valor_modelo = datos_vehiculo.iloc[0][columna_modelo]
    
    # Obtener datos de todos los vehículos del mismo modelo
    datos_modelo = df_total[df_total[columna_modelo] == valor_modelo].copy()
    
    if datos_modelo.empty or col_fecha not in datos_modelo.columns:
        return None

    # Convertir fechas a formato datetime
    datos_modelo[col_fecha] = pd.to_datetime(datos_modelo[col_fecha], errors='coerce')
    datos_modelo = datos_modelo.dropna(subset=[col_fecha])
    
    datos_vehiculo = datos_vehiculo.copy()
    datos_vehiculo[col_fecha] = pd.to_datetime(datos_vehiculo[col_fecha], errors='coerce')
    datos_vehiculo = datos_vehiculo.dropna(subset=[col_fecha])

    # Calcular métrica mensual
    frecuencia = 'MS'
    
    # Datos del vehículo seleccionado agrupados por mes
    vehiculo_mensual = datos_vehiculo.groupby(pd.Grouper(key=col_fecha, freq=frecuencia))[col_metrica].sum().reset_index()
    
    # Calcular promedio mensual del modelo
    modelo_por_vehiculo = datos_modelo.groupby([pd.Grouper(key=col_fecha, freq=frecuencia), "vehiculo"])[col_metrica].sum().reset_index()
    modelo_mensual = modelo_por_vehiculo.groupby(col_fecha)[col_metrica].mean().reset_index()
    
    # Crear gráfico comparativo
    fig = go.Figure()
    
    # Traza: Media del modelo
    if not modelo_mensual.empty:
        fig.add_trace(go.Scatter(
            x=modelo_mensual[col_fecha],
            y=modelo_mensual[col_metrica],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=2, dash='dash'), 
            name=f"Media {valor_modelo}",
            hovertemplate='Media: %{y:.1f}<extra></extra>'
        ))
    
    # Traza: Vehículo seleccionado
    if not vehiculo_mensual.empty:
        fig.add_trace(go.Scatter(
            x=vehiculo_mensual[col_fecha],
            y=vehiculo_mensual[col_metrica],
            mode='lines+markers',
            line=dict(color='#00CC96', width=4),
            marker=dict(size=8, color='#00CC96', line=dict(width=2, color='white')),
            name=f"{vehiculo_sel}",
            hovertemplate='Vehículo: %{y:.1f}<extra></extra>'
        ))

    aplicar_estilo_oscuro(fig)
    fig.update_layout(
        title=f"Comparativa {col_metrica.capitalize()} vs Media Modelo ({valor_modelo})",
        xaxis_title="Fecha",
        yaxis_title=col_metrica.capitalize(),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig