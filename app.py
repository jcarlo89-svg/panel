import streamlit as st
from streamlit_autorefresh import st_autorefresh
from PIL import Image
import io
import json
import os
import base64
import uuid

DATA_FILE = "scoreboard_data.json"

st.set_page_config(
    page_title="Marcador de Competencia",
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
        "grupos": {},
        "activo_izq": None,
        "activo_der": None,
        "version": 1
    }

def _load_from_disk():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "grupos" in data:
                data.setdefault("titulo", "GRAN FINAL - COMPETENCIA")
                data.setdefault("activo_izq", None)
                data.setdefault("activo_der", None)
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

query_params = st.query_params
is_admin = query_params.get("admin", "false").lower() == "true"

# ==============================================================================
# MODO 1: PANEL DE ADMINISTRACIÓN (?admin=true)
# ==============================================================================
if is_admin:
    st.title("🎛️ Panel de Control y Gestión de Grupos")
    st.info("Abre la URL principal (sin `?admin=true`) en el proyector. Todos los grupos y puntajes se guardan automáticamente en `scoreboard_data.json`.")

    # 1. Título del evento
    nuevo_titulo = st.text_input("Título del Evento / Ronda", value=store["titulo"])
    if nuevo_titulo != store["titulo"]:
        store["titulo"] = nuevo_titulo
        _save_to_disk(store)

    st.divider()

    # 2. Crear nuevo grupo
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

    # 3. Seleccionar qué 2 grupos se muestran en pantalla
    st.subheader("📺 Seleccionar los 2 grupos en pantalla")
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

    # 4. Gestionar todos los grupos creados (puntajes, nombre, imagen, eliminar)
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
                            if store.get("activo_izq") == gid
