import streamlit as st
import math
import base64

# --- CONFIGURACIÓN DE PÁGINA Y CSS PERSONALIZADO ---
st.set_page_config(page_title="BridgeBearing PRO 2026", layout="wide")

# CSS para asegurar el contraste, ajustar fuentes, estilizar pestañas y añadir marca de agua
st.markdown("""
<style>
    /* El texto global es negro por config.toml, funciona bien en blanco y gris claro */

    /* Asegura que todos los títulos (H1 a H6) sean azules corporativos y en negrita */
    h1, h2, h3, h4, h5, h6 {
        color: #054D7F !important;
        font-weight: bold !important;
    }
    
    /* Aumenta el tamaño de fuente general del texto */
    .stApp {
        font-size: 14px; 
    }

    /* Asegura que el texto dentro de TODOS los inputs sea NEGRO */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] div[role="button"] > span,
    div[data-testid="stRadio"] label span,
    div.stSelectbox div[role="listbox"] div span {
        color: #000000 !important;
    }
    
    /* Estilo base para todas las pestañas: texto azul corporativo y negrita */
    button[data-testid="stConfigurableLink"] {
        font-size: 16px !important;
        padding: 10px 15px !important;
        background-color: #FFFFFF !important; /* Fondo blanco para inactivo */
        color: #054D7F !important; /* Texto azul corporativo para inactivo */
        border-radius: 5px;
        font-weight: bold !important; /* Negrita */
        border: 1px solid #054D7F; /* Borde sutil para definir la pestaña */
        margin-right: 5px; /* Espacio entre pestañas */
    }

    /* Resalta la pestaña activa con fondo azul y letra blanca */
    button[data-testid="stConfigurableLink"][aria-selected="true"] {
        background-color: #054D7F !important; /* Fondo azul corporativo para activo */
        color: #FFFFFF !important; /* Texto blanco para activo */
        border: 1.5px solid #054D7F;
    }
    
    /* Eliminar espacio superior para acercar el contenido al borde */
    .block-container {
        padding-top: 2rem; 
    }
    
    /* Asegurar que las etiquetas de metric se vean bien */
    div[data-testid="stMetricValue"] {
        color: #054D7F;
        font-weight: bold;
    }

    /* CSS para la marca de agua (Watermark) */
    .watermark {
        position: fixed;
        top: 50%; /* Centrado verticalmente */
        left: 50%; /* Centrado horizontalmente */
        transform: translate(-50%, -50%); /* Ajuste para centrar exactamente el centro de la imagen */
        width: 1600px; /* Tamaño muy grande */
        height: auto;
        opacity: 0.03; /* Muy difuminado */
        pointer-events: none; /* Permite hacer clic a través de la imagen */
    }
    
    /* Clase para el logo en la cabecera */
    .header-logo-container {
        display: flex;
        justify-content: flex-end; /* Alinea el contenido a la derecha del contenedor (la columna) */
        align-items: center; /* Centra verticalmente el logo dentro del contenedor */
        height: 100%;
        padding-top: 15px; /* Añade un pequeño padding superior para mejor alineación visual con el st.title */
    }
    .header-logo {
        height: 50px; /* Tamaño fijo para el logo superior */
    }
</style>
""", unsafe_allow_html=True)


# --- BASES DE DATOS (NORMATIVA EN 1337-3 Y EN 1993-1-1) ---
MATERIALES_ACERO = {
    "S235JR": {"fy": 235.0, "Es": 210000.0, "vs": 0.3},
    "S275JR": {"fy": 275.0, "Es": 210000.0, "vs": 0.3},
    "S355JR": {"fy": 355.0, "Es": 355000.0, "vs": 0.3},
}

MATERIALES_ELASTOMERO = {
    "Caucho Natural (NR) G=0.9": {"G": 0.9, "tipo": "NR", "Eb": 2000.0},
    "Caucho Natural (NR) G=1.15": {"G": 1.15, "tipo": "NR", "Eb": 2000.0},
    "Cloropreno (CR) G=0.9": {"G": 0.9, "tipo": "CR", "Eb": 2000.0},
    "Cloropreno (CR) G=1.15": {"G": 1.15, "tipo": "CR", "Eb": 2000.0},
}

