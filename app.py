import streamlit as st
import pandas as pd

if "datos_filtrados" not in st.session_state:
    st.session_state.datos_filtrados = None

# Funciones externas
from modulos.filtros import aplicar_filtros
from modulos.graficos import (
    mapa_repostajes,
    grafico_barras_temporal,
    grafico_tarta_distribucion,
    grafico_dia_semana,
    grafico_lineal_consumo,
    grafico_comparativo_modelo
)
from modulos.utilidades import set_star_background

set_star_background()


# Configuración general
st.set_page_config(page_title="Repostajes", layout="wide")
st.title("🚗 Análisis de Repostajes")

# Carga de datos
st.sidebar.header("Datos de entrada")
modo = st.sidebar.radio("Fuente de datos", ["📤 Subir archivo"])

if modo == "📤 Subir archivo":
    archivo = st.sidebar.file_uploader("Sube un Excel (.xlsx)", type=["xlsx"])
    if archivo:

        df = pd.read_excel(archivo)  #lee el excel que se carga

        #Vista previa de los datos subidos
        st.subheader("Vista previa de los datos")
        st.dataframe(df.head(10), width='stretch') 

        #Se transforman las columnas a minusculas
        df.columns = df.columns.str.lower().str.strip()

        #Se estandariza la columna 'provincia'
        if "provincia" not in df.columns:
            if "direccion" in df.columns:
                # Se extrae provincia de dirección
                def extraer_provincia(dir_str):
                    parts = str(dir_str).split(',')
                    if len(parts) > 1:
                        return parts[1].strip()
                    return str(dir_str).strip()
                df["provincia"] = df["direccion"].apply(extraer_provincia)
            else:
                st.error("El archivo no tiene columna 'provincia' ni 'direccion'.")
                df = None
    
    else:
        df = None
else:
    st.sidebar.button("Cargar")

st.sidebar.divider()

# Filtros del panel lateral
def mostrar_filtros_laterales(df):
    st.header("Filtros")

    # Se inicializan las opciones vacías
    vehiculos_seleccionados = st.session_state.get("filter_vehiculo", [])
    combustibles_seleccionados = st.session_state.get("filter_combustible", [])
    provincias_seleccionadas = st.session_state.get("filter_provincia", [])

    # Función auxiliar para obtener opciones válidas basadas en otros filtros
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

    # Calcula las opciones disponibles para cada filtro basado en los otros filtros seleccionados
    if df is not None:
        vehiculos_disponibles = obtener_opciones_validas(df, "tipo_vehiculo", {
            "tipo_combustible": combustibles_seleccionados,
            "provincia": provincias_seleccionadas
        })
        
        combustibles_disponibles = obtener_opciones_validas(df, "tipo_combustible", {
            "tipo_vehiculo": vehiculos_seleccionados,
            "provincia": provincias_seleccionadas
        })
        
        provincias_disponibles = obtener_opciones_validas(df, "provincia", {
            "tipo_vehiculo": vehiculos_seleccionados,
            "tipo_combustible": combustibles_seleccionados
        })
        
        # Asegura que las opciones seleccionadas sigan disponibles en la lista
        opciones_tipo_vehiculo = sorted(list(set(vehiculos_disponibles) | set(vehiculos_seleccionados)))
        opciones_tipo_combustible = sorted(list(set(combustibles_disponibles) | set(combustibles_seleccionados)))
        opciones_provincia = sorted(list(set(provincias_disponibles) | set(provincias_seleccionadas)))

    else:
        opciones_tipo_vehiculo, opciones_tipo_combustible, opciones_provincia = [], [], []

    # Renderiza los widgets con las opciones completas
    tipos_vehiculo = st.multiselect("Tipo de vehículo", options=opciones_tipo_vehiculo, key="filter_vehiculo")
    tipos_combustible = st.multiselect("Tipo de combustible", options=opciones_tipo_combustible, key="filter_combustible")
    provincia = st.multiselect("Provincia", options=opciones_provincia, key="filter_provincia")
    
    # Filtros de rangos para métricas numéricas
    metricas_rango = ["repostado", "distancia", "consumo"]
    rangos_activos = {}

    st.subheader("Rangos")
    for metrica in metricas_rango:
        if df is not None and metrica in df.columns:
            # Calcula el min/max y asegura que el tipo sea numérico
            datos_columna = pd.to_numeric(df[metrica], errors='coerce').dropna()
            
            if not datos_columna.empty:
                valor_min = float(datos_columna.min())
                valor_max = float(datos_columna.max())
                
                if valor_min < valor_max:
                    rango_seleccionado = st.slider(f"Rango {metrica.capitalize()}", valor_min, valor_max, (valor_min, valor_max), key=f"slider_{metrica}")
                    rangos_activos[metrica] = rango_seleccionado
                else:
                    st.info(f"{metrica.capitalize()}: {valor_min}")
    
    rango_fechas = st.date_input("Rango de fechas", [])

    aplicar = st.button("Aplicar filtros")

    if aplicar:
        if df is not None:
            datos_filtrados = aplicar_filtros(
                df,
                tipos_vehiculo=tipos_vehiculo,
                tipos_combustible=tipos_combustible,
                provincia=provincia,
                rangos=rangos_activos,
                fechas=rango_fechas
            )
            st.session_state.datos_filtrados = datos_filtrados
            st.rerun()

