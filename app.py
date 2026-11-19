import streamlit as st
from streamlit_autorefresh import st_autorefresh
from PIL import Image
import io

# Configuración inicial de la página (debe ir primero)
st.set_page_config(
    page_title="Marcador de Competencia",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estado global compartido entre sesiones (Proyector <-> Controlador)
@st.cache_resource
def get_match_state():
    return {
        "titulo": "GRAN FINAL - COMPETENCIA",
        "eq1_nombre": "EQUIPO ALFA",
        "eq1_puntos": 0,
        "eq1_img": None,
        "eq2_nombre": "EQUIPO OMEGA",
        "eq2_puntos": 0,
        "eq2_img": None,
    }

state = get_match_state()

# Detectar si se accedió con ?admin=true en la URL
query_params = st.query_params
is_admin = query_params.get("admin", "false").lower() == "true"

# ==============================================================================
# MODO 1: PANEL DE CONTROL (Solo visible en ?admin=true)
# ==============================================================================
if is_admin:
    st.title("🎛️ Panel de Control del Marcador")
    st.info("💡 **Tip:** Abre la URL principal (sin `?admin=true`) en la pantalla del proyector. Los cambios aquí se reflejarán automáticamente allá.")

    # Título del evento
    state["titulo"] = st.text_input("Título del Evento / Ronda", value=state["titulo"])
    st.divider()

    col_ctrl1, col_ctrl2 = st.columns(2)

    # --- Controles Equipo 1 ---
    with col_ctrl1:
        st.subheader("🔵 Configuración Equipo 1")
        state["eq1_nombre"] = st.text_input("Nombre Equipo 1", value=state["eq1_nombre"], key="in_n1")
        
        img1 = st.file_uploader("Logo/Imagen Equipo 1", type=["png", "jpg", "jpeg", "webp"], key="up_1")
        if img1 is not None:
            state["eq1_img"] = img1.getvalue()
        if state["eq1_img"] is not None:
            if st.button("Quitar imagen Eq. 1"):
                state["eq1_img"] = None
                st.rerun()

        st.markdown(f"### Puntaje actual: **{state['eq1_puntos']}**")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("➕ 1", key="e1_p1", use_container_width=True):
            state["eq1_puntos"] += 1
            st.rerun()
        if b2.button("➕ 5", key="e1_p5", use_container_width=True):
            state["eq1_puntos"] += 5
            st.rerun()
        if b3.button("➕ 10", key="e1_p10", use_container_width=True):
            state["eq1_puntos"] += 10
            st.rerun()
        if b4.button("➖ 1", key="e1_m1", use_container_width=True):
            state["eq1_puntos"] = max(0, state["eq1_puntos"] - 1)
            st.rerun()

        # Edición manual directa por si se necesita corregir rápido
        nuevo_p1 = st.number_input("Ajuste manual Eq. 1", value=state["eq1_puntos"], step=1, key="man_1")
        if nuevo_p1 != state["eq1_puntos"]:
            state["eq1_puntos"] = nuevo_p1
            st.rerun()

    # --- Controles Equipo 2 ---
    with col_ctrl2:
        st.subheader("🔴 Configuración Equipo 2")
        state["eq2_nombre"] = st.text_input("Nombre Equipo 2", value=state["eq2_nombre"], key="in_n2")
        
        img2 = st.file_uploader("Logo/Imagen Equipo 2", type=["png", "jpg", "jpeg", "webp"], key="up_2")
        if img2 is not None:
            state["eq2_img"] = img2.getvalue()
        if state["eq2_img"] is not None:
            if st.button("Quitar imagen Eq. 2"):
                state["eq2_img"] = None
                st.rerun()

        st.markdown(f"### Puntaje actual: **{state['eq2_puntos']}**")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("➕ 1", key="e2_p1", use_container_width=True):
            state["eq2_puntos"] += 1
            st.rerun()
        if c2.button("➕ 5", key="e2_p5", use_container_width=True):
            state["eq2_puntos"] += 5
            st.rerun()
        if c3.button("➕ 10", key="e2_p10", use_container_width=True):
            state["eq2_puntos"] += 10
            st.rerun()
        if c4.button("➖ 1", key="e2_m1", use_container_width=True):
            state["eq2_puntos"] = max(0, state["eq2_puntos"] - 1)
            st.rerun()

        nuevo_p2 = st.number_input("Ajuste manual Eq. 2", value=state["eq2_puntos"], step=1, key="man_2")
        if nuevo_p2 != state["eq2_puntos"]:
            state["eq2_puntos"] = nuevo_p2
            st.rerun()

    st.divider()
    if st.button("🔄 Reiniciar Marcador a 0 - 0", type="primary"):
        state["eq1_puntos"] = 0
        state["eq2_puntos"] = 0
        st.rerun()

# ==============================================================================
# MODO 2: VISTA DE PROYECTOR (Limpia, sin controles, auto-actualizable)
# ==============================================================================
else:
    # Refresca la pantalla del proyector cada 2000 ms (2 segundos) para leer cambios
    st_autorefresh(interval=2000, key="projector_refresh")

    # CSS para ocultar elementos de Streamlit (menú, footer, header) y dar estilo proyector
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            
            /* Fondo oscuro elegante */
            .stApp {
                background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
                color: #f8fafc;
            }
            
            /* Título superior */
            .event-title {
                text-align: center;
                font-size: 2.8rem;
                font-weight: 800;
                letter-spacing: 3px;
                text-transform: uppercase;
                color: #38bdf8;
                margin-bottom: 1.5rem;
                text-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
            }

            /* Tarjetas de equipo */
            .team-card-1 {
                background: rgba(30, 58, 138, 0.35);
                border: 3px solid #3b82f6;
                border-radius: 24px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(59, 130, 246, 0.25);
            }
            .team-card-2 {
                background: rgba(153, 27, 27, 0.35);
                border: 3px solid #ef4444;
                border-radius: 24px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(239, 68, 68, 0.25);
            }

            .team-name {
                font-size: 2.6rem;
                font-weight: 800;
                margin-top: 15px;
                margin-bottom: 5px;
                text-transform: uppercase;
                color: #ffffff;
            }

            .score-box {
                font-size: 8.5rem;
                font-weight: 900;
                line-height: 1.05;
                margin: 10px 0;
                font-family: 'Arial Black', sans-serif;
                color: #facc15;
                text-shadow: 0 6px 20px rgba(250, 204, 21, 0.4);
            }

            .vs-text {
                text-align: center;
                font-size: 4rem;
                font-weight: 900;
                color: #94a3b8;
                margin-top: 180px;
            }
        </style>
    """, unsafe_allow_html=True)

    # Título del evento
    st.markdown(f'<div class="event-title">{state["titulo"]}</div>', unsafe_allow_html=True)

    col1, col_vs, col2 = st.columns([5, 1.2, 5])

    # Renderizar Equipo 1
    with col1:
        st.markdown('<div class="team-card-1">', unsafe_allow_html=True)
        if state["eq1_img"] is not None:
            image1 = Image.open(io.BytesIO(state["eq1_img"]))
            # Centrar imagen usando columnas internas
            _, img_col1, _ = st.columns([1, 2, 1])
            with img_col1:
                st.image(image1, use_container_width=True)
        else:
            st.markdown("<div style='font-size: 6rem; padding: 20px;'>🛡️</div>", unsafe_allow_html=True)
        
        st.markdown(f'<div class="team-name">{state["eq1_nombre"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-box">{state["eq1_puntos"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Separador VS
    with col_vs:
        st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)

    # Renderizar Equipo 2
    with col2:
        st.markdown('<div class="team-card-2">', unsafe_allow_html=True)
        if state["eq2_img"] is not None:
            image2 = Image.open(io.BytesIO(state["eq2_img"]))
            _, img_col2, _ = st.columns([1, 2, 1])
            with img_col2:
                st.image(image2, use_container_width=True)
        else:
            st.markdown("<div style='font-size: 6rem; padding: 20px;'>⚔️</div>", unsafe_allow_html=True)

        st.markdown(f'<div class="team-name">{state["eq2_nombre"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-box">{state["eq2_puntos"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)