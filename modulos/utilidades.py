import streamlit as st
import random

def set_animated_background():
    """
    Injects CSS to create an animated gradient background for the Streamlit app.
    """
    page_bg_img = """
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
    st.markdown(page_bg_img, unsafe_allow_html=True)

@st.cache_data
def get_star_css():
    """
    Generates the CSS for the star background. Cached to prevent regeneration on every rerun.
    """
    def get_shadows(n):
        return ", ".join([f"{random.randint(0, 2000)}px {random.randint(0, 2000)}px #FFF" for _ in range(n)])

    shadows_small = get_shadows(700)
    shadows_medium = get_shadows(200)
    shadows_big = get_shadows(100)

    # Tiempos de animación mucho más lentos (200s, 300s, 400s)
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
        z-index: 0; /* Cambiado de -1 a 0 para asegurar visibilidad, pero cuidado con tapar contenido */
        pointer-events: none;
    }}
    
    /* Ajustamos el z-index del contenido principal de Streamlit para que esté por encima */
    .main .block-container {{
        z-index: 1;
        position: relative;
    }}

    #stars {{
        width: 1px;
        height: 1px;
        background: transparent;
        box-shadow: {shadows_small};
        animation: animStar 200s linear infinite;
    }}
    #stars:after {{
        content: " ";
        position: absolute;
        top: 2000px;
        width: 1px;
        height: 1px;
        background: transparent;
        box-shadow: {shadows_small};
    }}

    #stars2 {{
        width: 2px;
        height: 2px;
        background: transparent;
        box-shadow: {shadows_medium};
        animation: animStar 300s linear infinite;
    }}
    #stars2:after {{
        content: " ";
        position: absolute;
        top: 2000px;
        width: 2px;
        height: 2px;
        background: transparent;
        box-shadow: {shadows_medium};
    }}

    #stars3 {{
        width: 3px;
        height: 3px;
        background: transparent;
        box-shadow: {shadows_big};
        animation: animStar 400s linear infinite;
    }}
    #stars3:after {{
        content: " ";
        position: absolute;
        top: 2000px;
        width: 3px;
        height: 3px;
        background: transparent;
        box-shadow: {shadows_big};
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
    """
    Injects the cached CSS for the star background.
    """
    css = get_star_css()
    st.markdown(css, unsafe_allow_html=True)
