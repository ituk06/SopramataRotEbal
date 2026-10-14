import streamlit as st
import math
import os
import pandas as pd
import numpy as np
import pydeck as pdk
import datetime

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Сопромат Трубопроводов", page_icon="🛢️", layout="wide")

st.markdown("""
    <style>
    .math-block { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; font-family: 'Courier New', monospace; margin-bottom: 15px; overflow-x: auto;}
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .error-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; margin-bottom: 20px;}
    .info-text { font-size: 1.05em; color: #34495E; margin-bottom: 15px; line-height: 1.6; background-color: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #1976d2;}
    .step-header { font-size: 1.2em; font-weight: bold; color: #2C3E50; margin-top: 20px; border-bottom: 2px solid #BDC3C7; padding-bottom: 5px; }

    @media print {
        .page-break { page-break-before: always; }
        .no-break { page-break-inside: avoid; }
        header {display: none !important;}
        .sidebar {display: none !important;}
        .stButton {display: none !important;}
        section[data-testid="stSidebar"] {display: none !important;}
        .info-text { border: 1px solid #ccc; background-color: transparent; }
    }
    </style>
""", unsafe_allow_html=True)

SORTAMENT = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 15.7, 16.0, 17.5, 18.7, 19.1, 20.0, 21.0, 22.0, 23.0,
             24.0, 25.0, 26.0, 27.0, 28.0, 30.0, 32.0, 34.0, 36.0]

CLIMATE_DATA = {
    "г. Губкинский (ЯНАО)": {"t_min": -50.0, "t_max": 30.0, "lat": 64.434, "lon": 76.5026, "snow": 5, "wind": 3},
    "г. Сургут (ХМАО)": {"t_min": -43.0, "t_max": 26.0, "lat": 61.25, "lon": 73.4167, "snow": 4, "wind": 2},
    "г. Уфа (Башкортостан)": {"t_min": -35.0, "t_max": 28.0, "lat": 54.7388, "lon": 55.9721, "snow": 5, "wind": 2},
    "г. Казань (Татарстан)": {"t_min": -32.0, "t_max": 30.0, "lat": 55.7903, "lon": 49.1204, "snow": 4, "wind": 2},
    "г. Якутск": {"t_min": -54.0, "t_max": 30.0, "lat": 62.0339, "lon": 129.733, "snow": 1, "wind": 1},
    "г. Оренбург": {"t_min": -31.0, "t_max": 30.0, "lat": 51.7666, "lon": 55.1005, "snow": 3, "wind": 3},
    "г. Москва": {"t_min": -28.0, "t_max": 28.0, "lat": 55.7558, "lon": 37.6173, "snow": 3, "wind": 1},
    "г. Новосибирск": {"t_min": -39.0, "t_max": 29.0, "lat": 55.0084, "lon": 82.9357, "snow": 4, "wind": 3},
    "г. Иркутск": {"t_min": -36.0, "t_max": 28.0, "lat": 52.2978, "lon": 104.296, "snow": 2, "wind": 3},
    "г. Владивосток": {"t_min": -24.0, "t_max": 27.0, "lat": 43.1198, "lon": 131.886, "snow": 2, "wind": 4},
    "г. Тюмень": {"t_min": -35.0, "t_max": 27.0, "lat": 57.1522, "lon": 65.5272, "snow": 3, "wind": 2},
    "г. Краснодар": {"t_min": -15.0, "t_max": 35.0, "lat": 45.0393, "lon": 38.9806, "snow": 2, "wind": 3},
    "г. Мурманск": {"t_min": -28.0, "t_max": 20.0, "lat": 68.9585, "lon": 33.0827, "snow": 5, "wind": 5},
}

RUSSIA_POLY = [
    (19.0, 54.0), (28.0, 60.0), (32.0, 69.5), (40.0, 68.0), (50.0, 69.0),
    (60.0, 69.0), (70.0, 73.0), (80.0, 73.0), (90.0, 76.0), (105.0, 77.0),
    (115.0, 74.0), (130.0, 72.0), (140.0, 73.0), (160.0, 70.0), (170.0, 69.0),
    (180.0, 68.0), (190.0, 66.0), (190.0, 62.0), (160.0, 53.0), (145.0, 43.0),
    (130.0, 42.5), (115.0, 49.5), (105.0, 50.0), (90.0, 50.0), (80.0, 51.0),
    (70.0, 54.0), (60.0, 54.0), (50.0, 51.0), (45.0, 43.0), (38.0, 43.5),
    (35.0, 47.0), (28.0, 51.0)
]


