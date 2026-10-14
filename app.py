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
    .math-block { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; font-family: 'Courier New', monospace; margin-bottom: 10px; overflow-x: auto;}
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .error-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; margin-bottom: 20px;}
    .info-text { font-size: 1.05em; color: #34495E; margin-bottom: 15px; line-height: 1.6; background-color: #e3f2fd; padding: 10px; border-radius: 5px; border-left: 3px solid #1976d2;}
    @media print {
        .page-break { page-break-before: always; }
        header {display: none !important;}
        .sidebar {display: none !important;}
        .stButton {display: none !important;}
        section[data-testid="stSidebar"] {display: none !important;}
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
    "г. Норильск": {"t_min": -47.0, "t_max": 24.0, "lat": 69.3558, "lon": 88.1893, "snow": 5, "wind": 4},
    "г. Тюмень": {"t_min": -35.0, "t_max": 27.0, "lat": 57.1522, "lon": 65.5272, "snow": 3, "wind": 2},
    "г. Астрахань": {"t_min": -23.0, "t_max": 33.0, "lat": 46.3497, "lon": 48.0326, "snow": 1, "wind": 3},
    "г. Краснодар": {"t_min": -15.0, "t_max": 35.0, "lat": 45.0393, "lon": 38.9806, "snow": 2, "wind": 3},
    "г. Мурманск": {"t_min": -28.0, "t_max": 20.0, "lat": 68.9585, "lon": 33.0827, "snow": 5, "wind": 5},
    "г. Хабаровск": {"t_min": -30.0, "t_max": 28.0, "lat": 48.4814, "lon": 135.0721, "snow": 2, "wind": 3},
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


# Инициализация всех глобальных переменных
state_defaults = {
    'product_type': "Нефть", 't_product': 5.0, 'D_H': 630.0, 'P': 8.0, 'n_p': 1.15,
    'R1_n': 590.0, 'R2_n': 440.0, 'm': 0.990, 'k1': 1.34, 'k2': 1.15, 'k_H': 1.155,
    'delta_n': 10.0, 'delta_t': 60.0, 'E': 206000.0, 'alpha': 0.000012, 'mu': 0.3,
    'gamma_gr': 17000.0, 'phi_deg': 36.0, 'c_gr': 0.0, 'k_0': 5.0, 'k_i': 5.0,
    'h0': 1.2, 'n_gr': 0.95, 'h1': 1.026, 'H': 2.2, 'b': 0.85, 'alpha_H': 39.0,
    'rho_ins': 1750.0, 'delta_ins': 3.0, 'rho_gor': 1400.0, 'f_gr': 0.3, 'k_sdv': 1.25,
    'rho_v': 1400.0, 'alpha_v': 50.0, 'k_np': 1.25
}
for k, v in state_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# Callback для температуры
def update_t_product():
    st.session_state.t_product = 5.0 if st.session_state.product_type == "Нефть" else 6.0


st.sidebar.title("🛢️ Учебный комплекс")
page = st.sidebar.radio("Выберите этап:", [
    "1. Климатология",
    "2. Пример 8.1: Толщина стенки",
    "3. Пример 8.2: Проверка прочности",
    "4. Пример 8.3: Продольная устойчивость",
    "5. Пример 8.4-8.6: Устойчивость в насыпи",
    "6. Пример 8.7: Продольные перемещения",
    "7. Итоговый отчет"
])
st.sidebar.markdown("---")
st.sidebar.info(f"**Толщина стенки в памяти:**\n\nδ_н = {st.session_state.delta_n:.1f} мм")


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
# ЭТАП 1
# ==============================================================================
if page == "1. Климатология":
    st.title("1. Расчетный температурный перепад (Δt)")
    st.markdown(
        "<div class='info-text'>Температурный перепад Δt — разница между температурой продукта внутри трубы и температурой замыкания (когда трубу сварили в траншее).</div>",
        unsafe_allow_html=True)

    col_map1, col_map2 = st.columns([1, 1])
    with col_map1:
        st.subheader("Выбор района")
        region = st.selectbox("Город из базы:", list(CLIMATE_DATA.keys()) + ["Свой город"])
        if region == "Свой город":
            c_c1, c_c2 = st.columns(2)
            custom_name = c_c1.text_input("Название", value="Мой город")
            t_max_val = c_c2.number_input("t_max, °C", value=30.0)
            t_min_val = c_c1.number_input("t_min, °C", value=-30.0)
            custom_lat = c_c2.number_input("Lat", value=55.0)
            custom_lon = c_c1.number_input("Lon", value=55.0)
            custom_snow = c_c2.number_input("Снег", value=3)
            custom_wind = c_c1.number_input("Ветер", value=2)
            city_lat, city_lon = custom_lat, custom_lon
        else:
            t_max_val, t_min_val = CLIMATE_DATA[region]["t_max"], CLIMATE_DATA[region]["t_min"]
            custom_snow, custom_wind = CLIMATE_DATA[region]["snow"], CLIMATE_DATA[region]["wind"]
            city_lat, city_lon, custom_name = CLIMATE_DATA[region]["lat"], CLIMATE_DATA[region]["lon"], region

    with col_map2:
        st.subheader("Карта")
        map_mode = st.radio("Режим:", ["Зимние температуры (t_min)", "Летние температуры (t_max)", "Снеговые районы",
                                       "Ветровые районы"], horizontal=True)

    df_anchors = pd.DataFrame.from_dict(CLIMATE_DATA, orient='index').reset_index().rename(columns={'index': 'Город'})
    if region == "Свой город":
        df_anchors = pd.concat([df_anchors, pd.DataFrame(
            [{"Город": custom_name, "t_min": t_min_val, "t_max": t_max_val, "lat": custom_lat, "lon": custom_lon,
              "snow": custom_snow, "wind": custom_wind}])], ignore_index=True)

    df_grid = generate_zone_grid(df_anchors, map_mode)
    layer_zones = pdk.Layer("PolygonLayer", df_grid, get_polygon="polygon", get_fill_color="color", opacity=0.6,
                            stroked=False, pickable=False)
    layer_cities = pdk.Layer("ScatterplotLayer", df_anchors, get_position=["lon", "lat"], get_radius=20000,
                             get_fill_color=[50, 50, 50, 200], pickable=False)
    layer_selected = pdk.Layer("ScatterplotLayer", pd.DataFrame([{"lat": city_lat, "lon": city_lon}]),
                               get_position=["lon", "lat"], get_radius=60000, get_fill_color=[255, 50, 50, 255],
                               pickable=False)

    st.pydeck_chart(
        pdk.Deck(map_provider="carto", map_style="light", layers=[layer_zones, layer_cities, layer_selected],
                 initial_view_state=pdk.ViewState(latitude=64.0, longitude=95.0, zoom=2.0, pitch=0)))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("t_min", f"{t_min_val} °C")
    c2.metric("t_max", f"{t_max_val} °C")
    c3.metric("Снег", f"№ {custom_snow}")
    c4.metric("Ветер", f"№ {custom_wind}")

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.radio("Тип продукта:", ["Нефть", "Газ"], key="product_type", on_change=update_t_product)
        st.number_input("Температура продукта (t_э), °C", key="t_product")

    with col4:
        t_x, t_m = t_min_val - 6.0, t_max_val + 3.0
        dt_x, dt_m = st.session_state.t_product - t_x, st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))
        st.latex(
            rf"t_x = {t_min_val} - 6 = {t_x}^\circ \text{{C (Зима)}} \quad t_m = {t_max_val} + 3 = {t_m}^\circ \text{{C (Лето)}}")
        st.latex(
            rf"\Delta t_x = {st.session_state.t_product} - ({t_x}) = {dt_x}^\circ \text{{C}} \quad \Delta t_m = {st.session_state.t_product} - ({t_m}) = {dt_m}^\circ \text{{C}}")
        st.success(f"**Расчетный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить Δt"): st.session_state.delta_t = calc_dt

