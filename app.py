import streamlit as st
import math
import base64

# --- CONFIGURACIÓN DE PÁGINA Y CSS PERSONALIZADO ---
st.set_page_config(page_title="BridgeBearing PRO 2026", layout="wide")

st.markdown("""
<style>
    /* Estilos Corporativos MRES */
    h1, h2, h3, h4, h5, h6 { color: #054D7F !important; font-weight: bold !important; }
    .stApp { font-size: 14px; }
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] div[role="button"] > span,
    div[data-testid="stRadio"] label span { color: #000000 !important; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { color: #054D7F; font-weight: bold; font-size: 24px; }
    .stMetric label { font-size: 12px; }
    .stAlert { font-size: 12px; }
    /* Estilo para el Logo y Marca de Agua */
    .header-logo-container { display: flex; justify-content: flex-end; align-items: center; height: 100%; padding-top: 15px; }
    .header-logo { height: 50px; }
    .watermark {
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 1600px; height: auto; opacity: 0.03; pointer-events: none; z-index: -1;
    }
</style>
""", unsafe_allow_html=True)

# --- BASES DE DATOS ---
MATERIALES_ACERO = {
    "S235JR": {"fy": 235.0, "Es": 210000.0, "vs": 0.3},
    "S275JR": {"fy": 275.0, "Es": 210000.0, "vs": 0.3},
    # ✅ FIX: Es = 210000 MPa (no 355000)
    "S355JR": {"fy": 355.0, "Es": 210000.0, "vs": 0.3},
}
MATERIALES_ELASTOMERO = {
    "Caucho Natural (NR) G=0.9": {"G": 0.9, "tipo": "NR", "Eb": 2000.0},
    "Caucho Natural (NR) G=1.15": {"G": 1.15, "tipo": "NR", "Eb": 2000.0},
    "Cloropreno (CR) G=0.9": {"G": 0.9, "tipo": "CR", "Eb": 2000.0},
    "Cloropreno (CR) G=1.15": {"G": 1.15, "tipo": "CR", "Eb": 2000.0},
}
MATERIALES_AISLADORES_SISMICOS = {
    "LRB (G=0.6 MPa, Plomo)": {"G": 0.6, "tipo": "LRB", "Qd_norm": 0.08, "alpha": 0.1},
    "HDRB (G=0.8 MPa, Amortig.)": {"G": 0.8, "tipo": "HDRB", "Qd_norm": 0.0, "alpha": 0.15},
}

# --- FUNCIONES DE CÁLCULO ---
def check_no_deslizamiento(Fz_min_N, Fx_N, Fy_N, Area_efectiva_m2, sup_c, inf_c, superficie_contacto):
    sigma_m_min_mpa = (Fz_min_N / Area_efectiva_m2) / 1e6
    opciones_ancladas = ["Placa Volada", "Placa Encastrada"]

    # Si ambas placas ancladas, se considera que no hay deslizamiento
    if sup_c in opciones_ancladas and inf_c in opciones_ancladas:
        return True, 0.0, 9999999.0, sigma_m_min_mpa, 0.6

    # ✅ FIX NORMATIVO: si σm,min < 3 MPa => NO OK (fricción no aplicable)
    if sigma_m_min_mpa < 3.0:
        Fh_N = math.sqrt(Fx_N**2 + Fy_N**2)
        return False, Fh_N, 0.0, sigma_m_min_mpa, 0.0  # capacidad 0

    if superficie_contacto.startswith("Hormigón"):
        Kf = 0.6
    else:
        Kf = 0.2

    mu_e = 0.1 + (1.5 * Kf / max(sigma_m_min_mpa, 0.001))
    Fh_N = math.sqrt(Fx_N**2 + Fy_N**2)
    F_resistencia_N = mu_e * Fz_min_N
    cumple = Fh_N <= F_resistencia_N
    return cumple, Fh_N, F_resistencia_N, sigma_m_min_mpa, Kf