def is_in_russia(lat, lon):
    x, y = lon, lat
    inside = False
    n = len(RUSSIA_POLY)
    p1x, p1y = RUSSIA_POLY[0]
    for i in range(n + 1):
        p2x, p2y = RUSSIA_POLY[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters: inside = not inside
        p1x, p1y = p2x, p2y
    return inside


WINTER_PAL = [[60, 0, 100], [0, 50, 200], [100, 150, 255], [150, 220, 200], [200, 255, 150]]
SUMMER_PAL = [[200, 255, 150], [255, 255, 150], [255, 180, 50], [255, 50, 50], [180, 0, 0]]
SNOW_PAL = [[240, 250, 255], [150, 200, 255], [0, 50, 200], [0, 0, 100]]
WIND_PAL = [[240, 255, 200], [255, 220, 100], [255, 100, 50], [200, 0, 0]]


def get_color(val, palette, min_v, max_v):
    ratio = max(0.0, min(1.0, (val - min_v) / (max_v - min_v) if max_v != min_v else 0.5))
    n_colors = len(palette)
    if ratio == 1.0: return palette[-1] + [160]
    scaled_ratio = ratio * (n_colors - 1)
    idx = int(scaled_ratio)
    t = scaled_ratio - idx
    c1, c2 = palette[idx], palette[idx + 1]
    return [int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t), int(c1[2] + (c2[2] - c1[2]) * t), 160]


@st.cache_data
def generate_zone_grid(df_anchors, mode):
    if mode == "Зимние температуры (t_min)":
        col, pal, mn, mx = "t_min", WINTER_PAL, -55.0, -15.0
    elif mode == "Летние температуры (t_max)":
        col, pal, mn, mx = "t_max", SUMMER_PAL, 15.0, 35.0
    elif mode == "Снеговые районы":
        col, pal, mn, mx = "snow", SNOW_PAL, 1.0, 6.0
    else:
        col, pal, mn, mx = "wind", WIND_PAL, 1.0, 6.0

    step_lat, step_lon = 0.5, 1.0
    dlat, dlon = step_lat / 2, step_lon / 2
    lats, lons = np.arange(41, 80, step_lat), np.arange(19, 191, step_lon)
    anchor_lats, anchor_lons, anchor_vals = df_anchors['lat'].values, df_anchors['lon'].values, df_anchors[col].values
    grid_data = []

    for lat in lats:
        for lon in lons:
            if not is_in_russia(lat, lon): continue
            dist_sq = ((lon - anchor_lons) * math.cos(math.radians(lat))) ** 2 + (lat - anchor_lats) ** 2 + 0.5
            weights = 1.0 / (dist_sq ** 2)
            val = np.sum(weights * anchor_vals) / np.sum(weights)
            c = get_color(val, pal, mn, mx)
            lon_real = lon if lon <= 180 else lon - 360
            grid_data.append({'polygon': [[lon_real - dlon, lat - dlat], [lon_real + dlon, lat - dlat],
                                          [lon_real + dlon, lat + dlat], [lon_real - dlon, lat + dlat]], 'color': c})
    return pd.DataFrame(grid_data)


def get_next_thickness(calc_thickness, min_thickness=12.0):
    target = max(calc_thickness, min_thickness)
    for t in SORTAMENT:
        if t >= target: return t
    return math.ceil(target)


def fmt(val):
    """Интеллектуальное округление до значащих цифр"""
    try:
        val = float(val)
        if val == 0: return "0"
        abs_val = abs(val)
        if abs_val < 0.0001:
            res = f"{val:.8f}"
        elif abs_val < 0.01:
            res = f"{val:.6f}"
        elif abs_val < 1:
            res = f"{val:.4f}"
        elif abs_val < 10:
            res = f"{val:.3f}"
        else:
            res = f"{val:.2f}"
        res = res.rstrip('0').rstrip('.')
        return res.replace('.', ',')
    except:
        return str(val)