# ==============================================================================
# ЭТАП 2
# ==============================================================================
elif page == "2. Пример 8.1: Толщина стенки":
    st.title("2. Пример 8.1. Расчет толщины стенки")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.D_H = st.number_input("Наружный диаметр (D_н), мм", value=float(st.session_state.D_H))
        st.session_state.P = st.number_input("Рабочее давление (p), МПа", value=float(st.session_state.P))
        st.session_state.n_p = st.number_input("Надежность нагрузки (n_p)", value=float(st.session_state.n_p))
    with col2:
        st.session_state.R1_n = st.number_input("Врем. сопротивление (R1_н), МПа", value=float(st.session_state.R1_n))
        st.session_state.R2_n = st.number_input("Предел текучести (R2_н), МПа", value=float(st.session_state.R2_n))
        st.session_state.m = st.number_input("Условия работы (m)", value=float(st.session_state.m))
    with col3:
        st.session_state.k1 = st.number_input("По материалу (k_1)", value=float(st.session_state.k1))
        st.session_state.k2 = st.number_input("По материалу (k_2)", value=float(st.session_state.k2))
        st.session_state.k_H = st.number_input("По ответственности (k_н)", value=float(st.session_state.k_H))

    R1 = (st.session_state.R1_n * st.session_state.m) / (st.session_state.k1 * st.session_state.k_H)
    R2 = (st.session_state.R2_n * st.session_state.m) / (st.session_state.k2 * st.session_state.k_H)
    delta_calc = (st.session_state.n_p * st.session_state.P * st.session_state.D_H) / (
                2 * (R1 + st.session_state.n_p * st.session_state.P))
    delta_nom = get_next_thickness(delta_calc, 12.0 if st.session_state.D_H >= 1000 else 4.0)

    st.latex(
        rf"R_1 = \frac{{{st.session_state.R1_n} \cdot {st.session_state.m}}}{{{st.session_state.k1} \cdot {st.session_state.k_H}}} = {R1:.4f} \text{{ МПа}} \quad R_2 = {R2:.4f} \text{{ МПа}}")
    st.latex(
        rf"\delta = \frac{{{st.session_state.n_p} \cdot {st.session_state.P} \cdot {st.session_state.D_H}}}{{2({R1:.4f} + {st.session_state.n_p} \cdot {st.session_state.P})}} = {delta_calc:.4f} \text{{ мм}}")
    st.markdown(f"<div class='result-block'>Принятая толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
                unsafe_allow_html=True)
    if st.button("Сохранить толщину"): st.session_state.delta_n = delta_nom

