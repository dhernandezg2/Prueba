import streamlit as st
import pandas as pd

if "df_filtrado" not in st.session_state:
    st.session_state.df_filtrado = None

#Funciones externas
from modulos.filtros import aplicar_filtros
from modulos.graficos import Grafico_lineal_parametros, mapa_repostajes, grafico_general_repostajes, grafico_top_vehiculos
from modulos.utilidades import set_star_background

set_star_background()


# CONFIGURACIÓN GENERAL 
st.set_page_config(page_title="Repostajes", layout="wide")
st.title("🚗 Análisis de Repostajes")

# CARGA DE DATOS
st.sidebar.header("Datos de entrada")
modo = st.sidebar.radio("Fuente de datos", ["📤 Subir archivo"])

if modo == "📤 Subir archivo":
    archivo = st.sidebar.file_uploader("Sube un Excel (.xlsx)", type=["xlsx"])
    if archivo:

        df = pd.read_excel(archivo)  #lee el excel que se carga

        #Vista previa de los datos subidos
        st.subheader("Vista previa de los datos")
        st.dataframe(df.head(10), width='stretch') 

        #Transformo las columnas a minusculas
        df.columns = df.columns.str.lower().str.strip()
    
    else:
        df = None
else:
    st.sidebar.button("Cargar")

st.sidebar.divider()

# FILTROS LATERALES
@st.fragment
def mostrar_filtros_laterales(df):
    st.header("Filtros")

    # Inicializar opciones vacías
    # Inicializar variables de selección desde session_state si existen para usar en el filtrado cruzado
    # Esto permite que el filtrado sea bidireccional (Vehículo <-> Combustible <-> Dirección)

    sel_vehiculos = st.session_state.get("filter_vehiculo", [])
    sel_combustibles = st.session_state.get("filter_combustible", [])
    sel_direcciones = st.session_state.get("filter_direccion", [])

    # Función auxiliar para obtener opciones válidas
    def obtener_opciones_validas(df, col_objetivo, filtros_dict):
        if df is None:
            return []
        
        df_temp = df.copy()
        for col, valores in filtros_dict.items():
            if valores and col in df_temp.columns:
                df_temp = df_temp[df_temp[col].isin(valores)]
                
        if col_objetivo in df_temp.columns:
            return sorted(df_temp[col_objetivo].dropna().unique())
        return []

    # Calcular opciones disponibles para cada filtro basado en los OTROS filtros seleccionados
    if df is not None:
        opciones_tipo_vehiculo = obtener_opciones_validas(df, "tipo_vehiculo", {
            "tipo_combustible": sel_combustibles,
            "direccion": sel_direcciones
        })
        
        opciones_tipo_combustible = obtener_opciones_validas(df, "tipo_combustible", {
            "tipo_vehiculo": sel_vehiculos,
            "direccion": sel_direcciones
        })
        
        opciones_direccion = obtener_opciones_validas(df, "direccion", {
            "tipo_vehiculo": sel_vehiculos,
            "tipo_combustible": sel_combustibles
        })
    else:
        opciones_tipo_vehiculo, opciones_tipo_combustible, opciones_direccion = [], [], []

    # Renderizar los widgets con las opciones calculadas y usar keys para persistencia
    # Nota: Streamlit elimina automáticamente opciones seleccionadas que ya no están en la lista de opciones (parametro 'options')
    tipos_vehiculo = st.multiselect("Tipo de vehículo", options=opciones_tipo_vehiculo, key="filter_vehiculo")
    tipos_combustible = st.multiselect("Tipo de combustible", options=opciones_tipo_combustible, key="filter_combustible")
    lugar = st.multiselect("Dirección", options=opciones_direccion, key="filter_direccion")

    parametro = st.selectbox("Parámetro", ["repostado", "distancia", "consumo"])

    #Hacemos que los rangos sean dinamicos y no sean siempre 0 - 100 (para los valores numericos)
    if df is not None and parametro.lower() in df.columns:
        min_val = float(df[parametro.lower()].min())
        max_val = float(df[parametro.lower()].max())
    else:
        min_val, max_val = 0, 100

    rango_valores = st.slider("Rango de valores", min_val, max_val, (min_val, max_val))

    rango_fechas = st.date_input("Rango de fechas", [])

    aplicar = st.button("Aplicar filtros")

    if aplicar:
        # Guardamos el parámetro actual para usarlo fuera del fragmento
        st.session_state.parametro_actual = parametro

        #Aplicamos los filtros de la columna de la izquierda.
        if df is not None:
            df_filtrado = aplicar_filtros(
                df,
                tipos_vehiculo = tipos_vehiculo,
                tipos_combustible = tipos_combustible,
                lugar = lugar,
                parametro = parametro,
                rango = rango_valores,
                fechas = rango_fechas
                )
            st.session_state.df_filtrado = df_filtrado
            st.rerun()