# --- ИНИЦИАЛИЗАЦИЯ И ЖЕСТКОЕ СОХРАНЕНИЕ ВСЕХ ПЕРЕМЕННЫХ В ПАМЯТЬ ---
state_defaults = {
    'product_type': "Нефть", 't_product': 5.0,
    'D_H': 1020.0, 'P': 6.0, 'n_p': 1.1,
    'R1_n': 490.0, 'R2_n': 345.0,
    'm': 0.990, 'k1': 1.34, 'k2': 1.15, 'k_H': 1.100,
    'delta_n': 11.0, 'delta_t': 50.0,
    'E': 206000.0, 'alpha': 0.000012, 'mu': 0.3,
    'gamma_gr': 17000.0, 'phi_deg': 36.0, 'c_gr': 0.0, 'k_0': 5.0, 'k_i': 5.0,
    'h0': 1.2, 'n_gr': 0.95, 'h1': 1.026, 'H': 2.2, 'b': 0.85, 'alpha_H': 39.0,
    'rho_ins': 1750.0, 'delta_ins': 3.0, 'rho_gor': 1400.0, 'f_gr': 0.3, 'k_sdv': 1.25,
    'rho_v': 1400.0, 'alpha_v': 50.0, 'k_np': 1.25, 'q_gor_input': 84689.4
}
for k, v in state_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
    if f"temp_{k}" not in st.session_state:
        st.session_state[f"temp_{k}"] = v


def update_val(key):
    st.session_state[key] = st.session_state[f"temp_{key}"]


def update_t_product():
    st.session_state.product_type = st.session_state.temp_product_type
    st.session_state.t_product = 5.0 if st.session_state.product_type == "Нефть" else 6.0
    st.session_state.temp_t_product = st.session_state.t_product


st.sidebar.title("🛢️ Навигация РГР")
page = st.sidebar.radio("Меню:", [
    "1. Климатология",
    "2. 8.1: Толщина стенки",
    "3. 8.2: Прочность по деформациям",
    "4. 8.3: Продольная устойчивость",
    "5. 8.4: Устойчивость в насыпи (Прямой)",
    "6. 8.5: Горизонтальный поворот",
    "7. 8.6: Вертикальный поворот",
    "8. 8.7: Продольные перемещения",
    "9. Итоговый отчет"
])
st.sidebar.markdown("---")
st.sidebar.info(f"**Толщина стенки (δ_н):**\n\n{fmt(st.session_state.delta_n)} мм")


def find_image(base_name):
    for ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']:
        if os.path.exists(base_name + ext): return base_name + ext
    return None


def check_strength(delta, dt):
    D_vn = st.session_state.D_H - 2 * delta
    sigma_kc_n = st.session_state.P * D_vn / (2 * delta)
    sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n
    sigma_pr_n = -st.session_state.alpha * st.session_state.E * dt + st.session_state.mu * sigma_kc_n
    if sigma_pr_n < 0:
        under_sqrt = 1 - 0.75 * (sigma_kc_n / sigma_kc_allow) ** 2
        if under_sqrt < 0: return False, sigma_kc_n, sigma_kc_allow, sigma_pr_n, 0, 0
        psi_1 = math.sqrt(under_sqrt) - 0.5 * (sigma_kc_n / sigma_kc_allow)
    else:
        psi_1 = 1.0
    sigma_pr_allow = psi_1 * sigma_kc_allow
    is_ok = (sigma_kc_n <= sigma_kc_allow) and (abs(sigma_pr_n) <= sigma_pr_allow)
    return is_ok, sigma_kc_n, sigma_kc_allow, sigma_pr_n, psi_1, sigma_pr_allow


# ==============================================================================
# 1. КЛИМАТОЛОГИЯ
# ==============================================================================
if page == "1. Климатология":
    st.title("1. Расчетный температурный перепад (Δt)")
    st.markdown(
        "<div class='info-text'>В данном разделе определяется разница между эксплуатационной температурой и температурой при сварке. Моделирование температурных зон выполняется методом IDW-интерполяции по границам РФ.</div>",
        unsafe_allow_html=True)

    col_map1, col_map2 = st.columns([1, 1])
    with col_map1:
        st.subheader("Выбор района")
        region = st.selectbox("Город из базы:", ["Свой город"] + list(CLIMATE_DATA.keys()))
        if region == "Свой город":
            c_c1, c_c2 = st.columns(2)
            custom_name = c_c1.text_input("Название", value="Сургут-Уфа")
            t_max_val = c_c2.number_input("t_max, °C", value=30.0)
            t_min_val = c_c1.number_input("t_min, °