import streamlit as st

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