def mostrar_croquis(tipo, acero_z):
    if tipo == "Aislador Sísmico":
        st.code(
            f"┌─────────────────────────┐\n"
            f"│ Núcleo de Plomo (LRB)   │\n"
            f"│ o Goma Alto Amortig.    │\n"
            f"├─────────────────────────┤ ts (Chapa {acero_z})\n"
            f"│       ELASTÓMERO        │ te\n"
            f"└─────────────────────────┘",
            language="text"
        )

# --- INTERFAZ LATERAL ---
with st.sidebar:
    st.title("Datos generales")
    project_name = st.text_input("Nombre del Proyecto", value="Proyecto MRES/Cliente")
    bearing_id = st.text_input("Identificador del Apoyo", value="Apoyo P1-A")
    modo_calculo = st.selectbox("Modo de Cálculo", ["Estándar (EN 1337-3)", "Sísmico (EN 15129)"])

    tipo_anclaje_sup, tipo_anclaje_inf = "", ""
    if modo_calculo == "Estándar (EN 1337-3)":
        tipo_apoyo = st.selectbox("Tipo de Apoyo Estándar", ["Tipo A", "Tipo B", "Tipo C"])
        if tipo_apoyo == "Tipo C":
            st.subheader("Configuración Tipo C")
            opciones_c = ["Gofrado (Fricción mejorada)", "Placa Volada", "Placa Encastrada"]
            tipo_anclaje_sup = st.selectbox("Placa Superior", opciones_c)
            tipo_anclaje_inf = st.selectbox("Placa Inferior", opciones_c)
    else:
        tipo_apoyo = "Aislador Sísmico"

    st.divider()
    st.subheader("Materiales")
    if tipo_apoyo == "Aislador Sísmico":
        acero_zunchos = st.selectbox("Acero Chapas Internas", list(MATERIALES_ACERO.keys()), index=0)
        sel_elast = st.selectbox("Material Aislador", list(MATERIALES_AISLADORES_SISMICOS.keys()))
        gamma_m = st.number_input("Coeficiente γm (Sísmico)", value=1.0)
    else:
        acero_zunchos = st.selectbox("Acero de las Chapas", list(MATERIALES_ACERO.keys()), index=0)
        sel_elast = st.selectbox("Tipo de Elastómero", list(MATERIALES_ELASTOMERO.keys()))
        gamma_m = st.number_input("Coeficiente γm (Seguridad)", value=1.15)

    KL = st.selectbox("Factor de Carga (KL)", [1.5, 1.0], help="1.5 para Puentes (Dinámica), 1.0 para Edificación (Estática)")
    st.divider()
    superficie_contacto = st.selectbox("Superficie de Contacto (Fricción)", ["Hormigón Kf=0,6", "resto de materiales kf=0,2"])

# --- CUERPO PRINCIPAL ---
col_title, col_logo_header = st.columns([0.8, 0.2])
try:
    bin_str_logo = base64.b64encode(open("mres_logo.png", "rb").read()).decode('utf-8')
    logo_src = f"data:image/png;base64,{bin_str_logo}"
except:
    logo_src = None

with col_title:
    st.title(f"{project_name} | {bearing_id} | {tipo_apoyo.upper()}")

with col_logo_header:
    if logo_src:
        st.markdown(f'<div class="header-logo-container"><img src="{logo_src}" class="header-logo"></div>', unsafe_allow_html=True)

col_params, col_results = st.columns([0.6, 0.4])