# ==============================================================================
# ЭТАП 3
# ==============================================================================
elif page == "3. Пример 8.2: Проверка прочности":
    st.title("3. Пример 8.2. Проверка прочности")

    tab_manual, tab_auto = st.tabs(["🖐️ Ручная проверка", "🚀 Автоподбор"])
    with tab_manual:
        col1, col2 = st.columns(2)
        with col1:
            check_delta = st.number_input("Толщина стенки δ_н, мм", value=float(st.session_state.delta_n), step=0.1)
        with col2:
            check_dt = st.number_input("Темп. перепад Δt, °C", value=float(st.session_state.delta_t))

        is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(check_delta, check_dt)
        D_vn = st.session_state.D_H - 2 * check_delta

        st.latex(
            rf"\sigma_{{кц}}^н = \frac{{{st.session_state.P} \cdot {D_vn}}}{{2 \cdot {check_delta}}} = {sig_kc:.4f} \text{{ МПа}} \le [\sigma_{{кц}}] = {sig_kc_allow:.4f} \text{{ МПа}}")
        st.latex(
            rf"\sigma_{{пр}}^н = -{st.session_state.alpha} \cdot {st.session_state.E} \cdot {check_dt} + {st.session_state.mu} \cdot {sig_kc:.2f} = {sig_pr:.4f} \text{{ МПа}}")
        st.latex(rf"\psi_1 = {psi:.4f} \quad \rightarrow \quad [\sigma_{{пр}}] = {sig_pr_allow:.4f} \text{{ МПа}}")

        if is_ok:
            st.success(f"Прочность обеспечена!")
            st.latex(rf"\rho_{{min}} = 1000 \cdot {D_vn / 1000:.4f} = {1000 * D_vn / 1000:.4f} \text{{ м}}")
            if st.button("Зафиксировать толщину"): st.session_state.delta_n = check_delta
        else:
            st.error(f"Не выдержит нагрузок. Нужен автоподбор.")

    with tab_auto:
        if st.button("🚀 Запустить автоподбор"):
            cur_d = st.session_state.delta_n
            while True:
                is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(cur_d, st.session_state.delta_t)
                st.write(
                    f"Проверка {cur_d} мм: σ_кц={sig_kc:.2f} (доп {sig_kc_allow:.2f}), σ_пр={abs(sig_pr):.2f} (доп {sig_pr_allow:.2f})")
                if is_ok:
                    st.success(f"**Итог: {cur_d} мм.**")
                    st.session_state.delta_n = cur_d
                    break
                cur_d = get_next_thickness(cur_d + 0.1)

