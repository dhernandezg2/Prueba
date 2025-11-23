import streamlit as st
import pandas as pd

if "df_filtrado" not in st.session_state:
    st.session_state.df_filtrado = None

#Funciones externas
from modulos.filtros import aplicar_filtros
from modulos.graficos import Grafico_lineal_parametros, mapa_repostajes, grafico_general_repostajes
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
st.sidebar.header("Filtros")
tipos_vehiculo = st.sidebar.multiselect("Tipo de vehículo", ["Furgoneta", "Camión", "Sedán"])  #tipos de vehículo
tipos_combustible = st.sidebar.multiselect("Tipo de combustible", ["Gasóleo", "Gasolina 95", "Diésel"])  #tipos de combustible
lugar = st.sidebar.text_input("Dirección") #Direccion

parametro = st.sidebar.selectbox("Parámetro", ["repostado", "distancia", "consumo"])


#Hacemos que los rangos sean dinamicos y no sean siempre 0 - 100 (para los valores numericos)
if df is not None and parametro.lower() in df.columns:
    min_val = float(df[parametro.lower()].min())
    max_val = float(df[parametro.lower()].max())
else:
    min_val, max_val = 0, 100

rango_valores = st.sidebar.slider("Rango de valores", min_val, max_val, (min_val, max_val))

rango_fechas = st.sidebar.date_input("Rango de fechas", [])

aplicar = st.sidebar.button("Aplicar filtros")

if aplicar:

    #Aplicamos los filtros de la columna de la izquierda.
    if df is not None:

        lugar = (lugar or "").strip() or None

        df_filtrado = aplicar_filtros(
            df,
            tipos_vehiculo = tipos_vehiculo,
            tipos_combustible = tipos_combustible,
            lugar = lugar,
            parametro = parametro,
            rango = rango_valores
            )
        st.session_state.df_filtrado = df_filtrado

        # st.subheader(f"Resultados filtrados ({len(df_filtrado)} filas)")
        # st.dataframe(df_filtrado, width='stretch')

df_filtrado = st.session_state.df_filtrado  # Recuperamos el dataframe persistente

# CREACIÓN DE PESTAÑAS
tab_general, tab_detalle = st.tabs(["Vista General", "Análisis Detallado"])

with tab_general:
    # Para la vista general, usamos el filtrado si existe, si no, el completo
    df_general = df_filtrado if df_filtrado is not None else df
    
    if df_general is not None:
        st.subheader(f"Resultados ({len(df_general)} filas)")
        st.dataframe(df_general, width='stretch')
        
        st.divider()
        st.subheader("Resumen General")
        fig_general = grafico_general_repostajes(df_general)
        if fig_general:
            st.plotly_chart(fig_general, width='stretch')
        else:
            st.info("No hay datos suficientes para generar el gráfico general.")
    else:
        st.info("Por favor, carga un archivo para ver los datos.")

with tab_detalle:
    # Para el detalle, SOLO mostramos si hay filtros aplicados (df_filtrado no es None)
    if df_filtrado is not None and not df_filtrado.empty:
        # SELECCION DEL VEHICULO
        st.subheader("Analisis individual del vehiculo")

        if df is None:
            st.info("Sube el archivo")
        else:
            if "vehiculo" not in df.columns:
                st.warning("No existe columna de vehiculos")
            elif df_filtrado is None or df_filtrado.empty:
                st.info("No hay informacion en el dataset")
            else:
                vehiculos = (df_filtrado["vehiculo"].astype(str).dropna().unique())
                vehiculos = sorted([vehiculo for vehiculo in vehiculos if vehiculo.strip() != ""])

                if len(vehiculos) == 0:
                    st.info("No hay vehiculos")
                else:
                    vehiculo_seleccionado = st.selectbox("Selecciona la matricula", vehiculos, index = None, placeholder="Selecciona una matrícula...")
                    
                    if vehiculo_seleccionado:
                        df_vehiculo = df_filtrado[df_filtrado["vehiculo"].astype(str) == str(vehiculo_seleccionado)]
                        st.dataframe(df_vehiculo, width='stretch')

                        #Histogramas del vehiculo
                        st.divider()
                        st.subheader(f"Grafico lineal de {parametro} del vehiculo seleccionado")

                        fig = Grafico_lineal_parametros(df_vehiculo, parametro)

                        if fig:
                            st.plotly_chart(fig, width='stretch')
                        else:
                            st.warning(f"No se generó el gráfico. Asegúrate de que el parámetro '{parametro}' exista en las columnas: {df_vehiculo.columns.tolist()}")

                        st.divider()
                        st.subheader(f"Mapa de repostajes del vehiculo {vehiculo_seleccionado}")

                        # Selector de estilo de mapa
                        estilo_mapa = st.radio(
                            "Estilo del mapa:",
                            ["Claro", "Oscuro"],
                            horizontal=True
                        )

                        fig_mapa = mapa_repostajes(df_vehiculo, vehiculo_seleccionado, estilo=estilo_mapa)

                        if fig_mapa:
                            st.pydeck_chart(fig_mapa, key=f"mapa_{estilo_mapa}")
                        else:
                            st.warning("No se generó el gráfico")
                    else:
                        st.info("Selecciona una matrícula para ver los detalles.")

    else:
        st.info("Aplica los filtros para ver los vehículos disponibles.")