# Llamada a la función de fragmento
with st.sidebar:
    mostrar_filtros_laterales(df)

# Recuperamos variables clave del estado para el resto de la app
if "parametro_actual" not in st.session_state:
    st.session_state.parametro_actual = "repostado" # Valor por defecto

parametro = st.session_state.parametro_actual


df_filtrado = st.session_state.df_filtrado  # Recuperamos el dataframe persistente

# CREACIÓN DE PESTAÑAS
tab_general, tab_filtrada, tab_vehiculo = st.tabs(["Vista General", "Vista Filtrada", "Información del Vehículo"])

with tab_general:
    # Vista General: SIEMPRE usa el dataframe original (df) sin filtrar
    if df is not None:
        st.subheader(f"Resultados Totales ({len(df)} filas)")
        st.dataframe(df, width='stretch')
        
        st.divider()
        st.subheader("Resumen General")
        # Lógica de selección para interactividad (Pop-out)
        key_chart = "chart_general"
        
        # Recuperar selección previa si existe
        indices_seleccionados = []
        if key_chart in st.session_state:
            state = st.session_state[key_chart]
            if state and "selection" in state and "points" in state["selection"]:
                indices_seleccionados = [p["point_index"] for p in state["selection"]["points"]]

        fig_general = grafico_general_repostajes(df, indices_adestacar=indices_seleccionados)
        
        if fig_general:
            st.plotly_chart(fig_general, use_container_width=True, key=key_chart, on_select="rerun")
        else:
            st.info("No hay datos suficientes para generar el gráfico general.")

        st.divider()
        st.subheader("Top Vehículos")
        
        n_top = st.slider("Número de vehículos a mostrar", 1, 20, 5, key="slider_general")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_top_repostado = grafico_top_vehiculos(df, "repostado", n_top)
            if fig_top_repostado:
                st.plotly_chart(fig_top_repostado, use_container_width=True, key="chart_top_repostado_general")
            else:
                st.info("No hay datos de repostaje.")
                
        with col2:
            # Verificamos si existe la columna distancia
            if "distancia" in df.columns:
                fig_top_distancia = grafico_top_vehiculos(df, "distancia", n_top)
                if fig_top_distancia:
                    st.plotly_chart(fig_top_distancia, use_container_width=True, key="chart_top_distancia_general")
                else:
                    st.info("No hay datos de distancia.")
            else:
                st.info("La columna 'distancia' no está disponible en los datos.")

    else:
        st.info("Por favor, carga un archivo para ver los datos.")

