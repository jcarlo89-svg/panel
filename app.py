import streamlit as st
from streamlit_autorefresh import st_autorefresh
from PIL import Image
import io
import json
import os
import base64
import uuid
import math

DATA_FILE = "scoreboard_data.json"

st.set_page_config(
    page_title="Marcador y Presentación de Grupos",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def _img_to_b64(img_bytes):
    if not img_bytes:
        return None
    return base64.b64encode(img_bytes).decode("utf-8")

def _b64_to_img(b64_str):
    if not b64_str:
        return None
    return base64.b64decode(b64_str.encode("utf-8"))

def _default_state():
    return {
        "titulo": "GRAN FINAL - COMPETENCIA",
        "evento_img_b64": None,
        "grupos": {},
        "activo_izq": None,
        "activo_der": None,
        "ganador_id": None,
        "version": 1
    }

def _load_from_disk():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "grupos" in data:
                data.setdefault("titulo", "GRAN FINAL - COMPETENCIA")
                data.setdefault("evento_img_b64", None)
                data.setdefault("activo_izq", None)
                data.setdefault("activo_der", None)
                data.setdefault("ganador_id", None)
                data.setdefault("version", 1)
                return data
        except Exception:
            pass
    return _default_state()

def _save_to_disk(state):
    state["version"] = state.get("version", 0) + 1
    tmp_file = f"{DATA_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp_file, DATA_FILE)

@st.cache_resource
def get_store():
    return _load_from_disk()

store = get_store()

def render_event_header(store_data, is_admin_view=False):
    raw_logo = _b64_to_img(store_data.get("evento_img_b64"))
    if is_admin_view:
        c_logo, c_title = st.columns([1.2, 6.8])
        with c_logo:
            if raw_logo:
                st.image(Image.open(io.BytesIO(raw_logo)), use_container_width=True)
            else:
                st.markdown("<div style='font-size: 3rem; text-align: center;'>🏆</div>", unsafe_allow_html=True)
        with c_title:
            st.markdown(f"<h2 style='margin: 0; padding-top: 8px;'>{store_data['titulo']}</h2>", unsafe_allow_html=True)
    else:
        if raw_logo:
            _, mid_col, _ = st.columns([4.2, 1.6, 4.2])
            with mid_col:
                st.markdown('<div class="event-logo-box">', unsafe_allow_html=True)
                st.image(Image.open(io.BytesIO(raw_logo)), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="event-title">{store_data["titulo"]}</div>', unsafe_allow_html=True)

def resolve_winner(store_data):
    grupos = store_data.get("grupos", {})
    if not grupos:
        return None
    chosen_id = store_data.get("ganador_id")
    if chosen_id and chosen_id in grupos:
        return grupos[chosen_id]
    # Si no se eligió uno manualmente, toma el grupo con mayor puntaje
    best_id = max(grupos.keys(), key=lambda k: grupos[k].get("puntos", 0))
    return grupos[best_id]

def render_celebration_overlay():
    st.markdown("""
        <style>
            .celebration-layer {
                position: fixed;
                inset: 0;
                pointer-events: none;
                overflow: hidden;
                z-index: 9999;
            }
            .balloon {
                position: absolute;
                bottom: -140px;
                width: 54px;
                height: 68px;
                border-radius: 50% 50% 45% 45%;
                opacity: 0.9;
                animation: floatUp var(--dur, 7s) linear infinite;
                animation-delay: var(--delay, 0s);
                left: var(--left, 50%);
                background: var(--color, #facc15);
                box-shadow: inset -8px -10px 16px rgba(0,0,0,0.22), 0 8px 18px rgba(0,0,0,0.25);
            }
            .balloon::after {
                content: "";
                position: absolute;
                bottom: -26px;
                left: 50%;
                width: 2px;
                height: 28px;
                background: rgba(255,255,255,0.55);
                transform: translateX(-50%);
            }
            @keyframes floatUp {
                0% {
                    transform: translateY(0) translateX(0) rotate(-4deg);
                    opacity: 0;
                }
                10% { opacity: 0.92; }
                50% {
                    transform: translateY(-55vh) translateX(18px) rotate(5deg);
                }
                90% { opacity: 0.9; }
                100% {
                    transform: translateY(-115vh) translateX(-14px) rotate(-3deg);
                    opacity: 0;
                }
            }
            .rocket {
                position: absolute;
                bottom: -90px;
                left: var(--left, 20%);
                font-size: 2.3rem;
                animation: launchRocket var(--dur, 4.5s) ease-out infinite;
                animation-delay: var(--delay, 0s);
                filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.8));
            }
            @keyframes launchRocket {
                0% {
                    transform: translateY(0) scale(0.9);
                    opacity: 0;
                }
                15% { opacity: 1; }
                70% {
                    transform: translateY(-68vh) scale(1.1);
                    opacity: 1;
                }
                85% {
                    transform: translateY(-76vh) scale(1.5);
                    opacity: 0.8;
                }
                100% {
                    transform: translateY(-82vh) scale(0.2);
                    opacity: 0;
                }
            }
            .burst {
                position: absolute;
                top: var(--top, 28%);
                left: var(--left, 50%);
                width: 14px;
                height: 14px;
                border-radius: 50%;
                animation: fireworkBurst var(--dur, 3.2s) ease-out infinite;
                animation-delay: var(--delay, 0s);
                box-shadow:
                    0 -55px 0 var(--c1, #facc15),
                    39px -39px 0 var(--c2, #38bdf8),
                    55px 0 0 var(--c3, #f472b6),
                    39px 39px 0 var(--c4, #4ade80),
                    0 55px 0 var(--c1, #facc15),
                    -39px 39px 0 var(--c2, #38bdf8),
                    -55px 0 0 var(--c3, #f472b6),
                    -39px -39px 0 var(--c4, #4ade80);
            }
            @keyframes fireworkBurst {
                0% {
                    transform: scale(0.15);
                    opacity: 0;
                }
                25% {
                    opacity: 1;
                }
                85% {
                    transform: scale(1.35);
                    opacity: 0.9;
                }
                100% {
                    transform: scale(1.65);
                    opacity: 0;
                }
            }
            .confetti {
                position: absolute;
                top: -20px;
                left: var(--left, 50%);
                width: 10px;
                height: 18px;
                background: var(--color, #facc15);
                animation: confettiFall var(--dur, 4.8s) linear infinite;
                animation-delay: var(--delay, 0s);
            }
            @keyframes confettiFall {
                0% {
                    transform: translateY(0) rotate(0deg);
                    opacity: 1;
                }
                100% {
                    transform: translateY(105vh) rotate(540deg);
                    opacity: 0.85;
                }
            }
        </style>
        <div class="celebration-layer">
            <div class="balloon" style="--left: 6%; --dur: 7.2s; --delay: 0s; --color: #ef4444;"></div>
            <div class="balloon" style="--left: 14%; --dur: 8.4s; --delay: 1.5s; --color: #3b82f6;"></div>
            <div class="balloon" style="--left: 23%; --dur: 6.8s; --delay: 0.7s; --color: #facc15;"></div>
            <div class="balloon" style="--left: 78%; --dur: 7.8s; --delay: 1.1s; --color: #22c55e;"></div>
            <div class="balloon" style="--left: 86%; --dur: 6.6s; --delay: 2.2s; --color: #ec4899;"></div>
            <div class="balloon" style="--left: 93%; --dur: 8.1s; --delay: 0.4s; --color: #38bdf8;"></div>

            <div class="rocket" style="--left: 12%; --dur: 4.2s; --delay: 0.2s;">🚀</div>
            <div class="rocket" style="--left: 88%; --dur: 4.8s; --delay: 1.4s;">🚀</div>

            <div class="burst" style="--top: 22%; --left: 20%; --dur: 3.0s; --delay: 0.4s; --c1: #facc15; --c2: #ef4444; --c3: #38bdf8; --c4: #4ade80;"></div>
            <div class="burst" style="--top: 26%; --left: 80%; --dur: 3.4s; --delay: 1.2s; --c1: #f472b6; --c2: #facc15; --c3: #a855f7; --c4: #38bdf8;"></div>
            <div class="burst" style="--top: 18%; --left: 50%; --dur: 3.6s; --delay: 2.0s; --c1: #4ade80; --c2: #facc15; --c3: #fb7185; --c4: #60a5fa;"></div>

            <div class="confetti" style="--left: 18%; --dur: 4.5s; --delay: 0s; --color: #facc15;"></div>
            <div class="confetti" style="--left: 32%; --dur: 5.2s; --delay: 0.8s; --color: #38bdf8;"></div>
            <div class="confetti" style="--left: 45%; --dur: 4.1s; --delay: 1.6s; --color: #f472b6;"></div>
            <div class="confetti" style="--left: 62%; --dur: 5.0s; --delay: 0.4s; --color: #4ade80;"></div>
            <div class="confetti" style="--left: 75%; --dur: 4.7s; --delay: 1.9s; --color: #fb923c;"></div>
            <div class="confetti" style="--left: 89%; --dur: 4.3s; --delay: 1.1s; --color: #a855f7;"></div>
        </div>
    """, unsafe_allow_html=True)

query_params = st.query_params
is_admin = query_params.get("admin", "false").lower() == "true"
view_mode = query_params.get("view", "score").lower()

# ==============================================================================
# MODO 1: PANEL DE ADMINISTRACIÓN (?admin=true)
# ==============================================================================
if is_admin:
    st.title("🎛️ Panel de Control y Gestión de Grupos")
    render_event_header(store, is_admin_view=True)
    st.info(
        "Vistas disponibles para el proyector:\n"
        "- **Duelo 1 vs 1:** URL base (sin parámetros)\n"
        "- **Presentación de todos los grupos:** agrega `?view=lineup`\n"
        "- **Equipo ganador con celebración:** agrega `?view=winner`"
    )

    st.subheader("🏁 Configuración del Evento")
    c_t, c_l, c_q = st.columns([3.5, 3, 1.5])
    with c_t:
        nuevo_titulo = st.text_input("Título del Evento / Ronda", value=store["titulo"])
        if nuevo_titulo != store["titulo"]:
            store["titulo"] = nuevo_titulo
            _save_to_disk(store)
            st.rerun()
    with c_l:
        logo_evento = st.file_uploader("Logo del Evento", type=["png", "jpg", "jpeg", "webp"], key="up_evento_logo")
        if logo_evento is not None:
            store["evento_img_b64"] = _img_to_b64(logo_evento.getvalue())
            _save_to_disk(store)
            st.rerun()
    with c_q:
        st.write("")
        st.write("")
        if store.get("evento_img_b64"):
            if st.button("🗑️ Quitar logo", key="btn_quitar_logo_evento", use_container_width=True):
                store["evento_img_b64"] = None
                _save_to_disk(store)
                st.rerun()

    st.divider()

    st.subheader("➕ Crear nuevo grupo")
    with st.form("form_crear_grupo", clear_on_submit=True):
        c_nom, c_pts, c_img = st.columns([3, 1.5, 3])
        with c_nom:
            nombre_nuevo = st.text_input("Nombre del grupo", placeholder="Ej. Los 4 Fastásticos")
        with c_pts:
            puntos_iniciales = st.number_input("Puntaje inicial", min_value=0, value=0, step=1)
        with c_img:
            img_nueva = st.file_uploader("Logo / Imagen", type=["png", "jpg", "jpeg", "webp"])

        submitted = st.form_submit_button("Guardar grupo", type="primary")
        if submitted:
            nombre_limpio = nombre_nuevo.strip()
            if not nombre_limpio:
                st.warning("Escribe un nombre para el grupo.")
            else:
                gid = str(uuid.uuid4())[:8]
                img_bytes = img_nueva.getvalue() if img_nueva is not None else None
                store["grupos"][gid] = {
                    "nombre": nombre_limpio,
                    "puntos": int(puntos_iniciales),
                    "img_b64": _img_to_b64(img_bytes)
                }
                if store["activo_izq"] is None:
                    store["activo_izq"] = gid
                elif store["activo_der"] is None and store["activo_izq"] != gid:
                    store["activo_der"] = gid
                _save_to_disk(store)
                st.success(f"Grupo '{nombre_limpio}' guardado.")
                st.rerun()

    st.divider()

    st.subheader("📺 Seleccionar los 2 grupos en pantalla (Modo Duelo)")
    grupos = store["grupos"]

    if len(grupos) < 2:
        st.warning("Crea al menos **2 grupos** para seleccionar el enfrentamiento en pantalla.")
    else:
        ids_ordenados = list(grupos.keys())
        etiquetas = {gid: f"{grupos[gid]['nombre']} ({grupos[gid]['puntos']} pts)" for gid in ids_ordenados}

        idx_izq = ids_ordenados.index(store["activo_izq"]) if store["activo_izq"] in ids_ordenados else 0
        idx_der = ids_ordenados.index(store["activo_der"]) if store["activo_der"] in ids_ordenados else (1 if len(ids_ordenados) > 1 else 0)

        col_sel1, col_sel2, col_swap = st.columns([4, 4, 2])
        with col_sel1:
            sel_izq = st.selectbox(
                "Grupo Izquierda (Pantalla)",
                options=ids_ordenados,
                index=idx_izq,
                format_func=lambda x: etiquetas[x],
                key="sel_izq_box"
            )
        with col_sel2:
            sel_der = st.selectbox(
                "Grupo Derecha (Pantalla)",
                options=ids_ordenados,
                index=idx_der,
                format_func=lambda x: etiquetas[x],
                key="sel_der_box"
            )
        with col_swap:
            st.write("")
            st.write("")
            if st.button("🔀 Intercambiar lados", use_container_width=True):
                store["activo_izq"], store["activo_der"] = store["activo_der"], store["activo_izq"]
                _save_to_disk(store)
                st.rerun()

        if sel_izq == sel_der:
            st.error("Elige dos grupos distintos para izquierda y derecha.")
        else:
            if sel_izq != store["activo_izq"] or sel_der != store["activo_der"]:
                store["activo_izq"] = sel_izq
                store["activo_der"] = sel_der
                _save_to_disk(store)
                st.rerun()

    st.divider()

    st.subheader("🏆 Equipo Ganador (Modo Celebración ?view=winner)")
    if not grupos:
        st.caption("Crea grupos para elegir o detectar al ganador.")
    else:
        ids_ordenados = list(grupos.keys())
        opciones_ganador = ["auto"] + ids_ordenados
        actual_ganador = store.get("ganador_id") if store.get("ganador_id") in ids_ordenados else "auto"
        idx_gan = opciones_ganador.index(actual_ganador)

        def fmt_gan(opt):
            if opt == "auto":
                best = resolve_winner(store)
                return f"Automático (Mayor puntaje: {best['nombre'] if best else '-'})"
            return f"{grupos[opt]['nombre']} ({grupos[opt]['puntos']} pts)"

        sel_gan = st.selectbox(
            "Equipo a mostrar en la pantalla de celebración",
            options=opciones_ganador,
            index=idx_gan,
            format_func=fmt_gan,
            key="sel_winner_box"
        )
        nuevo_gan_id = None if sel_gan == "auto" else sel_gan
        if nuevo_gan_id != store.get("ganador_id"):
            store["ganador_id"] = nuevo_gan_id
            _save_to_disk(store)
            st.rerun()

    st.divider()

    st.subheader(f"📋 Todos los grupos guardados ({len(grupos)})")
    if not grupos:
        st.caption("Aún no hay grupos creados.")
    else:
        for gid, gdata in list(grupos.items()):
            en_pantalla = ""
            if gid == store.get("activo_izq"):
                en_pantalla = " 🟢 [IZQUIERDA]"
            elif gid == store.get("activo_der"):
                en_pantalla = " 🔴 [DERECHA]"

            with st.expander(f"**{gdata['nombre']}** — {gdata['puntos']} pts{en_pantalla}", expanded=(gid in [store.get("activo_izq"), store.get("activo_der")])):
                c_preview, c_controls = st.columns([1.5, 4.5])

                with c_preview:
                    raw_img = _b64_to_img(gdata.get("img_b64"))
                    if raw_img:
                        st.image(Image.open(io.BytesIO(raw_img)), use_container_width=True)
                    else:
                        st.markdown("<div style='font-size: 3.5rem; text-align: center;'>🛡️</div>", unsafe_allow_html=True)

                with c_controls:
                    nuevo_nombre = st.text_input("Nombre", value=gdata["nombre"], key=f"nom_{gid}")
                    if nuevo_nombre.strip() and nuevo_nombre.strip() != gdata["nombre"]:
                        store["grupos"][gid]["nombre"] = nuevo_nombre.strip()
                        _save_to_disk(store)
                        st.rerun()

                    b1, b2, b3, b4, b5 = st.columns(5)
                    if b1.button("➕ 1", key=f"p1_{gid}", use_container_width=True):
                        store["grupos"][gid]["puntos"] += 1
                        _save_to_disk(store)
                        st.rerun()
                    if b2.button("➕ 5", key=f"p5_{gid}", use_container_width=True):
                        store["grupos"][gid]["puntos"] += 5
                        _save_to_disk(store)
                        st.rerun()
                    if b3.button("➕ 10", key=f"p10_{gid}", use_container_width=True):
                        store["grupos"][gid]["puntos"] += 10
                        _save_to_disk(store)
                        st.rerun()
                    if b4.button("➖ 1", key=f"m1_{gid}", use_container_width=True):
                        store["grupos"][gid]["puntos"] = max(0, store["grupos"][gid]["puntos"] - 1)
                        _save_to_disk(store)
                        st.rerun()
                    if b5.button("0️⃣ Reset", key=f"r0_{gid}", use_container_width=True):
                        store["grupos"][gid]["puntos"] = 0
                        _save_to_disk(store)
                        st.rerun()

                    c_up, c_del = st.columns([3, 1])
                    with c_up:
                        up_edit = st.file_uploader("Cambiar imagen", type=["png", "jpg", "jpeg", "webp"], key=f"up_{gid}")
                        if up_edit is not None:
                            store["grupos"][gid]["img_b64"] = _img_to_b64(up_edit.getvalue())
                            _save_to_disk(store)
                            st.rerun()
                    with c_del:
                        st.write("")
                        if st.button("🗑️ Eliminar", key=f"del_{gid}", use_container_width=True):
                            del store["grupos"][gid]
                            if store.get("activo_izq") == gid:
                                store["activo_izq"] = next(iter(store["grupos"]), None)
                            if store.get("activo_der") == gid:
                                restantes = [k for k in store["grupos"] if k != store.get("activo_izq")]
                                store["activo_der"] = restantes[0] if restantes else None
                            if store.get("ganador_id") == gid:
                                store["ganador_id"] = None
                            _save_to_disk(store)
                            st.rerun()

# ==============================================================================
# MODO 2A: EQUIPO GANADOR CON CELEBRACIÓN (?view=winner)
# ==============================================================================
elif view_mode == "winner":
    st_autorefresh(interval=2000, key="winner_refresh")

    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            [data-testid="stToolbar"] {display: none;}
            [data-testid="stDecoration"] {display: none;}

            .stApp {
                background: radial-gradient(circle at center, #312e81 0%, #0f172a 75%);
                color: #f8fafc;
            }

            .event-logo-box img {
                max-height: 95px !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
                margin: 0 auto 4px auto;
            }

            .event-title {
                text-align: center;
                font-size: 2.2rem;
                font-weight: 800;
                letter-spacing: 3px;
                text-transform: uppercase;
                color: #38bdf8;
                margin-bottom: 0.2rem;
            }

            .champion-badge {
                text-align: center;
                font-size: 2.2rem;
                font-weight: 900;
                letter-spacing: 4px;
                text-transform: uppercase;
                color: #facc15;
                text-shadow: 0 0 25px rgba(250, 204, 21, 0.65);
                margin-bottom: 1rem;
                animation: pulseBadge 1.6s ease-in-out infinite alternate;
            }

            @keyframes pulseBadge {
                from { transform: scale(1); }
                to { transform: scale(1.05); }
            }

            [data-testid="stImage"] img {
                max-height: 330px;
                width: 100% !important;
                object-fit: contain;
                border-radius: 24px;
                border: 3px solid rgba(250, 204, 21, 0.65);
                box-shadow: 0 14px 36px rgba(250, 204, 21, 0.28);
                background: rgba(15, 23, 42, 0.7);
                padding: 10px;
            }

            .winner-name {
                text-align: center;
                font-size: 3.1rem;
                font-weight: 900;
                text-transform: uppercase;
                color: #ffffff;
                margin-top: 14px;
                text-shadow: 0 6px 22px rgba(0, 0, 0, 0.5);
            }

            .winner-pts {
                text-align: center;
                font-size: 4.5rem;
                font-weight: 900;
                color: #facc15;
                line-height: 1.05;
                margin-top: 4px;
                text-shadow: 0 6px 24px rgba(250, 204, 21, 0.45);
            }
        </style>
    """, unsafe_allow_html=True)

    render_celebration_overlay()
    render_event_header(store, is_admin_view=False)

    winner = resolve_winner(store)
    if not winner:
        st.markdown(
            "<div style='text-align: center; font-size: 2rem; color: #94a3b8; padding: 90px 0;'>"
            "Aún no hay un equipo ganador definido."
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="champion-badge">🏆 ¡EQUIPO GANADOR! 🏆</div>', unsafe_allow_html=True)
        _, w_col, _ = st.columns([3, 4, 3])
        with w_col:
            raw_w = _b64_to_img(winner.get("img_b64"))
            if raw_w:
                st.image(Image.open(io.BytesIO(raw_w)), use_container_width=True)
            else:
                st.markdown("<div style='font-size: 7.5rem; text-align: center; padding: 20px;'>🏆</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="winner-name">{winner["nombre"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="winner-pts">{winner["puntos"]} PTS</div>', unsafe_allow_html=True)

# ==============================================================================
# MODO 2B: PRESENTACIÓN DE TODOS LOS GRUPOS EN UNA SOLA PANTALLA (?view=lineup)
# ==============================================================================
elif view_mode == "lineup":
    st_autorefresh(interval=2000, key="lineup_refresh")

    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            [data-testid="stToolbar"] {display: none;}
            [data-testid="stDecoration"] {display: none;}

            .stApp {
                background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
                color: #f8fafc;
            }

            .event-logo-box img {
                max-height: 95px !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
                margin: 0 auto 4px auto;
            }

            .event-title {
                text-align: center;
                font-size: 2.3rem;
                font-weight: 800;
                letter-spacing: 3px;
                text-transform: uppercase;
                color: #38bdf8;
                margin-bottom: 0.2rem;
            }

            .lineup-sub {
                text-align: center;
                font-size: 1.15rem;
                font-weight: 600;
                letter-spacing: 2px;
                text-transform: uppercase;
                color: #94a3b8;
                margin-bottom: 1.4rem;
            }

            [data-testid="stImage"] img {
                max-height: 220px;
                width: 100% !important;
                object-fit: contain;
                border-radius: 18px;
                box-shadow: 0 10px 24px rgba(0, 0, 0, 0.45);
                background: rgba(15, 23, 42, 0.65);
                padding: 6px;
            }

            .lineup-name {
                text-align: center;
                font-size: 1.65rem;
                font-weight: 800;
                margin-top: 10px;
                margin-bottom: 2px;
                text-transform: uppercase;
                color: #ffffff;
            }

            .lineup-pts {
                text-align: center;
                font-size: 1.5rem;
                font-weight: 800;
                color: #facc15;
                margin-bottom: 24px;
            }
        </style>
    """, unsafe_allow_html=True)

    render_event_header(store, is_admin_view=False)
    st.markdown('<div class="lineup-sub">EQUIPOS PARTICIPANTES</div>', unsafe_allow_html=True)

    grupos_lista = list(store["grupos"].values())
    total = len(grupos_lista)

    if total == 0:
        st.markdown(
            "<div style='text-align: center; font-size: 1.8rem; color: #94a3b8; padding: 90px 0;'>"
            "Aún no hay grupos registrados. Agrega grupos desde ?admin=true"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        if total <= 2:
            cols_per_row = 2
        elif total <= 4:
            cols_per_row = total
        elif total <= 6:
            cols_per_row = 3
        else:
            cols_per_row = 4

        rows = math.ceil(total / cols_per_row)
        idx = 0
        for _ in range(rows):
            cols = st.columns(cols_per_row)
            for c_idx in range(cols_per_row):
                if idx >= total:
                    break
                g = grupos_lista[idx]
                with cols[c_idx]:
                    raw = _b64_to_img(g.get("img_b64"))
                    if raw:
                        st.image(Image.open(io.BytesIO(raw)), use_container_width=True)
                    else:
                        st.markdown("<div style='font-size: 5rem; text-align: center; padding: 20px;'>🛡️</div>", unsafe_allow_html=True)
                    st.markdown(f'<div class="lineup-name">{g["nombre"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="lineup-pts">{g["puntos"]} PTS</div>', unsafe_allow_html=True)
                idx += 1

# ==============================================================================
# MODO 2C: VISTA DE PROYECTOR - DUELO 1 VS 1 (Pantalla pública limpia)
# ==============================================================================
else:
    st_autorefresh(interval=2000, key="projector_refresh")

    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display:none;}
            [data-testid="stToolbar"] {display: none;}
            [data-testid="stDecoration"] {display: none;}

            .stApp {
                background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
                color: #f8fafc;
            }

            .event-logo-box img {
                max-height: 105px !important;
                box-shadow: none !important;
                background: transparent !important;
                padding: 0 !important;
                margin: 0 auto 4px auto;
            }

            .event-title {
                text-align: center;
                font-size: 2.5rem;
                font-weight: 800;
                letter-spacing: 3px;
                text-transform: uppercase;
                color: #38bdf8;
                margin-bottom: 1.0rem;
                text-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
            }

            [data-testid="stImage"] img {
                max-height: 340px;
                width: 100% !important;
                object-fit: contain;
                border-radius: 20px;
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
                background: rgba(15, 23, 42, 0.6);
                padding: 8px;
            }

            .team-name-1 {
                text-align: center;
                font-size: 2.5rem;
                font-weight: 800;
                margin-top: 14px;
                margin-bottom: 4px;
                text-transform: uppercase;
                color: #60a5fa;
            }

            .team-name-2 {
                text-align: center;
                font-size: 2.5rem;
                font-weight: 800;
                margin-top: 14px;
                margin-bottom: 4px;
                text-transform: uppercase;
                color: #f87171;
            }

            .score-box {
                text-align: center;
                font-size: 8rem;
                font-weight: 900;
                line-height: 1.0;
                margin: 6px 0 0 0;
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

    render_event_header(store, is_admin_view=False)

    g_izq = store["grupos"].get(store.get("activo_izq"))
    g_der = store["grupos"].get(store.get("activo_der"))

    col1, col_vs, col2 = st.columns([5, 1, 5])

    with col1:
        if g_izq:
            raw1 = _b64_to_img(g_izq.get("img_b64"))
            if raw1:
                st.image(Image.open(io.BytesIO(raw1)), use_container_width=True)
            else:
                st.markdown("<div style='font-size: 7rem; text-align: center; padding: 30px;'>🛡️</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="team-name-1">{g_izq["nombre"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box">{g_izq["puntos"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 2rem; text-align: center; padding: 80px 0; color: #94a3b8;'>Selecciona Grupo Izquierda en ?admin=true</div>", unsafe_allow_html=True)

    with col_vs:
        st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)

    with col2:
        if g_der:
            raw2 = _b64_to_img(g_der.get("img_b64"))
            if raw2:
                st.image(Image.open(io.BytesIO(raw2)), use_container_width=True)
            else:
                st.markdown("<div style='font-size: 7rem; text-align: center; padding: 30px;'>⚔️</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="team-name-2">{g_der["nombre"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="score-box">{g_der["puntos"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 2rem; text-align: center; padding: 80px 0; color: #94a3b8;'>Selecciona Grupo Derecha en ?admin=true</div>", unsafe_allow_html=True)
