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

        # Estandarizar columna 'provincia'
        if "provincia" not in df.columns:
            if "direccion" in df.columns:
                # Intentar extraer provincia de dirección (formato 'Pais, Ciudad, ...')
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

# FILTROS LATERALES
# @st.fragment eliminado para evitar conflictos de estado/rerun con la persistencia de filtros
def mostrar_filtros_laterales(df):
    st.header("Filtros")

    # Inicializar opciones vacías
    # Inicializar variables de selección desde session_state
    
    sel_vehiculos = st.session_state.get("filter_vehiculo", [])
    sel_combustibles = st.session_state.get("filter_combustible", [])
    sel_provincias = st.session_state.get("filter_provincia", [])

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
        # Calcular opciones validas según el filtrado cruzado
        valid_veh = obtener_opciones_validas(df, "tipo_vehiculo", {
            "tipo_combustible": sel_combustibles,
            "provincia": sel_provincias
        })
        
        valid_comb = obtener_opciones_validas(df, "tipo_combustible", {
            "tipo_vehiculo": sel_vehiculos,
            "provincia": sel_provincias
        })
        
        valid_prov = obtener_opciones_validas(df, "provincia", {
            "tipo_vehiculo": sel_vehiculos,
            "tipo_combustible": sel_combustibles
        })
        
        # IMPORTANTE: Asegurar que las opciones seleccionadas actualmente sigan existiendo en las opciones
        # para evitar que streamlit las borre automáticamente.
        opciones_tipo_vehiculo = sorted(list(set(valid_veh) | set(sel_vehiculos)))
        opciones_tipo_combustible = sorted(list(set(valid_comb) | set(sel_combustibles)))
        opciones_provincia = sorted(list(set(valid_prov) | set(sel_provincias)))

    else:
        opciones_tipo_vehiculo, opciones_tipo_combustible, opciones_provincia = [], [], []

    # Renderizar los widgets con las opciones completas
    tipos_vehiculo = st.multiselect("Tipo de vehículo", options=opciones_tipo_vehiculo, key="filter_vehiculo")
    tipos_combustible = st.multiselect("Tipo de combustible", options=opciones_tipo_combustible, key="filter_combustible")
    provincia = st.multiselect("Provincia", options=opciones_provincia, key="filter_provincia")

    parametro = None # Ya no usamos un solo parámetro

    # Detectar columnas numéricas relevantes para rangos
    # Podríamos hacerlo dinámico o fijo según requisitos. Haremos fijo a las 3 principales.
    metricas_rango = ["repostado", "distancia", "consumo"]
    rangos_activos = {}

    st.subheader("Rangos")
    for metrica in metricas_rango:
        if df is not None and metrica in df.columns:
            # Calcular min/max
            # Asegurar numérico primero por si acaso
            col_data = pd.to_numeric(df[metrica], errors='coerce').dropna()
            
            if not col_data.empty:
                min_val = float(col_data.min())
                max_val = float(col_data.max())
                
                # Crear slider si hay variabilidad, o mostrar solo info
                if min_val < max_val:
                    # Usar key única por métrica
                    rango_sel = st.slider(f"Rango {metrica.capitalize()}", min_val, max_val, (min_val, max_val), key=f"slider_{metrica}")
                    rangos_activos[metrica] = rango_sel
                else:
                    st.info(f"{metrica.capitalize()}: {min_val}")
    
    rango_fechas = st.date_input("Rango de fechas", [])

    aplicar = st.button("Aplicar filtros")

    if aplicar:
        # Ya no guardamos parámetro único en session state de esta forma
        # st.session_state.parametro_actual = parametro

        #Aplicamos los filtros de la columna de la izquierda.
        if df is not None:
            df_filtrado = aplicar_filtros(
                df,
                tipos_vehiculo = tipos_vehiculo,
                tipos_combustible = tipos_combustible,
                lugar = provincia, # Pasamos provincia como 'lugar'
                rangos = rangos_activos,
                fechas = rango_fechas
                )
            st.session_state.df_filtrado = df_filtrado
            st.rerun()

# Llamada a la función de fragmento
with st.sidebar:
    mostrar_filtros_laterales(df)

# Recuperamos variables clave del estado para el resto de la app
# parametro_actual ya no es crítico para el filtrado, pero tal vez para gráficos.
# Dejaremos un default para compatibilidad si algo lo usa.
if "parametro_actual" not in st.session_state:
    st.session_state.parametro_actual = "repostado" 

parametro = st.session_state.parametro_actual


df_filtrado = st.session_state.df_filtrado  # Recuperamos el dataframe persistente

# Definimos el dataframe activo para todas las pestañas (filtrado o total)
df_activo = df_filtrado if df_filtrado is not None else df

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
        if col_anio in df_local.columns:
            fig_anio = grafico_tarta_distribucion(df_local, col_anio, "Distribución por Año")
            if fig_anio: st.plotly_chart(fig_anio, use_container_width=True, key=f"pie_anio_{clave_sufijo}")

with tab_general:
    if df_activo is not None:
        st.subheader("Vista General de toda la Flota (Filtrada)")
        mostrar_graficos_resumen(df_activo, "general")
    else:
        st.info("Carga un archivo para ver los datos.")

with tab_provincia:
    if df_activo is not None:
        st.subheader("Vista por Provincia")
        
        # Como ya garantizamos la columna 'provincia' en la carga, usamos esa directamente.
        if "provincia" in df_activo.columns:
            lugares = sorted(df_activo["provincia"].astype(str).unique())
            lugar_sel = st.selectbox("Selecciona Provincia:", lugares, index=0)
            
            if lugar_sel:
                df_prov = df_activo[df_activo["provincia"] == lugar_sel]
                mostrar_graficos_resumen(df_prov, "provincia")
        else:
             # Fallback por seguridad si algo falla en la carga
            st.warning("No se encontró columna de Provincia.")
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