with col_params:
    st.subheader("Geometría")
    forma = st.radio("Forma del apoyo", ["Rectangular", "Circular"], horizontal=True)

    if forma == "Rectangular":
        a = st.number_input("Lado a (mm)", value=300.0)
        b = st.number_input("Lado b (mm)", value=400.0)
        area_bruta, perim_bruto = a * b, 2 * (a + b)
        a_prime = a
    else:
        diam = st.number_input("Diámetro D (mm)", value=400.0)
        a = diam
        area_bruta, perim_bruto = (math.pi * diam**2) / 4, math.pi * diam
        a_prime = diam

    t_f = st.number_input("Espesor forro lateral t_f (mm)", value=5.0)

    te = st.number_input("Espesor capa elastómero te (mm)", value=10.0)
    ts = st.number_input("Espesor zunchos internos ts (mm)", value=3.0)
    n_capas = st.number_input("Número de capas internas", value=3, min_value=1)

    if tipo_apoyo == "Tipo C":
        st.subheader("Detalles de Placas")
        if "Placa Volada" in [tipo_anclaje_sup, tipo_anclaje_inf]:
            st.number_input("Espesor Placa Exterior tp (mm)", value=20.0, key="tp_val")
        if "Placa Encastrada" in [tipo_anclaje_sup, tipo_anclaje_inf]:
            st.number_input("Profundidad de empotramiento (mm)", value=100, key="prof_val")

    usar_agujeros = st.checkbox("Añadir agujeros (anclajes pasantes)")
    area_agujeros = 0.0
    if usar_agujeros:
        n_agujeros = st.number_input("Número de agujeros", min_value=1, max_value=4, value=2)
        diam_agujero = st.number_input("Diámetro de agujero (mm)", value=22.0, help="Diámetro del agujero terminado, ej. para M20 usar 22mm")
        area_agujeros = n_agujeros * (math.pi * diam_agujero**2) / 4

    if modo_calculo == "Estándar (EN 1337-3)":
        st.subheader("Cargas ELU / ELS")
        fz_kn = st.number_input("Fz Máxima ELU (kN)", value=800.0)
        fz_min_kn = st.number_input("Fz Mínima ELS (kN)", value=100.0)
        fx_kn = st.number_input("Fx ELU (kN)", value=0.0)
        fy_kn = st.number_input("Fy ELU (kN)", value=0.0)
        vx_mm = st.number_input("Desplazamiento vx (mm)", value=20.0)
        giro_mrad = st.number_input("Giro alpha_a (mrad)", value=5.0)
        alpha_a = giro_mrad / 1000.0
    else:
        fz_kn = st.number_input("Carga Permanente G + Q (kN)", value=1200.0)
        vx_mm = st.number_input("Desplazamiento Sísmico (mm)", value=150.0)
        fz_min_kn, fx_kn, fy_kn, alpha_a = fz_kn, 0.0, 0.0, 0.0

# --- CÁLCULOS TÉCNICOS ---
mat_elast = MATERIALES_AISLADORES_SISMICOS[sel_elast] if modo_calculo == "Sísmico (EN 15129)" else MATERIALES_ELASTOMERO[sel_elast]
G, Eb = mat_elast['G'], mat_elast.get('Eb', 2000.0)

if forma == "Rectangular":
    a_net_dim = a - 2 * t_f
    b_net_dim = b - 2 * t_f
    A_net = a_net_dim * b_net_dim - area_agujeros
    perim_neto_libre = 2 * (a_net_dim + b_net_dim)
else:
    d_net_dim = diam - 2 * t_f
    A_net = (math.pi * d_net_dim**2) / 4 - area_agujeros
    perim_neto_libre = math.pi * d_net_dim

if A_net <= 0:
    st.error("Error: Área Neta calculada es cero o negativa. Revise geometría (t_f o agujeros).")
    st.stop()

S = A_net / (perim_neto_libre * te)
Te = n_capas * te
sigma_m = (fz_kn * 1000) / A_net
sigma_m_min = (fz_min_kn * 1000) / A_net
eps_c_d = 1.5 * (sigma_m / (G * S))
gamma_cizalla = vx_mm / Te
eps_alpha_d = (a_prime * alpha_a) / (3 * Te)

# Inicializamos variables
cumple_desl, fr_res, kf_res, Kh_kN_mm, Keff = False, 0.0, 0.0, 0.0, 0.0

if modo_calculo == "Estándar (EN 1337-3)":
    eps_tot = KL * (eps_c_d + gamma_cizalla + eps_alpha_d)
    limite_eps = 7.0 / gamma_m
    ts_min = (sigma_m * te) / (MATERIALES_ACERO[acero_zunchos]['fy'] / gamma_m)

    # ✅ check deslizamiento (ya gestiona σm,min < 3 MPa)
    cumple_desl, Fh_N_chk, fr_res, sigma_m_min_mpa, kf_res = check_no_deslizamiento(
        fz_min_kn*1000, fx_kn*1000, fy_kn*1000, A_net/1e6,
        tipo_anclaje_sup, tipo_anclaje_inf, superficie_contacto
    )

    Kh_kN_mm = (G * area_bruta) / (Te * 1000)