# Llamada a la función para mostrar los filtros
with st.sidebar:
    mostrar_filtros_laterales(df)

# Recupera los datos filtrados 
datos_filtrados = st.session_state.datos_filtrados
datos_activos = datos_filtrados if datos_filtrados is not None else df

# Crea las distintas pestañas
tab_general, tab_provincia, tab_vehiculo = st.tabs(["Vista General", "Vista por Provincia", "Detalle Vehículo"])

# Función para mostrar los gráficos repetidos en General y Provincia
def mostrar_graficos_resumen(datos_locales, clave_sufijo=""):

    if datos_locales is None or datos_locales.empty:
        st.info("No hay datos para mostrar.")
        return

    # 1. Gráficos Temporales
    col1, col2 = st.columns(2)
    with col1:
        if "repostado" in datos_locales.columns and "fecha" in datos_locales.columns:
            fig_rep = grafico_barras_temporal(datos_locales, "fecha", "repostado", "M", "Repostado Mensual (l)")
            if fig_rep: st.plotly_chart(fig_rep, use_container_width=True, key=f"bar_rep_{clave_sufijo}")
    
    with col2:
        if "distancia" in datos_locales.columns and "fecha" in datos_locales.columns:
            fig_dist = grafico_barras_temporal(datos_locales, "fecha", "distancia", "M", "Recorrido Mensual (km)")
            if fig_dist: st.plotly_chart(fig_dist, use_container_width=True, key=f"bar_dist_{clave_sufijo}")
            
    st.divider()
    
    # 2. Tipos de Combustible y Día de la Semana
    col3, col4 = st.columns(2)
    with col3:
        if "tipo_combustible" in datos_locales.columns:
            fig_comb = grafico_tarta_distribucion(datos_locales, "tipo_combustible", "Tipos de Combustible")
            if fig_comb: st.plotly_chart(fig_comb, use_container_width=True, key=f"pie_comb_{clave_sufijo}")
            
    with col4:
        if "fecha" in datos_locales.columns:
            fig_sem = grafico_dia_semana(datos_locales, "fecha")
            if fig_sem: st.plotly_chart(fig_sem, use_container_width=True, key=f"pie_sem_{clave_sufijo}")

    st.divider()

with tab_general:
    if datos_activos is not None:
        st.subheader("Vista General de la Flota")
        mostrar_graficos_resumen(datos_activos, "general")
    else:
        st.info("Carga un archivo para ver los datos.")