# --- BASE DE DATOS SÍSMICA ---
MATERIALES_AISLADORES_SISMICOS = {
    "LRB (G=0.6 MPa, Plomo)": {"G": 0.6, "tipo": "LRB", "Qd_norm": 0.08, "alpha": 0.1}, 
    "HDRB (G=0.8 MPa, Amortig.)": {"G": 0.8, "tipo": "HDRB", "Qd_norm": 0.0, "alpha": 0.15}, 
}

# --- FUNCIONES DE CÁLCULO NORMATIVO ---

def check_no_deslizamiento(Fz_min_N, Fx_N, Fy_N, Area_efectiva, superficie_contacto):
    """Comprobación de no deslizamiento según UNE-EN 1337-3, apartado 5.3.3.6."""
    sigma_m_min_mpa = (Fz_min_N / Area_efectiva) / 1e6
    if superficie_contacto == "Hormigón": Kf = 0.6
    else: Kf = 0.2
    mu_e = 0.1 + (1.5 * Kf / sigma_m_min_mpa)
    Fh_N = math.sqrt(Fx_N**2 + Fy_N**2)
    F_resistencia_N = mu_e * Fz_min_N
    cumple = Fh_N <= F_resistencia_N
    return cumple, Fh_N, F_resistencia_N

def mostrar_croquis(tipo, acero_z, acero_e=""):
    """Muestra el croquis según el tipo seleccionado."""
    if tipo in ["Tipo A", "Tipo B", "Tipo C"]:
        pass 
    else:
        st.info("📌 **Aislador Sísmico:** Diseño para disipar energía (LRB/HDRB).")
        st.code(f"┌─────────────────────────┐\n│ Núcleo de Plomo (LRB)   │\n│ o Goma Alto Amortig.    │\n├─────────────────────────┤ ts (Chapa {acero_z})\n│       ELASTÓMERO        │ te\n└─────────────────────────┘", language="text")

# --- INTERFAZ LATERAL (DATOS GENERALES) ---
with st.sidebar:
    st.title("Datos generales")
    
    project_name = st.text_input("Nombre del Proyecto", value="Proyecto MRES/Cliente")
    bearing_id = st.text_input("Identificador del Apoyo", value="Apoyo P1-A")

    modo_calculo = st.selectbox("Modo de Cálculo", ["Estándar (EN 1337-3)", "Sísmico (EN 15129)"])

    if modo_calculo == "Estándar (EN 1337-3)":
        tipo_apoyo = st.selectbox("Tipo de Apoyo Estándar", ["Tipo A", "Tipo B", "Tipo C"])
    else:
        tipo_apoyo = "Aislador Sísmico"
        
    st.divider()
    st.subheader("Selección de Materiales")
    
    if tipo_apoyo == "Aislador Sísmico":
        acero_zunchos = st.selectbox("Acero de las Chapas Internas", list(MATERIALES_ACERO.keys()), index=0)
        acero_externo = acero_zunchos
        sel_elast = st.selectbox("Material Aislador", list(MATERIALES_AISLADORES_SISMICOS.keys()))
        gamma_m = st.number_input("Coeficiente γm (Seguridad Sísmica)", value=1.0, step=0.05)
    else:
        if tipo_apoyo == "Tipo C":
            acero_zunchos = st.selectbox("Acero Zunchos Internos (ts)", list(MATERIALES_ACERO.keys()), key="z1", index=0)
            acero_externo = st.selectbox("Acero Placas Exteriores (tp)", list(MATERIALES_ACERO.keys()), key="z2", index=1)
        else:
            acero_zunchos = st.selectbox("Acero de las Chapas", list(MATERIALES_ACERO.keys()), index=0)
            acero_externo = acero_zunchos
        sel_elast = st.selectbox("Tipo de Elastómero", list(MATERIALES_ELASTOMERO.keys()))
        gamma_m = st.number_input("Coeficiente γm (Seguridad)", value=1.15, step=0.05)
    
    tipo_carga_KL = st.selectbox("Tipo de Carga (Factor KL)", ["Estática (1.0)", "Dinámica/Puente (1.5)"])
    KL = 1.0 if tipo_carga_KL == "Estática (1.0)" else 1.5
    
    superficie_contacto = st.selectbox("Superficie de Contacto (Fricción)", ["Hormigón", "Otros materiales/morteros"])