else:
    Keff = ((G * area_bruta) / Te) / 1000

# --- RESULTADOS Y SUGERENCIAS ---
with col_results:
    st.header("Resultados")
    if modo_calculo == "Estándar (EN 1337-3)":
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Área Neta (A_net)", f"{A_net:.0f} mm²")
            st.metric("Factor S", f"{S:.2f}")
            st.metric("σm Máx", f"{sigma_m:.2f} MPa")
            st.metric("σm Mín", f"{sigma_m_min:.2f} MPa")
        with c2:
            st.metric("Distorsión γ", f"{gamma_cizalla:.3f}")
            st.metric("ε Total", f"{eps_tot:.3f}", delta=f"Lím: {limite_eps:.2f}")
            st.metric("Rigidez Kh", f"{Kh_kN_mm:.2f} kN/mm")

        st.divider()

        # 1. Tensión Máxima (Límite 15 MPa)
        ratio_sigma_max = sigma_m / 15.0
        if ratio_sigma_max <= 1.0:
            st.success(f"✅ Tensión Máxima OK (Uso: {ratio_sigma_max*100:.0f}%)")
        else:
            st.error(f"❌ Tensión Máxima Excesiva (Ratio: {ratio_sigma_max:.2f})")

        # 2. Tensión Mínima (Límite 3 MPa)
        if sigma_m_min >= 3.0:
            st.success(f"✅ Tensión Mínima OK (σmín/3: {sigma_m_min/3.0:.2f})")
        else:
            st.error("❌ Tensión Mínima Insuficiente (< 3 MPa)")

        # 3. Cizalla (Límite 1.0)
        ratio_gamma = gamma_cizalla / 1.0
        if ratio_gamma < 1.0:
            st.success(f"✅ Cizalla OK (Uso: {ratio_gamma*100:.0f}%)")
        else:
            st.error(f"❌ Cizalla Falla (Ratio: {ratio_gamma:.2f})")

        # 4. ε Total (Límite limite_eps)
        ratio_eps_tot = eps_tot / limite_eps
        if ratio_eps_tot <= 1.0:
            st.success(f"✅ Deformación Total OK (Uso: {ratio_eps_tot*100:.0f}%)")
        else:
            st.error(f"❌ ε Total Excesiva (Ratio: {ratio_eps_tot:.2f})")

        # 5. Zunchos
        ratio_ts = ts_min / ts
        if ratio_ts <= 1.0:
            st.success(f"✅ Zunchos OK (ts mín/ts: {ratio_ts:.2f})")
        else:
            st.error(f"❌ ts Insuficiente (Mín: {ts_min:.2f} mm)")

        # 6. Deslizamiento - RATIO CORREGIDO (UNIDADES)
        Fh_N = math.sqrt((fx_kn*1000)**2 + (fy_kn*1000)**2)

        # ✅ Si σm,min < 3 MPa => fr_res = 0 => NO OK y ratio no aplicable
        if sigma_m_min < 3.0:
            st.warning("⚠️ Riesgo de Deslizamiento: σm mín < 3 MPa (fricción no válida según norma)")
        else:
            # fr_res está en N (devuelto por check_no_deslizamiento)
            ratio_friccion = Fh_N / fr_res if fr_res > 0 else float("inf")
            if cumple_desl:
                st.success(f"✅ Estabilidad al Deslizamiento OK (Uso: {ratio_friccion*100:.0f}%, Kf={kf_res})")
            else:
                st.warning(f"⚠️ Riesgo de Deslizamiento (Ratio: {ratio_friccion:.2f} > 1.0)")

    else:
        st.metric("Rigidez Keff", f"{Keff:.2f} kN/mm")

# --- MARCA DE AGUA FINAL ---
if logo_src:
    st.markdown(f'<img src="{logo_src}" class="watermark">', unsafe_allow_html=True)

with st.sidebar:
    st.divider()
    mostrar_croquis(tipo_apoyo, acero_zunchos)