with tab_filtrada:
    # Vista Filtrada: Usa df_filtrado
    if df_filtrado is not None and not df_filtrado.empty:
        st.subheader(f"Resultados Filtrados ({len(df_filtrado)} filas)")
        st.dataframe(df_filtrado, width='stretch')
        
        st.divider()
        st.subheader("Resumen Filtrado")
        fig_filtrado = grafico_general_repostajes(df_filtrado)
        if fig_filtrado:
            st.plotly_chart(fig_filtrado, use_container_width=True, key="chart_filtrado")
        else:
            st.info("No hay datos suficientes para generar el gráfico filtrado.")
            
        st.divider()
        st.subheader("Top Vehículos (Filtrado)")
        
        n_top_filt = st.slider("Número de vehículos a mostrar", 1, 20, 5, key="slider_filtrado")
        
        col1_f, col2_f = st.columns(2)
        
        with col1_f:
            fig_top_repostado_f = grafico_top_vehiculos(df_filtrado, "repostado", n_top_filt)
            if fig_top_repostado_f:
                st.plotly_chart(fig_top_repostado_f, use_container_width=True, key="chart_top_repostado_filtrado")
            else:
                st.info("No hay datos de repostaje.")
                
        with col2_f:
            if "distancia" in df_filtrado.columns:
                fig_top_distancia_f = grafico_top_vehiculos(df_filtrado, "distancia", n_top_filt)
                if fig_top_distancia_f:
                    st.plotly_chart(fig_top_distancia_f, use_container_width=True, key="chart_top_distancia_filtrado")
                else:
                    st.info("No hay datos de distancia.")
            else:
                st.info("La columna 'distancia' no está disponible en los datos.")
                
    elif df is None:
        st.info("Por favor, carga un archivo para ver los datos.")
    else:
        st.warning("No hay datos que coincidan con los filtros aplicados.")

with tab_vehiculo:
    # Información del Vehículo
    # Usamos df_filtrado para que la lista de vehículos respete los filtros, 
    # pero si no hay filtros (o no hay resultados), podríamos querer ver todos.
    # Asumiremos que el usuario quiere seleccionar de los vehículos disponibles tras el filtrado.
    
    if df_filtrado is not None and not df_filtrado.empty:
        st.subheader("Análisis Individual del Vehículo")

        if "vehiculo" not in df.columns:
            st.warning("No existe columna de vehiculos")
        else:
            vehiculos = (df_filtrado["vehiculo"].astype(str).dropna().unique())
            vehiculos = sorted([vehiculo for vehiculo in vehiculos if vehiculo.strip() != ""])

            if len(vehiculos) == 0:
                st.info("No hay vehículos disponibles con los filtros actuales.")
            else:
                vehiculo_seleccionado = st.selectbox("Selecciona la matrícula", vehiculos, index=None, placeholder="Selecciona una matrícula...")
                
                if vehiculo_seleccionado:
                    # Filtramos del dataframe filtrado para mantener coherencia, o del original si queremos todo el historial del coche
                    # Generalmente "Información del vehículo" implica todo sobre ese vehículo, pero si estamos filtrando por fecha, 
                    # quizás solo queramos ver ese rango. Mantendremos la coherencia con los filtros globales.
                    df_vehiculo = df_filtrado[df_filtrado["vehiculo"].astype(str) == str(vehiculo_seleccionado)]
                    
                    st.dataframe(df_vehiculo, width='stretch')

                    # Histogramas del vehiculo
                    st.divider()
                    st.subheader(f"Gráfico lineal de {parametro} del vehículo seleccionado")

                    fig = Grafico_lineal_parametros(df_vehiculo, parametro)

                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key="chart_lineal_vehiculo")
                    else:
                        st.warning(f"No se generó el gráfico. Asegúrate de que el parámetro '{parametro}' exista.")

                    st.divider()
                    st.subheader(f"Mapa de repostajes del vehículo {vehiculo_seleccionado}")

                    # Selector de estilo de mapa
                    estilo_mapa = st.radio(
                        "Estilo del mapa:",
                        ["Claro", "Oscuro"],
                        horizontal=True,
                        key="estilo_mapa_vehiculo"
                    )

                    fig_mapa = mapa_repostajes(df_vehiculo, vehiculo_seleccionado, estilo=estilo_mapa)

                    if fig_mapa:
                        st.pydeck_chart(fig_mapa) # key ya no es estrictamente necesario si no hay conflicto, pero pydeck_chart lo maneja
                    else:
                        st.warning("No se generó el mapa.")
                else:
                    st.info("Selecciona una matrícula para ver los detalles.")
    elif df is None:
        st.info("Por favor, carga un archivo para ver los datos.")
    else:
        st.warning("No hay vehículos disponibles con los filtros actuales.")
