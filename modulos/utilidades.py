import streamlit as st
import random

def set_animated_background():

    fondo_css = """
    <style>
    /* Animación de gradiente */
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    
    /* Aplicar al contenedor principal de Streamlit */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    </style>
    """
    st.markdown(fondo_css, unsafe_allow_html=True)

@st.cache_data
def get_star_css():

    def generar_sombras(cantidad):
        return ", ".join([f"{random.randint(0, 2000)}px {random.randint(0, 2000)}px #FFF" for _ in range(cantidad)])

    estrellas_pequenas = generar_sombras(700)
    estrellas_medianas = generar_sombras(200)
    estrellas_grandes = generar_sombras(100)

    return f"""
    <style>
    /* Fondo general - Forzamos el color de fondo */
    .stApp {{
        background: radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%) !important;
    }}

    /* Contenedor fijo para las estrellas */
    .star-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 0;
        pointer-events: none;
    }}
    
    /* Ajustamos el z-index del contenido principal */
    .main .block-container {{
        z-index: 1;
        position: relative;
    }}

    /* Estrellas pequeñas */
    #stars {{
        width: 1px;
        height: 1px;
        background: transparent;
        box-shadow: {estrellas_pequenas};
        animation: animStar 200s linear infinite;
    }}
    #stars:after {{
        content: " ";
        position: absolute;
        top: 2000px;
        width: 1px;
        height: 1px;
        background: transparent;
        box-shadow: {estrellas_pequenas};
    }}

    /* Estrellas medianas */
    #stars2 {{
        width: 2px;
        height: 2px;
        background: transparent;
        box-shadow: {estrellas_medianas};
        animation: animStar 300s linear infinite;
    }}
    #stars2:after {{
        content: " ";
        position: absolute;
        top: 2000px;
        width: 2px;
        height: 2px;
        background: transparent;
        box-shadow: {estrellas_medianas};
    }}

    /* Estrellas grandes */
    #stars3 {{
        width: 3px;
        height: 3px;
        background: transparent;
        box-shadow: {estrellas_grandes};
        animation: animStar 400s linear infinite;
    }}
    #stars3:after {{
        content: " ";
        position: absolute;
        top: 2000px;
        width: 3px;
        height: 3px;
        background: transparent;
        box-shadow: {estrellas_grandes};
    }}

    @keyframes animStar {{
        from {{ transform: translateY(0px); }}
        to {{ transform: translateY(-2000px); }}
    }}
    </style>
    
    <div class="star-container">
        <div id="stars"></div>
        <div id="stars2"></div>
        <div id="stars3"></div>
    </div>
    """

def set_star_background():

    css = get_star_css()
    st.markdown(css, unsafe_allow_html=True)