with tab_provincia:
    if datos_activos is not None:
        st.subheader("Vista por Provincia")
        
        if "provincia" in datos_activos.columns:
            lugares = sorted(datos_activos["provincia"].astype(str).unique())
            lugar_sel = st.selectbox("Selecciona Provincia:", lugares, index=0)
            
            if lugar_sel:
                datos_prov = datos_activos[datos_activos["provincia"] == lugar_sel]
                mostrar_graficos_resumen(datos_prov, "provincia")
        else:
            st.warning("No se encontró columna de Provincia.")
    else:
        st.info("Carga un archivo.")

with tab_vehiculo:
    if df is not None:
        st.subheader("Vista Detallada del Vehículo")
        
        # Selector de vehículo
        datos_base = datos_activos
        
        if "vehiculo" in datos_base.columns:
            vehiculos = sorted(datos_base["vehiculo"].astype(str).unique())
            vehiculo_sel = st.selectbox("Selecciona Vehículo:", vehiculos, index=None, placeholder="Matrícula...")
            
            if vehiculo_sel:
                datos_vehiculo = datos_base[datos_base["vehiculo"].astype(str) == str(vehiculo_sel)]
                
                # Gráficos mensuales, semanales y anuales
                periodo = st.radio("Agrupación temporal:", ["Mensual", "Semanal", "Anual"], horizontal=True)
                if periodo == "Mensual":
                    codigo_periodo = "M"
                elif periodo == "Semanal":
                     codigo_periodo = "W"
                else: 
                     codigo_periodo = "Y"
                
                c1, c2 = st.columns(2)
                with c1:
                     if "repostado" in datos_vehiculo.columns:
                         f1 = grafico_barras_temporal(datos_vehiculo, "fecha", "repostado", codigo_periodo, f"Repostado ({periodo})")
                         if f1: st.plotly_chart(f1, use_container_width=True, key="v_rep")
                with c2:
                    if "distancia" in datos_vehiculo.columns:
                         f2 = grafico_barras_temporal(datos_vehiculo, "fecha", "distancia", codigo_periodo, f"Recorrido ({periodo})")
                         if f2: st.plotly_chart(f2, use_container_width=True, key="v_dist")
                         
                st.divider()
                
                # Gráfico Consumo
                st.subheader("Tendencia de Consumo")
                if "consumo" in datos_vehiculo.columns or ("repostado" in datos_vehiculo.columns and "distancia" in datos_vehiculo.columns):
                    columna_consumo = "consumo"
                    if "consumo" not in datos_vehiculo.columns and "repostado" in datos_vehiculo.columns:
                        st.warning("No se encontró columna 'consumo'. Se muestra evolución de 'repostado'.")
                        columna_consumo = "repostado"

                    tendencia = grafico_lineal_consumo(datos_vehiculo, "fecha", columna_consumo)
                    if tendencia: st.plotly_chart(tendencia, use_container_width=True, key="v_trend")
                
                st.divider()
                st.subheader("Comparativa con Modelo")
                metricas = [c for c in ["repostado", "distancia", "consumo"] if c in datos_activos.columns]
                if metricas:
                    metrica_comp = st.selectbox("Métrica a comparar:", metricas)
                    f_comp = grafico_comparativo_modelo(datos_activos, vehiculo_sel, "fecha", metrica_comp, "tipo_vehiculo")
                    if f_comp: st.plotly_chart(f_comp, use_container_width=True, key="v_comp")
                    else: st.info("No se pudo generar la comparativa (faltan datos del modelo).")
                
                # Mapa
                st.divider()
                st.subheader("Mapa de Repostajes")
                if "latitud" in datos_vehiculo.columns:
                     f_map = mapa_repostajes(datos_vehiculo, vehiculo_sel)
                     if f_map: st.plotly_chart(f_map, use_container_width=True, key="v_map")
                
            else:
                st.info("Selecciona un vehículo.")
        else:
            st.warning("No se encontró la columna 'vehiculo'.")