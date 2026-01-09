import streamlit as st
import pandas as pd

if "df_filtrado" not in st.session_state:
    st.session_state.df_filtrado = None

#Funciones externas
from modulos.filtros import aplicar_filtros
from modulos.graficos import (
    Grafico_lineal_parametros, mapa_repostajes, grafico_general_repostajes, grafico_top_vehiculos,
    grafico_barras_temporal, grafico_tarta_distribucion, grafico_dia_semana, grafico_lineal_consumo,
    grafico_comparativo_modelo
)
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
# CREACIÓN DE PESTAÑAS
tab_general, tab_provincia, tab_vehiculo = st.tabs(["Vista General (Flota)", "Vista por Provincia", "Detalle Vehículo"])

def mostrar_graficos_resumen(df_local, clave_sufijo=""):
    """
    Helper para mostrar los gráficos repetidos en General y Provincia.
    """
    if df_local is None or df_local.empty:
        st.info("No hay datos para mostrar.")
        return

    # 1. Gráficos Temporales (Repostado y Recorrido)
    col1, col2 = st.columns(2)
    with col1:
        if "repostado" in df_local.columns and "fecha" in df_local.columns:
            fig_rep = grafico_barras_temporal(df_local, "fecha", "repostado", "M", "Repostado Mensual")
            if fig_rep: st.plotly_chart(fig_rep, use_container_width=True, key=f"bar_rep_{clave_sufijo}")
    
    with col2:
        if "distancia" in df_local.columns and "fecha" in df_local.columns:
            fig_dist = grafico_barras_temporal(df_local, "fecha", "distancia", "M", "Recorrido Mensual (km)")
            if fig_dist: st.plotly_chart(fig_dist, use_container_width=True, key=f"bar_dist_{clave_sufijo}")
            
    st.divider()
    
    # 2. Tipos de Combustible y Día de Semana
    col3, col4 = st.columns(2)
    with col3:
        if "tipo_combustible" in df_local.columns:
            fig_comb = grafico_tarta_distribucion(df_local, "tipo_combustible", "Tipos de Combustible")
            if fig_comb: st.plotly_chart(fig_comb, use_container_width=True, key=f"pie_comb_{clave_sufijo}")
            
    with col4:
        if "fecha" in df_local.columns:
            fig_sem = grafico_dia_semana(df_local, "fecha")
            if fig_sem: st.plotly_chart(fig_sem, use_container_width=True, key=f"pie_sem_{clave_sufijo}")

    st.divider()

    # 3. Etiqueta o Año Matriculación
    col5, col6 = st.columns(2)
    hay_etiqueta = "etiqueta" in df_local.columns
    hay_anio = "año_matriculacion" in df_local.columns or "anio_matriculacion" in df_local.columns
    
    # Normalizar nombre año
    col_anio = "año_matriculacion" if "año_matriculacion" in df_local.columns else "anio_matriculacion"

    with col5:
        if hay_etiqueta:
            fig_eti = grafico_tarta_distribucion(df_local, "etiqueta", "Distribución por Etiqueta")
            if fig_eti: st.plotly_chart(fig_eti, use_container_width=True, key=f"pie_eti_{clave_sufijo}")
    
    with col6:
        if hay_anio in df_local.columns: # Corrección de lógica
            pass
        if col_anio in df_local.columns:
            fig_anio = grafico_tarta_distribucion(df_local, col_anio, "Distribución por Año")
            if fig_anio: st.plotly_chart(fig_anio, use_container_width=True, key=f"pie_anio_{clave_sufijo}")

with tab_general:
    if df is not None:
        st.subheader("Vista General de toda la Flota")
        mostrar_graficos_resumen(df, "general")
    else:
        st.info("Carga un archivo para ver los datos.")