# --- EXTRACCIÓN DE DATOS DE MATERIAL SELECCIONADO ---
mat_z = MATERIALES_ACERO[acero_zunchos]

if tipo_apoyo == "Aislador Sísmico":
    mat_elast = MATERIALES_AISLADORES_SISMICOS[sel_elast]
    G = mat_elast['G']
else:
    mat_elast = MATERIALES_ELASTOMERO[sel_elast]
    G = mat_elast['G']
    Eb = mat_elast['Eb'] 

# --- CUERPO PRINCIPAL ---

# NUEVO LAYOUT DEL TÍTULO CON LOGO DERECHO
col_title, col_logo_header = st.columns([0.8, 0.2])
with col_title:
    st.title(f"{project_name} | {bearing_id} | {tipo_apoyo.upper()}")
with col_logo_header:
    try:
        bin_str_header_logo = base64.b64encode(open("mres_logo.png", "rb").read()).decode('utf-8')
        st.markdown(f'<div class="header-logo-container"><img src="data:image/png;base64,{bin_str_header_logo}" class="header-logo"></div>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("No se pudo cargar mres_logo.png para la cabecera.")


a, b, te, ts, n_capas, fz_kn, fz_min_kn, fx_kn, fy_kn, vx_mm, vy_mm, alpha_a, alpha_b, tp, d_core = [0.0]*15 
area_bruta, perim_bruto, a_prime, b_prime = [0.0]*4
tab1, tab2 = st.tabs(["PARÁMETROS GEOMÉTRICOS Y CARGAS", "RESULTADOS Y VERIFICACIONES NORMATIVAS"])

with tab1:
    col_geo, col_cargas = st.columns(2)
    with col_geo:
        st.subheader("Geometría")
        forma = st.radio("Forma del apoyo", ["Rectangular", "Circular"], horizontal=True)
        if forma == "Rectangular":
            a = st.number_input("Lado a (mm)", value=300)
            b = st.number_input("Lado b (mm)", value=400)
            area_bruta = a * b
            perim_bruto = 2 * (a + b)
            a_prime, b_prime = a, b
        else:
            diam = st.number_input("Diámetro D (mm)", value=400)
            a = b = diam
            area_bruta = (math.pi * diam**2) / 4
            perim_bruto = math.pi * diam
            a_prime = b_prime = diam
        te = st.number_input("Espesor capa elastómero te (mm)", value=10.0)
        ts = st.number_input("Espesor zunchos internos ts (mm)", value=3.0)
        if tipo_apoyo in ["Tipo B", "Tipo C", "Aislador Sísmico"]: n_capas = st.number_input("Número de capas internas de goma (n)", value=10 if tipo_apoyo=="Aislador Sísmico" else 3, min_value=1)
        else: n_capas = 1
        if tipo_apoyo == "Tipo C": tp = st.number_input(f"Espesor Placa Exterior tp ({acero_externo}) (mm)", value=20.0)
        if sel_elast.startswith("LRB"):
            d_core = st.number_input("Diámetro Núcleo de Plomo d_core (mm)", value=int(diam/4) if 'diam' in locals() else 100)
    with col_cargas:
        if modo_calculo == "Estándar (EN 1337-3)":
             st.subheader("Cargas y Desplazamientos ELU / ELS")
             fz_kn = st.number_input("Fz ELU (kN)", value=800.0)
             fz_min_kn = st.number_input("Fz Mín ELS (kN)", value=100.0)
             fx_kn = st.number_input("Fx ELU (kN)", value=0.0)
             fy_kn = st.number_input("Fy ELU (kN)", value=0.0)
             col_vx, col_vy = st.columns(2)
             with col_vx:
                 vx_mm = st.number_input("Desplazamiento Horizontal vx (mm)", value=20.0)
             with col_vy:
                 vy_mm = st.number_input("Desplazamiento Horizontal vy (mm)", value=0.0)
             st.subheader("Giro Angular (Rotación)")
             col_aa, col_ab = st.columns(2)
             with col_aa:
                alpha_a_mrad = st.number_input("Giro alpha_a (mrad, dir. a)", value=5.0, format="%.2f")
             with col_ab:
                alpha_b_mrad = st.number_input("Giro alpha_b (mrad, dir. b)", value=0.00, format="%.2f")
             
             alpha_a = alpha_a_mrad / 1000.0
             alpha_b = alpha_b_mrad / 1000.0

        else:
            st.subheader("Parámetros Sísmicos (EN 1998-1)")
            fz_kn = st.number_input("Carga Vertical Permanente G + Q (kN)", value=1200.0)
            d_sismico_mm = st.number_input("Desplazamiento Sísmico de Diseño d_c (mm)", value=150.0)
            fz_min_kn = fz_kn
            vx_mm = d_sismico_mm
            vy_mm = 0.0 
            fx_kn, fy_kn, alpha_a, alpha_b = 0.0, 0.0, 0.0, 0.0

# --- CÁLCULOS TÉCNICOS ---
A1 = area_bruta 
perim = perim_bruto 
if sel_elast.startswith("LRB") and d_core > 0:
    A_core = (math.pi * d_core**2) / 4
    A_rubber_net = A1 - A_core
    perim_rubber = math.pi * d_core 
    S = A_rubber_net / (perim_rubber * te)
    sigma_m = (fz_kn * 1000) / A_rubber_net 
else:
    A_rubber_net = A1 
    S = A1 / (perim * te) 
    sigma_m = (fz_kn * 1000) / A1
Te = n_capas * te 
eps_c_d = 1.5 * (sigma_m / (G * S)) 
vxy_d = math.sqrt(vx_mm**2 + vy_mm**2) 
eps_q_d = vxy_d / Te 
eps_alpha_d = ((a_prime**2 * alpha_a**2) + (b_prime**2 * alpha_b**2))**0.5 / (3 * Te)
if modo_calculo == "Estándar (EN 1337-3)":
    eps_tot = KL * (eps_c_d + eps_q_d + eps_alpha_d)
    limite_eps = 7.0 / gamma_m
    ts_min = (1.0 * sigma_m * te) / (mat_z['fy'] / gamma_m)
    limite_torsion_mpa = (2/3) * (a_prime * G * S) / Te
    cumple_torsion = sigma_m <= limite_torsion_mpa
    Fz_min_N = fz_min_kn * 1000
    Fx_N = fx_kn * 1000
    Fy_N = fy_kn * 1000
    cumple_deslizamiento, Fh_calc, Fh_resis = check_no_deslizamiento(Fz_min_N, Fx_N, Fy_N, A1, superficie_contacto)
    Kv_kN_mm = (Eb * A1) / (Te * 1000) 
    Kh_kN_mm = (G * A1) / (Te * 1000)
else:
    Ds_mm = d_sismico_mm
    Qd_norm = mat_elast['Qd_norm']
    alpha = mat_elast['alpha'] 
    Qd_N = Qd_norm * A_rubber_net 
    Kh1_N_mm = (G * A_rubber_net) / Te 
    Kh2_N_mm = alpha * Kh1_N_mm 
    Keff_N_mm = (Qd_N * (1 - alpha) / Ds_mm) + Kh2_N_mm 
    Keff_kN_mm = Keff_N_mm / 1000 
    d_y_mm = Qd_N / Kh1_N_mm 
    if Ds_mm > d_y_mm:
        xi_eff_decimal = (2 * Qd_N * (Ds_mm - d_y_mm)) / (math.pi * Keff_N_mm * Ds_mm**2)
        xi_eff_percent = xi_eff_decimal * 100
    else:
        xi_eff_percent = 0.0 
    eps_tot, limite_eps, ts_min, limite_torsion_mpa, cumple_torsion, cumple_deslizamiento, Fh_calc, Fh_resis, Kv_kN_mm, Kh_kN_mm = [0.0]*10

# --- PESTAÑA 2: RESULTADOS ---
with tab2:
    st.header(f"Verificaciones y Resultados ({modo_calculo})")
    if modo_calculo == "Estándar (EN 1337-3)":
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.subheader("Geometría & Tensión")
            st.metric("Factor de Forma (S)", f"{S:.2f}")
            st.metric("Tensión Media (σm)", f"{sigma_m:.2f} MPa")
            st.metric("Espesor Goma Total (Te)", f"{Te:.1f} mm")
            st.metric("Rigidez Vertical $K_v$", f"{Kv_kN_mm:.2f} kN/mm")
        with col_res2:
            st.subheader("Deformaciones")
            st.metric("Eps. Total $\epsilon_{t,d}$", f"{eps_tot:.4f}")
            st.metric("Límite ULS", f"{limite_eps:.4f}")
            st.metric("Rigidez Horizontal $K_h$", f"{Kh_kN_mm:.2f} kN/mm")
        with col_res3:
            st.subheader("Comprobaciones Adicionales")
            if eps_tot <= limite_eps: st.success(f"✅ Límite Deformación CUMPLE")
            else: st.error(f"❌ Límite Deformación FALLA")

            if ts >= ts_min: st.success(f"✅ Zunchos OK (Mín: {ts_min:.2f}mm)")
            else: st.error(f"❌ Zunchos Insuficientes")
            if cumple_deslizamiento: st.success(f"✅ NO DESLIZA")
            else: st.warning(f"⚠️ RIESGO DESLIZAMIENTO")
            if cumple_torsion: st.success(f"✅ ESTABLE Torsión")
            else: st.error(f"❌ INESTABLE Torsión")
    else:
        st.subheader(f"Resultados para Aislador Sísmico {sel_elast}")
        col_sism1, col_sism2, col_sism3 = st.columns(3)
        col_sism1.metric("Rigidez Efectiva $K_{eff}$", f"{Keff_kN_mm:.2f} kN/mm")
        col_sism2.metric("Amortiguamiento $\\xi_{eff}$", f"{xi_eff_percent:.1f} %")
        col_sism3.metric("Fuerza Característica $Q_d$", f"{Qd_N/1000:.2f} kN")
        st.subheader("Verificación de Desplazamiento Sísmico")
        if eps_q_d >= 1.0 and eps_q_d <= 3.0: 
             st.success(f"✅ DESPLAZAMIENTO OK: $\gamma$ = {eps_q_d:.4f} (Rango típico 1.0 a 3.0)")
        else:
             st.warning(f"⚠️ REVISAR DESPLAZAMIENTO: $\gamma$ = {eps_q_d:.4f} (Fuera de rango típico)")

    reporte = f"REPORTE TÉCNICO\nModo: {modo_calculo}\nMaterial: {sel_elast}\nSigma_m: {sigma_m:.2f} MPa"
    st.download_button("Descargar Informe Técnico", reporte, file_name="calculo_apoyo.txt")

with st.sidebar:
    st.divider()
    mostrar_croquis(tipo_apoyo, acero_zunchos)

# --- Implementación de la marca de agua ---
try:
    bin_str_logo = base64.b64encode(open("mres_logo.png", "rb").read()).decode('utf-8')
    st.markdown(f'<img src="data:image/png;base64,{bin_str_logo}" class="watermark">', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("No se pudo cargar mres_logo.png para la marca de agua.")