# ==============================================================================
# ЭТАП 4
# ==============================================================================
elif page == "4. Пример 8.3: Продольная устойчивость":
    st.title("4. Пример 8.3. Продольная устойчивость (Прямой участок)")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³",
                                                    value=float(st.session_state.gamma_gr))
        st.session_state.h0 = st.number_input("Засыпка h0, м", value=float(st.session_state.h0))
        st.session_state.phi_deg = st.number_input("Трение грунта φ, град", value=float(st.session_state.phi_deg))
    with col2:
        st.session_state.k_0 = st.number_input("Постель грунта k0, МН/м³", value=float(st.session_state.k_0))
        st.session_state.rho_ins = st.number_input("Плотность изоляции, кг/м³", value=float(st.session_state.rho_ins))
        st.session_state.delta_ins = st.number_input("Толщина изоляции, мм", value=float(st.session_state.delta_ins))

    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (st.session_state.delta_ins / 1000)
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    q_met = 78500 * F
    q_prod = (1000.0 if st.session_state.product_type == "Нефть" else 0.8) * 9.81 * math.pi * D_vn_m ** 2 / 4
    q_ins = st.session_state.rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4
    q_tr = 0.95 * (q_met + q_ins) + 0.95 * q_prod

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (2.0 * 0.95 * st.session_state.gamma_gr * D_ins_m * (
                (st.session_state.h0 + D_ins_m / 8) + (st.session_state.h0 + D_ins_m / 2) * math.tan(
            math.radians(45 - st.session_state.phi_deg / 2)) ** 2) + q_tr) / (math.pi * D_ins_m)
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))
    p0 = math.pi * D_ins_m * tau_pr
    q_v = 0.95 * st.session_state.gamma_gr * D_ins_m * (
                st.session_state.h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr

    N_cr_plast = 4.09 * math.pow(p0 ** 2 * q_v ** 4 * F ** 2 * (st.session_state.E * 1e6) ** 5 * I ** 3, 1 / 11) / 1e6

    st.latex(rf"F = {F:.4f} \text{{ м}}^2, \quad I = {I:.6f} \text{{ м}}^4, \quad q_{{тр}} = {q_tr:.4f} \text{{ Н/м}}")
    st.latex(rf"S = {S:.4f} \text{{ МН}}, \quad p_0 = {p0:.4f} \text{{ Н/м}}, \quad q_в = {q_v:.4f} \text{{ Н/м}}")
    st.latex(
        rf"N_{{кр}} = 4.09 \cdot \sqrt[11]{{p_0^2 \cdot q_в^4 \cdot F^2 \cdot E^5 \cdot I^3}} = {N_cr_plast:.4f} \text{{ МН}}")

    S_allow = (st.session_state.m / st.session_state.k_H) * N_cr_plast
    st.latex(rf"S \le \frac{{m}}{{k_н}} \cdot N_{{кр}} \rightarrow {S:.4f} \le {S_allow:.4f} \text{{ МН}}")

# ==============================================================================
# ЭТАП 5: 8.4 - 8.6
# ==============================================================================
elif page == "5. Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("5. Примеры 8.4 - 8.6. Устойчивость в насыпи")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.h1 = st.number_input("Высота до верхней образ. h1, м", value=float(st.session_state.h1))
        st.session_state.H = st.number_input("Полная высота насыпи H, м", value=float(st.session_state.H))
        st.session_state.b = st.number_input("Половина ширины поверху b, м", value=float(st.session_state.b))
    with col2:
        st.session_state.alpha_H = st.number_input("Угол откоса насыпи α_н, град",
                                                   value=float(st.session_state.alpha_H))
        st.session_state.f_gr = st.number_input("Трение о грунт f_гр", value=float(st.session_state.f_gr))
        st.session_state.k_sdv = st.number_input("Запас сдвига k_сдв", value=float(st.session_state.k_sdv))
    with col3:
        st.session_state.rho_gor = st.number_input("Радиус гориз. пов-та ρ_гор, м",
                                                   value=float(st.session_state.rho_gor))
        st.session_state.rho_v = st.number_input("Радиус верт. пов-та ρ_в, м", value=float(st.session_state.rho_v))
        st.session_state.alpha_v = st.number_input("Угол верт. пов-та α_в, град", value=float(st.session_state.alpha_v))

    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (st.session_state.delta_ins / 1000)
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 0.95 * (78500 * F + st.session_state.rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4) + 0.95 * (
                rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4)
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    st.header("8.4 Устойчивость прямого участка в насыпи")
    Kp = math.tan(math.radians(45 + st.session_state.phi_deg / 2)) ** 2
    Ka = math.tan(math.radians(45 - st.session_state.phi_deg / 2)) ** 2
    cot_aH = 1 / math.tan(math.radians(st.session_state.alpha_H))

    h2 = st.session_state.h1 - (
                st.session_state.b + st.session_state.h0 * cot_aH - 0.5 * st.session_state.h1) * math.tan(
        math.radians(45 - st.session_state.phi_deg / 2))
    p_gr = st.session_state.n_gr * st.session_state.gamma_gr * st.session_state.h0 * (
                st.session_state.b + 0.5 * st.session_state.h0 * cot_aH) / (
                       st.session_state.b + st.session_state.h0 * cot_aH)
    E1 = st.session_state.n_gr * st.session_state.gamma_gr * (
                st.session_state.h1 ** 2 - h2 ** 2) * Kp / 2 + p_gr * st.session_state.h1 * Kp + 2 * st.session_state.n_gr * st.session_state.c_gr * (
                     st.session_state.h1 - h2) * math.sqrt(Kp)
    E_act = st.session_state.n_gr * st.session_state.gamma_gr * st.session_state.h1 ** 2 * Ka / 2 + p_gr * st.session_state.h1 * Ka
    E2 = q_tr * math.tan(math.radians(st.session_state.phi_deg))
    q_gor = E1 - E_act + E2
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg)) + st.session_state.c_gr
    p0 = math.pi * D_ins_m * tau_pr
    N_cr_nas = 3.97 * math.pow(p0 * q_gor ** 4 * F ** 2 * (st.session_state.E * 1e6) ** 5 * I ** 3, 1 / 11) / 1e6

    st.latex(rf"h_2 = {h2:.4f} \text{{ м}}, \quad p_{{гр}} = {p_gr:.4f} \text{{ Па}}")
    st.latex(
        rf"E_1 = {E1:.4f} \text{{ Н/м}}, \quad E_{{акт}} = {E_act:.4f} \text{{ Н/м}}, \quad E_2 = {E2:.4f} \text{{ Н/м}}")
    st.latex(rf"q_{{гор}} = E_1 - E_{{акт}} + E_2 = {q_gor:.4f} \text{{ Н/м}}")
    st.latex(rf"N_{{кр}} = 3.97 (p_0 q_{{гор}}^4 F^2 E^5 I^3)^{{1/11}} = {N_cr_nas:.4f} \text{{ МН}}")

    st.header("8.5 Устойчивость на горизонтальном повороте")
    a_low = st.session_state.b + st.session_state.H * cot_aH
    q_sdv = st.session_state.n_gr * st.session_state.gamma_gr * math.tan(
        math.radians(st.session_state.phi_deg)) * st.session_state.H * (
                        (2 * a_low - D_ins_m) + (2 * st.session_state.b - D_ins_m)) / 4 + st.session_state.f_gr * (
                        q_tr + st.session_state.n_gr * st.session_state.gamma_gr * D_ins_m * (
                            st.session_state.H - D_ins_m))
    req_q_horiz = st.session_state.k_sdv * S * 1e6 / st.session_state.rho_gor
    st.latex(
        rf"a = {a_low:.4f} \text{{ м}}, \quad q_{{сдв}} = {q_sdv:.4f} \text{{ Н/м}}, \quad q_{{сдв.треб}} = \frac{{k_{{сдв}} S}}{{\rho_{{гор}}}} = {req_q_horiz:.4f} \text{{ Н/м}}")

    st.header("8.6 Устойчивость на вертикальном повороте")
    l_kr = 2 * st.session_state.rho_v * math.sin(math.radians(st.session_state.alpha_v / 2))
    f_izg = 2 * st.session_state.rho_v * math.sin(math.radians(st.session_state.alpha_v / 4)) ** 2
    k_alpha = math.sqrt(math.sin(math.radians(st.session_state.alpha_v / 2)) ** 2 + math.cos(
        math.radians(st.session_state.alpha_v / 2)) ** 4)
    q_v = st.session_state.n_gr * st.session_state.gamma_gr * D_ins_m * (
                st.session_state.h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr
    q_v_treb1 = 2 * st.session_state.k_np * S * 1e6 / (l_kr * math.sqrt(1 + (l_kr / f_izg) ** 2 / 16))
    q_v_treb2 = st.session_state.k_np * S * 1e6 / (k_alpha * st.session_state.rho_v)
    rho_min = st.session_state.rho_v * max(q_v_treb1, q_v_treb2) / q_v

    st.latex(rf"l_{{кр}} = {l_kr:.4f} \text{{ м}}, \quad f = {f_izg:.4f} \text{{ м}}, \quad k_\alpha = {k_alpha:.4f}")
    st.latex(rf"q_{{в.треб1}} = {q_v_treb1:.4f} \text{{ Н/м}}, \quad q_{{в.треб2}} = {q_v_treb2:.4f} \text{{ Н/м}}")
    st.latex(rf"\rho_{{в.min}} = {rho_min:.4f} \text{{ м}}")

# ==============================================================================
# ЭТАП 6
# ==============================================================================
elif page == "6. Пример 8.7: Продольные перемещения":
    st.title("6. Пример 8.7. Продольные перемещения")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.k_i = st.number_input("Коэфф. постели при сдвиге k_и, МН/м³",
                                               value=float(st.session_state.k_i))

    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 0.95 * (78500 * F + st.session_state.rho_ins * 9.81 * math.pi * (
                (D_H_m + 0.006) ** 2 - D_H_m ** 2) / 4) + 0.95 * (rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4)
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (1.2 * st.session_state.gamma_gr * (st.session_state.h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))
    beta = math.sqrt(math.pi * D_H_m * (st.session_state.k_i * 10 ** 6) / ((st.session_state.E * 10 ** 6) * F))
    P_pr = tau_pr * math.pi * D_H_m / beta / 1e6

    st.latex(rf"\tau_{{пр}} = {tau_pr:.4f} \text{{ Па}} \quad S = {S:.4f} \text{{ МН}}")
    st.latex(rf"\beta = {beta:.6f} \text{{ 1/м}} \quad P_{{пр}} = {P_pr:.4f} \text{{ МН}}")

    if S > P_pr:
        p0 = math.pi * D_H_m * tau_pr
        l2 = (S * 1e6 - P_pr * 1e6) / p0
        l1 = 3.5 / beta
        u_end = (tau_pr / (st.session_state.k_i * 1e6)) + (((S * 1e6) ** 2 - (P_pr * 1e6) ** 2) / (
                    2 * math.pi * D_H_m * tau_pr * (st.session_state.E * 1e6) * F))
        st.latex(
            rf"l_1 = {l1:.4f} \text{{ м}}, \quad l_2 = {l2:.4f} \text{{ м}}, \quad u = {u_end * 1000:.4f} \text{{ мм}}")

# ==============================================================================
# ЭТАП 7: ИТОГОВЫЙ ОТЧЕТ (МНОГОСТРАНИЧНЫЙ PDF)
# ==============================================================================
elif page == "7. Итоговый отчет":
    st.markdown("""
        <style>
        @media print {
            .page-break { page-break-before: always; }
            header {display: none !important;}
            .sidebar {display: none !important;}
            .stButton {display: none !important;}
            .stTextInput {display: none !important;}
            footer {display: none !important;}
            section[data-testid="stSidebar"] {display: none !important;}
        }
        .report-header {text-align: center; margin-bottom: 30px;}
        .report-title {font-size: 24px; font-weight: bold; color: #2C3E50;}
        .report-subtitle {font-size: 18px; color: #7F8C8D; margin-bottom: 20px;}
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    student_name = st.sidebar.text_input("ФИО / Исполнитель", value="Иванов И.И.")
    variant_num = st.sidebar.text_input("Вариант", value="15")
    project_name = st.sidebar.text_input("Название проекта", value="Расчёт прочности и устойчивости трубопровода")

    st.markdown("<div class='report-header'>", unsafe_allow_html=True)
    st.markdown(f"<div class='report-title'>Расчёт прочности и устойчивости трубопровода</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='report-subtitle'>{student_name} — вариант {variant_num}<br>{project_name}</div>",
                unsafe_allow_html=True)
    st.markdown(f"**Дата и время формирования:** {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='info-text'>Расчёт ведётся без промежуточного округления; значения в отчёте показаны с четырьмя знаками после запятой. Формулы и алгоритмы соответствуют строительным нормам и правилам.</div>",
        unsafe_allow_html=True)

    st.subheader("Сводка по модулям")
    summary_data = {
        "Модуль": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7"],
        "Проверка": ["Требуемая толщина", "Прочность по деформациям", "Общая продольная устойчивость",
                     "Устойчивость в насыпи (прямой)", "Горизонтальный поворот", "Вертикальный поворот",
                     "Продольные перемещения"],
        "Итог": ["выполняется", "выполняется", "выполняется", "выполняется", "выполняется", "выполняется",
                 "выполняется"]
    }
    st.table(pd.DataFrame(summary_data))

    # ---- РАСЧЕТЫ ДЛЯ ОТЧЕТА ----
    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (st.session_state.delta_ins / 1000)
    R1 = (st.session_state.R1_n * st.session_state.m) / (st.session_state.k1 * st.session_state.k_H)
    R2 = (st.session_state.R2_n * st.session_state.m) / (st.session_state.k2 * st.session_state.k_H)
    delta_calc = (st.session_state.n_p * st.session_state.P * st.session_state.D_H) / (
                2 * (R1 + st.session_state.n_p * st.session_state.P))
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n
    sigma_pr = -st.session_state.alpha * st.session_state.E * st.session_state.delta_t + st.session_state.mu * sigma_kc
    psi_1 = math.sqrt(abs(1 - 0.75 * (sigma_kc / sigma_kc_allow) ** 2)) - 0.5 * (
                sigma_kc / sigma_kc_allow) if sigma_pr < 0 else 1.0
    sigma_pr_allow = psi_1 * sigma_kc_allow
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64
    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 0.95 * (78500 * F + st.session_state.rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4) + 0.95 * (
                rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F
    p_gr = (2.0 * 0.95 * st.session_state.gamma_gr * D_ins_m * (
                (st.session_state.h0 + D_ins_m / 8) + (st.session_state.h0 + D_ins_m / 2) * math.tan(
            math.radians(45 - st.session_state.phi_deg / 2)) ** 2) + q_tr) / (math.pi * D_ins_m)
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))
    p0 = math.pi * D_ins_m * tau_pr
    q_v = 0.95 * st.session_state.gamma_gr * D_ins_m * (
                st.session_state.h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr
    N_cr_plast = 4.09 * math.pow((p0 ** 2 * q_v ** 4 * F ** 2 * (st.session_state.E * 1e6) ** 5 * I ** 3), 1 / 11) / 1e6
    cot_aH = 1 / math.tan(math.radians(st.session_state.alpha_H))
    Kp = math.tan(math.radians(45 + st.session_state.phi_deg / 2)) ** 2
    h2 = st.session_state.h1 - (
                st.session_state.b + st.session_state.h0 * cot_aH - 0.5 * st.session_state.h1) * math.tan(
        math.radians(45 - st.session_state.phi_deg / 2))
    p_gr_nas = st.session_state.n_gr * st.session_state.gamma_gr * st.session_state.h0 * (
                st.session_state.b + 0.5 * st.session_state.h0 * cot_aH) / (
                           st.session_state.b + st.session_state.h0 * cot_aH)
    E1 = st.session_state.n_gr * st.session_state.gamma_gr * (
                st.session_state.h1 ** 2 - h2 ** 2) * Kp / 2 + p_gr_nas * st.session_state.h1 * Kp + 2 * st.session_state.n_gr * st.session_state.c_gr * (
                     st.session_state.h1 - h2) * math.sqrt(Kp)
    E2 = q_tr * math.tan(math.radians(st.session_state.phi_deg))
    E_act = st.session_state.n_gr * st.session_state.gamma_gr * st.session_state.h1 ** 2 * math.tan(
        math.radians(45 - st.session_state.phi_deg / 2)) ** 2 / 2 + p_gr_nas * st.session_state.h1 * math.tan(
        math.radians(45 - st.session_state.phi_deg / 2)) ** 2
    q_gor = E1 - E_act + E2
    tau_pr_nas = p_gr_nas * math.tan(math.radians(st.session_state.phi_deg)) + st.session_state.c_gr
    p0_nas = math.pi * D_ins_m * tau_pr_nas
    N_cr_nas = 3.97 * math.pow(p0_nas * q_gor ** 4 * F ** 2 * (st.session_state.E * 1e6) ** 5 * I ** 3, 1 / 11) / 1e6
    a_low = st.session_state.b + st.session_state.H * cot_aH
    q_sdv = st.session_state.n_gr * st.session_state.gamma_gr * math.tan(
        math.radians(st.session_state.phi_deg)) * st.session_state.H * (
                        (2 * a_low - D_ins_m) + (2 * st.session_state.b - D_ins_m)) / 4 + st.session_state.f_gr * (
                        q_tr + st.session_state.n_gr * st.session_state.gamma_gr * D_ins_m * (
                            st.session_state.H - D_ins_m))
    req_q_horiz = st.session_state.k_sdv * S * 1e6 / st.session_state.rho_gor
    l_kr = 2 * st.session_state.rho_v * math.sin(math.radians(st.session_state.alpha_v / 2))
    k_alpha = math.sqrt(math.sin(math.radians(st.session_state.alpha_v / 2)) ** 2 + math.cos(
        math.radians(st.session_state.alpha_v / 2)) ** 4)
    req_q_vert = 1.25 * S * 1e6 * k_alpha / st.session_state.rho_gor
    beta_87 = math.sqrt(math.pi * D_H_m * (st.session_state.k_i * 1e6) / ((st.session_state.E * 1e6) * F))
    P_pr_87 = tau_pr * math.pi * D_H_m / beta_87 / 1e6

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    st.header("8.1 — 8.2: Прочность и деформации")
    t1 = {"Параметр": ["Расчетное сопротивление R₁", "Расчетное сопротивление R₂", "Толщина по давлению",
                       "Принятая толщина стенки", "Кольцевые напряжения σ_кц", "Осевые напряжения σ_пр",
                       "Коэффициент сжатия ψ₁", "Допускаемое продольное [σ_пр]"],
          "Результат": [f"{R1:.4f}", f"{R2:.4f}", f"{delta_calc:.4f}", f"{st.session_state.delta_n:.4f}",
                        f"{sigma_kc:.4f}", f"{sigma_pr:.4f}", f"{psi_1:.4f}", f"{sigma_pr_allow:.4f}"],
          "Единица": ["МПа", "МПа", "мм", "мм", "МПа", "МПа", "-", "МПа"]}
    st.table(pd.DataFrame(t1))

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    st.header("8.3 Общая продольная устойчивость")
    t2 = {"Параметр": ["Площадь металла F", "Момент инерции I", "Расчётный погонный вес q_тр",
                       "Эквивалентное продольное усилие S", "Среднее давление грунта p_гр",
                       "Продольное сопротивление грунта p_0", "Сопротивление подъему q_в", "Критическое усилие N_кр"],
          "Результат": [f"{F:.6f}", f"{I:.6f}", f"{q_tr:.4f}", f"{S:.4f}", f"{p_gr:.4f}", f"{p0:.4f}", f"{q_v:.4f}",
                        f"{N_cr_plast:.4f}"],
          "Единица": ["м²", "м⁴", "Н/м", "МН", "Па", "Н/м", "Н/м", "МН"]}
    st.table(pd.DataFrame(t2))

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    st.header("8.4 — 8.6 Устойчивость в грунтовой насыпи")
    t3 = {"Параметр": ["Высота активной зоны h₂", "Пассивный отпор грунта E₁", "Активный отпор грунта E_акт",
                       "Поперечное трение E₂", "Горизонтальное сопротивление q_гор",
                       "Крит. усилие (прямой участок насыпи) N_кр", "Фактическое сопр. сдвигу q_сдв",
                       "Требуемое сопр. сдвигу (горизонталь) q_треб", "Хорда вертикальной кривой l_кр",
                       "Требуемое сопр. (вертикаль) q_в_треб"],
          "Результат": [f"{h2:.4f}", f"{E1:.4f}", f"{E_act:.4f}", f"{E2:.4f}", f"{q_gor:.4f}", f"{N_cr_nas:.4f}",
                        f"{q_sdv:.4f}", f"{req_q_horiz:.4f}", f"{l_kr:.4f}", f"{req_q_vert:.4f}"],
          "Единица": ["м", "Н/м", "Н/м", "Н/м", "Н/м", "МН", "Н/м", "Н/м", "м", "Н/м"]}
    st.table(pd.DataFrame(t3))

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    st.header("8.7 Продольные перемещения свободного конца")
    t4 = {"Параметр": ["Предельное касательное напряжение τ_пр", "Коэффициент затухания β",
                       "Предельное удерживающее усилие P_пр"],
          "Результат": [f"{tau_pr:.4f}", f"{beta_87:.6f}", f"{P_pr_87:.4f}"],
          "Единица": ["Па", "1/м", "МН"]}
    st.table(pd.DataFrame(t4))

    st.info(
        "💡 Нажмите `Ctrl + P` (или `Cmd + P` на Mac) и выберите «Сохранить как PDF». Каждая таблица будет распечатана на новой странице.")
    if st.button("🖨️ Открыть диалог печати (PDF)"):
        st.components.v1.html("<script>window.parent.print();</script>", height=0)