with tab_provincia:
    if df is not None:
        st.subheader("Vista por Provincia")
        
        # Selector de provincia (usamos 'direccion' o 'provincia')
        col_lugar = "provincia" if "provincia" in df.columns else "direccion"
        
        # Lógica para extraer provincia limpia si usamos dirección
        # Se asume formato "Pais, Ciudad, Calle..." -> Extraer índice 1
        if col_lugar == "direccion":
            def extraer_ciudad(dir_str):
                parts = str(dir_str).split(',')
                # Si hay comas, tomamos el segundo elemento (índice 1) asumiendo "País, Ciudad, ..."
                if len(parts) > 1:
                    return parts[1].strip()
                return str(dir_str).strip()
            
            # Usamos una columna temporal para el selector
            df_temp = df.copy()
            df_temp["_provincia_calc"] = df_temp[col_lugar].apply(extraer_ciudad)
            
            lugares = sorted(df_temp["_provincia_calc"].unique())
            lugar_sel = st.selectbox("Selecciona Provincia / Ciudad:", lugares, index=0)
            
            if lugar_sel:
                # Filtrar usando la columna calculada
                df_prov = df_temp[df_temp["_provincia_calc"] == lugar_sel]
                mostrar_graficos_resumen(df_prov, "provincia")
                
        elif col_lugar in df.columns:
            lugares = sorted(df[col_lugar].astype(str).unique())
            lugar_sel = st.selectbox("Selecciona Provincia:", lugares, index=0)
            
            if lugar_sel:
                df_prov = df[df[col_lugar] == lugar_sel]
                mostrar_graficos_resumen(df_prov, "provincia")
        else:
            st.warning("No se encontró columna de Provincia o Dirección.")
            # Fallback a usar df_filtrado si el usuario usó filtros laterales
            if df_filtrado is not None:
                st.info("Mostrando datos de filtros laterales:")
                mostrar_graficos_resumen(df_filtrado, "prov_filtrado")

    else:
        st.info("Carga un archivo.")

with tab_vehiculo:
    if df is not None:
        st.subheader("Vista Detallada del Vehículo")
        
        # Selector de vehículo
        # Usamos df_filtrado si existe para reducir lista, si no df completo
        base_df = df_filtrado if df_filtrado is not None else df
        
        if "vehiculo" in base_df.columns:
            vehiculos = sorted(base_df["vehiculo"].astype(str).unique())
            vehiculo_sel = st.selectbox("Selecciona Vehículo:", vehiculos, index=None, placeholder="Matrícula...")
            
            if vehiculo_sel:
                df_v = df[df["vehiculo"].astype(str) == str(vehiculo_sel)]
                
                # Gráficos mensuales/semanales
                periodo = st.radio("Agrupación temporal:", ["Mensual", "Semanal"], horizontal=True)
                per_code = "M" if periodo == "Mensual" else "W"
                
                c1, c2 = st.columns(2)
                with c1:
                     if "repostado" in df_v.columns:
                         f1 = grafico_barras_temporal(df_v, "fecha", "repostado", per_code, f"Repostado ({periodo})")
                         if f1: st.plotly_chart(f1, use_container_width=True, key="v_rep")
                with c2:
                    if "distancia" in df_v.columns:
                         f2 = grafico_barras_temporal(df_v, "fecha", "distancia", per_code, f"Recorrido ({periodo})")
                         if f2: st.plotly_chart(f2, use_container_width=True, key="v_dist")
                         
                st.divider()
                
                # Gráfico Consumo (más o menos)
                st.subheader("Tendencia de Consumo")
                if "consumo" in df_v.columns or ("repostado" in df_v.columns and "distancia" in df_v.columns):
                    # Si no hay consumo, calculamos al vuelo para el gráfico? 
                    # grafico_lineal_consumo ya requiere columna.
                    # Vamos a intentar asegurar que 'consumo' exista o se puede pasar 'repostado' como proxy si no
                    col_con = "consumo"
                    if "consumo" not in df_v.columns and "repostado" in df_v.columns: 
                        # Si no hay consumo explicitamente, usamos repostado como metrica de gasto?? 
                        # El usuario dijo "si el consumo va a más o menos".
                        # Si no existe, avisamos.
                        if "consumo" not in df_v.columns:
                            st.warning("No se encontró columna 'consumo'. Se muestra evolución de 'repostado'.")
                            col_con = "repostado"

                    f_trend = grafico_lineal_consumo(df_v, "fecha", col_con)
                    if f_trend: st.plotly_chart(f_trend, use_container_width=True, key="v_trend")
                
                st.divider()
                st.subheader("Comparativa con Modelo")
                # Gráfico comparativo
                # Todos los vehículos del mismo modelo en tono claro
                metrics = [c for c in ["repostado", "distancia", "consumo"] if c in df.columns]
                if metrics:
                    metrica_comp = st.selectbox("Métrica a comparar:", metrics)
                    f_comp = grafico_comparativo_modelo(df, vehiculo_sel, "fecha", metrica_comp, "tipo_vehiculo")
                    # Nota: asumo 'tipo_vehiculo' como modelo, si hay columna 'modelo' mejor.
                    if f_comp: st.plotly_chart(f_comp, use_container_width=True, key="v_comp")
                    else: st.info("No se pudo generar la comparativa (faltan datos del modelo).")
                
                # Mapa
                st.divider()
                st.subheader("Mapa de Repostajes")
                if "latitud" in df_v.columns:
                     f_map = mapa_repostajes(df_v, vehiculo_sel)
                     if f_map: st.pydeck_chart(f_map)
                
            else:
                st.info("Selecciona un vehículo.")
        else:
            st.warning("No se encontró columna 'vehiculo'.")
