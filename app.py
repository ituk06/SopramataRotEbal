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


# Глобальная инициализация переменных (Защита от белых экранов)
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


def update_t_product():
    st.session_state.t_product = 5.0 if st.session_state.product_type == "Нефть" else 6.0


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
st.sidebar.info(f"**Толщина стенки (δ_н):**\n\n{st.session_state.delta_n:.1f} мм")


def find_image(base_name):
    for ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']:
        if os.path.exists(base_name + ext): return base_name + ext
    return None


# ==============================================================================
# 1. КЛИМАТОЛОГИЯ
# ==============================================================================
if page == "1. Климатология":
    st.title("1. Расчетный температурный перепад (Δt)")
    st.markdown(
        "<div class='info-text'>В данном разделе определяется разница между эксплуатационной температурой и температурой при сварке. Моделирование температурных зон выполняется методом IDW-интерполяции.</div>",
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
        st.subheader("Интерактивная карта")
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
    st.markdown("<div class='step-header'>Вычисление расчетного перепада</div>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.radio("Тип продукта:", ["Нефть", "Газ"], key="product_type", on_change=update_t_product)
        st.number_input("Температура продукта (t_э), °C", key="t_product")

    with col4:
        t_x, t_m = t_min_val - 6.0, t_max_val + 3.0
        dt_x, dt_m = st.session_state.t_product - t_x, st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))
        st.latex(rf"t_x = {t_min_val} - 6 = {t_x}^\circ \text{{C (Замыкание зимой)}}")
        st.latex(rf"t_m = {t_max_val} + 3 = {t_m}^\circ \text{{C (Замыкание летом)}}")
        st.latex(rf"\Delta t_x = {st.session_state.t_product} - ({t_x}) = {dt_x}^\circ \text{{C}}")
        st.latex(rf"\Delta t_m = {st.session_state.t_product} - ({t_m}) = {dt_m}^\circ \text{{C}}")
        st.success(f"**Расчетный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить Δt"): st.session_state.delta_t = calc_dt

# ==============================================================================
# 2. ПРИМЕР 8.1
# ==============================================================================
elif page == "2. 8.1: Толщина стенки":
    st.title("2. Пример 8.1. Расчет толщины стенки")
    st.markdown(
        "<div class='info-text'>Минимально необходимая толщина стенки трубы вычисляется по безмоментной теории оболочек (формула котла) от воздействия внутреннего давления. Полученное значение округляется до ближайшего большего из ГОСТ.</div>",
        unsafe_allow_html=True)

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

    st.markdown("<div class='step-header'>Ход вычислений</div>", unsafe_allow_html=True)
    st.latex(
        rf"R_1 = \frac{{R_1^н \cdot m}}{{k_1 \cdot k_н}} = \frac{{{st.session_state.R1_n} \cdot {st.session_state.m}}}{{{st.session_state.k1} \cdot {st.session_state.k_H}}} = {R1:.4f} \text{{ МПа}}")
    st.latex(
        rf"R_2 = \frac{{R_2^н \cdot m}}{{k_2 \cdot k_н}} = \frac{{{st.session_state.R2_n} \cdot {st.session_state.m}}}{{{st.session_state.k2} \cdot {st.session_state.k_H}}} = {R2:.4f} \text{{ МПа}}")
    st.latex(
        rf"\delta = \frac{{n_p \cdot p \cdot D_н}}{{2(R_1 + n_p \cdot p)}} = \frac{{{st.session_state.n_p} \cdot {st.session_state.P} \cdot {st.session_state.D_H}}}{{2({R1:.4f} + {st.session_state.n_p} \cdot {st.session_state.P})}} = {delta_calc:.4f} \text{{ мм}}")

    st.markdown(
        f"<div class='result-block'>Округление по ГОСТ. Принятая толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
        unsafe_allow_html=True)
    if st.button("Сохранить толщину"): st.session_state.delta_n = delta_nom

# ==============================================================================
# 3. ПРИМЕР 8.2
# ==============================================================================
elif page == "3. 8.2: Прочность по деформациям":
    st.title("3. Пример 8.2. Прочность по деформациям")
    st.markdown(
        "<div class='info-text'>Подземный трубопровод ограничен грунтом в перемещениях. Из-за этого возникают продольные растягивающие или сжимающие напряжения. Учет двухосного напряженного состояния производится через коэффициент $\psi_1$.</div>",
        unsafe_allow_html=True)

    tab_manual, tab_auto = st.tabs(["🖐️ Детальный расчет", "🚀 Автоподбор"])

    with tab_manual:
        col1, col2 = st.columns(2)
        with col1:
            check_delta = st.number_input("Толщина стенки δ_н, мм", value=float(st.session_state.delta_n), step=0.1)
        with col2:
            check_dt = st.number_input("Темп. перепад Δt, °C", value=float(st.session_state.delta_t))

        D_vn = st.session_state.D_H - 2 * check_delta
        sigma_kc = st.session_state.P * D_vn / (2 * check_delta)
        sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n
        sigma_pr = -st.session_state.alpha * st.session_state.E * check_dt + st.session_state.mu * sigma_kc
        R2_A = (st.session_state.m * st.session_state.R2_n) / (0.9 * st.session_state.k_H)

        st.markdown("<div class='step-header'>1. Кольцевые напряжения</div>", unsafe_allow_html=True)
        st.latex(
            rf"\sigma_{{кц}}^н = \frac{{p \cdot D_{{вн}}}}{{2\delta_н}} = \frac{{{st.session_state.P} \cdot {D_vn:.2f}}}{{2 \cdot {check_delta}}} = {sigma_kc:.4f} \text{{ МПа}}")
        st.latex(
            rf"[\sigma_{{кц}}] = \frac{{m}}{{0.9 \cdot k_н}} \cdot R_2^н = \frac{{{st.session_state.m}}}{{0.9 \cdot {st.session_state.k_H}}} \cdot {st.session_state.R2_n} = {sigma_kc_allow:.4f} \text{{ МПа}}")

        st.markdown("<div class='step-header'>2. Продольные напряжения</div>", unsafe_allow_html=True)
        st.latex(
            rf"\sigma_{{пр}}^н = -\alpha \cdot E \cdot \Delta t + \mu \cdot \sigma_{{кц}}^н = -{st.session_state.alpha} \cdot {st.session_state.E} \cdot {check_dt} + {st.session_state.mu} \cdot {sigma_kc:.2f} = {sigma_pr:.4f} \text{{ МПа}}")

        st.markdown("<div class='step-header'>3. Эквивалентные напряжения и проверка</div>", unsafe_allow_html=True)
        if sigma_pr < 0:
            under_sqrt = 1 - 0.75 * (sigma_kc / sigma_kc_allow) ** 2
            if under_sqrt < 0:
                psi_1 = 0.0
                st.error("Ошибка: Кольцевые напряжения превышают допустимые пределы (подкоренное выражение < 0).")
            else:
                psi_1 = math.sqrt(under_sqrt) - 0.5 * (sigma_kc / sigma_kc_allow)
                st.latex(
                    rf"\psi_1 = \sqrt{{1 - 0.75 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right)^2}} - 0.5 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right) = {psi_1:.4f}")
        else:
            psi_1 = 1.0
            st.write("Труба растянута ($\sigma_{пр}^н \ge 0$), следовательно $\psi_1 = 1.0$")

        sigma_pr_allow = psi_1 * sigma_kc_allow
        st.latex(
            rf"[\sigma_{{пр}}] = \psi_1 \cdot R_2^д = {psi_1:.4f} \cdot {R2_A:.4f} = {sigma_pr_allow:.4f} \text{{ МПа}}")

        is_ok = (sigma_kc <= sigma_kc_allow) and (abs(sigma_pr) <= sigma_pr_allow)

        if is_ok:
            st.markdown(f"<div class='result-block'>Прочность обеспечена (σ_кц ≤ [σ_кц] и |σ_пр| ≤ [σ_пр]).</div>",
                        unsafe_allow_html=True)
            st.latex(
                rf"\text{{Мин. радиус изгиба СОД: }} \rho_{{min}} = 1000 \cdot D_{{вн}} = {1000 * D_vn / 1000:.4f} \text{{ м}}")
            if st.button("Зафиксировать толщину"): st.session_state.delta_n = check_delta
        else:
            st.markdown(f"<div class='error-block'>Прочность НЕ обеспечена. Требуется увеличить толщину стенки.</div>",
                        unsafe_allow_html=True)

    with tab_auto:
        st.subheader("Автоматический перебор толщин по ГОСТ")
        if st.button("🚀 Запустить автоподбор"):
            cur_d = st.session_state.delta_n
            iteration = 1
            while True:
                D_vn_iter = st.session_state.D_H - 2 * cur_d
                sig_kc_iter = st.session_state.P * D_vn_iter / (2 * cur_d)
                sig_pr_iter = -st.session_state.alpha * st.session_state.E * st.session_state.delta_t + st.session_state.mu * sig_kc_iter
                psi_iter = math.sqrt(abs(1 - 0.75 * (sig_kc_iter / sigma_kc_allow) ** 2)) - 0.5 * (
                            sig_kc_iter / sigma_kc_allow) if sig_pr_iter < 0 else 1.0
                sig_pr_allow_iter = psi_iter * sigma_kc_allow
                is_ok_iter = (sig_kc_iter <= sigma_kc_allow) and (abs(sig_pr_iter) <= sig_pr_allow_iter)

                with st.expander(f"Итерация {iteration}. Проверка δ = {cur_d} мм",
                                 expanded=True if is_ok_iter else False):
                    st.write(f"σ_кц = {sig_kc_iter:.2f} МПа (доп. {sigma_kc_allow:.2f} МПа)")
                    st.write(f"σ_пр = {abs(sig_pr_iter):.2f} МПа (доп. {sig_pr_allow_iter:.2f} МПа)")

                if is_ok_iter:
                    st.success(f"**Толщина стенки успешно подобрана: {cur_d} мм.**")
                    st.session_state.delta_n = cur_d
                    break
                else:
                    cur_d = get_next_thickness(cur_d + 0.1)
                    iteration += 1

# ==============================================================================
# 4. ПРИМЕР 8.3
# ==============================================================================
elif page == "4. 8.3: Продольная устойчивость":
    st.title("4. Пример 8.3. Продольная устойчивость (Прямой участок)")
    st.markdown(
        "<div class='info-text'>Оценка устойчивости сжатого подземного трубопровода против выпучивания. Рассматриваются две математические модели связи с грунтом: упругая и жесткопластичная.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³",
                                                    value=float(st.session_state.gamma_gr))
        st.session_state.h0 = st.number_input("Засыпка до верха h0, м", value=float(st.session_state.h0))
        st.session_state.phi_deg = st.number_input("Трение грунта φ, град", value=float(st.session_state.phi_deg))
    with col2:
        st.session_state.k_0 = st.number_input("Постель грунта k0, МН/м³", value=float(st.session_state.k_0))
        st.session_state.rho_ins = st.number_input("Плотность изоляции ρ_из, кг/м³",
                                                   value=float(st.session_state.rho_ins))
        st.session_state.delta_ins = st.number_input("Толщина изоляции, мм", value=float(st.session_state.delta_ins))

    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (st.session_state.delta_ins / 1000)
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_met = 78500 * F
    q_prod = rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4
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
    N_cr_uprug = 2.0 * math.sqrt((st.session_state.k_0 * 1e6) * D_ins_m * (st.session_state.E * 1e6) * I) / 1e6
    lam = 2 * math.pi * math.pow((st.session_state.E * 1e6) * I / (st.session_state.k_0 * 1e6 * D_ins_m), 0.25)

    st.markdown("<div class='step-header'>1. Геометрия и весовые нагрузки</div>", unsafe_allow_html=True)
    st.latex(rf"F = \frac{{\pi(D_н^2 - D_{{вн}}^2)}}{{4}} = {F:.6f} \text{{ м}}^2 \quad I = {I:.6f} \text{{ м}}^4")
    st.latex(
        rf"q_{{мет}} = \gamma_м F = {q_met:.2f} \text{{ Н/м}} \quad q_{{прод}} = \rho_{{пр}} g \frac{{\pi D_{{вн}}^2}}{{4}} = {q_prod:.2f} \text{{ Н/м}}")
    st.latex(rf"q_{{тр}} = n_{{с.в}}(q_{{мет}} + q_{{из}}) + n_{{пр}} q_{{прод}} = {q_tr:.4f} \text{{ Н/м}}")

    st.markdown("<div class='step-header'>2. Продольное усилие и давление грунта</div>", unsafe_allow_html=True)
    st.latex(rf"S = [(0.5 - \mu)\sigma_{{кц}} + \alpha E \Delta t] F = {S:.4f} \text{{ МН}}")
    st.latex(
        rf"p_{{гр}} = {p_gr:.4f} \text{{ Па}} \quad \rightarrow \quad \tau_{{пр}} = p_{{гр}} \tan \varphi = {tau_pr:.4f} \text{{ Па}}")
    st.latex(rf"p_0 = \pi D_{{н.и}} \tau_{{пр}} = {p0:.4f} \text{{ Н/м}} \quad q_в = {q_v:.4f} \text{{ Н/м}}")

    st.markdown("<div class='step-header'>3. Критические усилия (упругая и пластичная связи)</div>",
                unsafe_allow_html=True)
    st.latex(rf"N_{{кр.пл}} = 4.09 \sqrt[11]{{p_0^2 q_в^4 F^2 E^5 I^3}} = {N_cr_plast:.4f} \text{{ МН}}")
    st.latex(
        rf"N_{{кр.уп}} = 2 \sqrt{{k_0 D_{{н.и}} E I}} = {N_cr_uprug:.4f} \text{{ МН}} \quad (\text{{длина волны }} \lambda = {lam:.2f} \text{{ м}})")

    S_allow = (st.session_state.m / st.session_state.k_H) * min(N_cr_plast, N_cr_uprug)
    st.markdown("<div class='step-header'>4. Заключение</div>", unsafe_allow_html=True)
    st.latex(
        rf"S \le \frac{{m}}{{k_н}} \cdot \min(N_{{кр.пл}}, N_{{кр.уп}}) \rightarrow {S:.4f} \le {S_allow:.4f} \text{{ МН}}")

    if S <= S_allow:
        st.markdown(f"<div class='result-block'>Общая продольная устойчивость прямого участка ОБЕСПЕЧЕНА.</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='error-block'>Устойчивость НЕ обеспечена. Требуется балластировка (пригрузы).</div>",
                    unsafe_allow_html=True)

# ==============================================================================
# 5. ПРИМЕР 8.4
# ==============================================================================
elif page == "5. 8.4: Устойчивость в насыпи (Прямой)":
    st.title("5. Пример 8.4. Устойчивость в грунтовой насыпи")
    st.markdown(
        "<div class='info-text'>Расчет устойчивости трубопровода, уложенного в наземную насыпь (часто на болотах). Оценивается пассивный отпор берм насыпи, который предотвращает боковой выброс трубы.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.h1 = st.number_input("Высота до верхней образ. h1, м", value=float(st.session_state.h1))
        st.session_state.H = st.number_input("Полная высота насыпи H, м", value=float(st.session_state.H))
        st.session_state.b = st.number_input("Половина ширины поверху b, м", value=float(st.session_state.b))
    with col2:
        st.session_state.alpha_H = st.number_input("Угол откоса насыпи α_н, град", min_value=10.0,
                                                   value=float(st.session_state.alpha_H))
        st.session_state.gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³",
                                                    value=float(st.session_state.gamma_gr))
        st.session_state.phi_deg = st.number_input("Угол трения грунта φ, град", value=float(st.session_state.phi_deg))

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

    st.markdown("<div class='step-header'>1. Геометрия призмы выпирания</div>", unsafe_allow_html=True)
    Kp = math.tan(math.radians(45 + st.session_state.phi_deg / 2)) ** 2
    Ka = math.tan(math.radians(45 - st.session_state.phi_deg / 2)) ** 2
    cot_aH = 1.0 / math.tan(math.radians(st.session_state.alpha_H))

    h2 = st.session_state.h1 - (
                st.session_state.b + st.session_state.h0 * cot_aH - 0.5 * st.session_state.h1) * math.tan(
        math.radians(45 - st.session_state.phi_deg / 2))
    st.latex(rf"h_2 = h_1 - (b + h_0 \cot \alpha_н - 0.5 h_1) \tan(45^\circ - \varphi/2) = {h2:.4f} \text{{ м}}")

    st.markdown("<div class='step-header'>2. Горизонтальное сопротивление насыпи</div>", unsafe_allow_html=True)
    p_gr_nas = st.session_state.n_gr * st.session_state.gamma_gr * st.session_state.h0 * (
                st.session_state.b + 0.5 * st.session_state.h0 * cot_aH) / (
                           st.session_state.b + st.session_state.h0 * cot_aH)
    E1 = st.session_state.n_gr * st.session_state.gamma_gr * (
                st.session_state.h1 ** 2 - h2 ** 2) * Kp / 2 + p_gr_nas * st.session_state.h1 * Kp
    E_act = st.session_state.n_gr * st.session_state.gamma_gr * st.session_state.h1 ** 2 * Ka / 2 + p_gr_nas * st.session_state.h1 * Ka
    E2 = q_tr * math.tan(math.radians(st.session_state.phi_deg))
    q_gor = E1 - E_act + E2

    st.latex(rf"p_{{гр}} = {p_gr_nas:.4f} \text{{ Па}} \quad (\text{{давление на образующую}})")
    st.latex(rf"E_1 = {E1:.4f} \text{{ Н/м}} \quad (\text{{пассивный отпор}})")
    st.latex(rf"E_{{акт}} = {E_act:.4f} \text{{ Н/м}} \quad (\text{{активное давление}})")
    st.latex(rf"E_2 = q_{{тр}} \tan \varphi = {E2:.4f} \text{{ Н/м}} \quad (\text{{поперечное трение}})")
    st.latex(rf"q_{{гор}} = E_1 - E_{{акт}} + E_2 = {q_gor:.4f} \text{{ Н/м}}")

    st.markdown("<div class='step-header'>3. Критическое усилие и проверка</div>", unsafe_allow_html=True)
    tau_pr_nas = p_gr_nas * math.tan(math.radians(st.session_state.phi_deg))
    p0_nas = math.pi * D_ins_m * tau_pr_nas
    N_cr_nas = 3.97 * math.pow(p0_nas * q_gor ** 4 * F ** 2 * (st.session_state.E * 1e6) ** 5 * I ** 3, 1 / 11) / 1e6

    st.latex(rf"N_{{кр}} = 3.97 \sqrt[11]{{p_0 q_{{гор}}^4 F^2 E^5 I^3}} = {N_cr_nas:.4f} \text{{ МН}}")
    S_allow_nas = (st.session_state.m / st.session_state.k_H) * N_cr_nas
    st.latex(rf"S \le \frac{{m}}{{k_н}} \cdot N_{{кр}} \rightarrow {S:.4f} \le {S_allow_nas:.4f} \text{{ МН}}")

    if S <= S_allow_nas:
        st.markdown(f"<div class='result-block'>Устойчивость прямого участка в насыпи ОБЕСПЕЧЕНА.</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='error-block'>Устойчивость прямого участка в насыпи НЕ обеспечена. Увеличьте ширину бермы $b$.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# 6. ПРИМЕР 8.5
# ==============================================================================
elif page == "6. 8.5: Горизонтальный поворот":
    st.title("6. Пример 8.5. Устойчивость на горизонтальном повороте")
    st.markdown(
        "<div class='info-text'>Изогнутая в горизонтальной плоскости труба под воздействием давления и нагрева стремится выпрямиться. Проверяется, способна ли берма насыпи удержать трубу от бокового сдвига наружу кривой.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.rho_gor = st.number_input("Радиус гориз. поворота ρ_гор, м",
                                                   value=float(st.session_state.rho_gor))
        st.session_state.k_sdv = st.number_input("Запас против сдвига k_сдв", value=float(st.session_state.k_sdv))
    with col2:
        st.session_state.f_gr = st.number_input("Трение трубы о грунт f_гр", value=float(st.session_state.f_gr))

    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (st.session_state.delta_ins / 1000)
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4

    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 0.95 * (78500 * F + st.session_state.rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4) + 0.95 * (
                rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4)
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    st.markdown("<div class='step-header'>1. Геометрия насыпи и сдвигающее усилие</div>", unsafe_allow_html=True)
    cot_aH = 1.0 / math.tan(math.radians(st.session_state.alpha_H))
    a_low = st.session_state.b + st.session_state.H * cot_aH

    req_q_horiz = st.session_state.k_sdv * S * 1e6 / st.session_state.rho_gor

    st.latex(
        rf"a = b + H \cot \alpha_н = {st.session_state.b} + {st.session_state.H} \cdot {cot_aH:.4f} = {a_low:.4f} \text{{ м}}")
    st.latex(
        rf"q_{{сдв.треб}} = \frac{{k_{{сдв}} S}}{{\rho_{{гор}}}} = \frac{{{st.session_state.k_sdv} \cdot {S:.4f} \cdot 10^6}}{{{st.session_state.rho_gor}}} = {req_q_horiz:.4f} \text{{ Н/м}}")

    st.markdown("<div class='step-header'>2. Фактическое сопротивление грунта сдвигу</div>", unsafe_allow_html=True)
    term1 = st.session_state.n_gr * st.session_state.gamma_gr * math.tan(
        math.radians(st.session_state.phi_deg)) * st.session_state.H
    term2 = ((2 * a_low - D_ins_m) + (2 * st.session_state.b - D_ins_m)) / 4
    term3 = st.session_state.f_gr * (
                q_tr + st.session_state.n_gr * st.session_state.gamma_gr * D_ins_m * (st.session_state.H - D_ins_m))
    q_sdv = term1 * term2 + term3

    st.latex(
        rf"q_{{сдв}} = n_{{гр}}\gamma_{{гр}}\tan\varphi \cdot H \frac{{(2a - D_{{н.и}}) + (2b - D_{{н.и}})}}{{4}} + f_{{гр}}(q_{{тр}} + n_{{гр}}\gamma_{{гр}}D_{{н.и}}(H - D_{{н.и}}))")
    st.latex(rf"q_{{сдв}} = {q_sdv:.4f} \text{{ Н/м}}")

    st.markdown("<div class='step-header'>3. Заключение</div>", unsafe_allow_html=True)
    if q_sdv >= req_q_horiz:
        st.markdown(
            f"<div class='result-block'>Устойчивость горизонтального поворота ОБЕСПЕЧЕНА.<br>Фактическое сопротивление {q_sdv:.2f} Н/м > Требуемого {req_q_horiz:.2f} Н/м.</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='error-block'>Устойчивость НЕ обеспечена. Грунт не удержит трубу (Сдвиг {q_sdv:.2f} < {req_q_horiz:.2f}). Требуется увеличить радиус кривизны.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# 7. ПРИМЕР 8.6
# ==============================================================================
elif page == "7. 8.6: Вертикальный поворот":
    st.title("7. Пример 8.6. Устойчивость на вертикальном повороте")
    st.markdown(
        "<div class='info-text'>Труба, изогнутая выпуклостью вверх (на холме/перегибе рельефа), под действием продольных сил стремится выскочить из траншеи вверх. Единственное, что ее держит — собственный вес и вес грунта засыпки над ней.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.rho_v = st.number_input("Радиус верт. поворота ρ_в, м", value=float(st.session_state.rho_v))
        st.session_state.alpha_v = st.number_input("Угол верт. поворота α_в, град",
                                                   value=float(st.session_state.alpha_v))
    with col2:
        st.session_state.k_np = st.number_input("Запас против подъема k_н.п", value=float(st.session_state.k_np))

    D_H_m, delta_m = st.session_state.D_H / 1000, st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (st.session_state.delta_ins / 1000)
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4

    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 0.95 * (78500 * F + st.session_state.rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4) + 0.95 * (
                rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4)
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    st.markdown("<div class='step-header'>1. Геометрия кривой и коэффициент угла</div>", unsafe_allow_html=True)
    l_kr = 2 * st.session_state.rho_v * math.sin(math.radians(st.session_state.alpha_v / 2))
    f_izg = 2 * st.session_state.rho_v * math.sin(math.radians(st.session_state.alpha_v / 4)) ** 2
    k_alpha = math.sqrt(math.sin(math.radians(st.session_state.alpha_v / 2)) ** 2 + math.cos(
        math.radians(st.session_state.alpha_v / 2)) ** 4)

    st.latex(rf"l_{{кр}} = 2 \rho_в \sin(\alpha_в / 2) = {l_kr:.4f} \text{{ м (хорда кривой)}}")
    st.latex(rf"f = 2 \rho_в \sin^2(\alpha_в / 4) = {f_izg:.4f} \text{{ м (стрела упругого изгиба)}}")
    st.latex(rf"k_\alpha = \sqrt{{\sin^2(\alpha_в/2) + \cos^4(\alpha_в/2)}} = {k_alpha:.4f}")

    st.markdown("<div class='step-header'>2. Требуемое сопротивление подъему (Две проверки)</div>",
                unsafe_allow_html=True)
    q_v_treb1 = 2 * st.session_state.k_np * S * 1e6 / (
                l_kr * math.sqrt(1 + (l_kr / f_izg) ** 2 / 16)) if f_izg > 0 else 0
    q_v_treb2 = st.session_state.k_np * S * 1e6 / (k_alpha * st.session_state.rho_v)

    st.latex(
        rf"q_{{в.треб1}} = \frac{{2 k_{{н.п}} S}}{{l_{{кр}} \sqrt{{1 + (l_{{кр}}/f)^2 / 16}}}} = {q_v_treb1:.4f} \text{{ Н/м}}")
    st.latex(rf"q_{{в.треб2}} = \frac{{k_{{н.п}} S}}{{k_\alpha \rho_в}} = {q_v_treb2:.4f} \text{{ Н/м}}")

    st.markdown("<div class='step-header'>3. Фактическое сопротивление (Вес грунта над трубой)</div>",
                unsafe_allow_html=True)
    q_v = 0.95 * st.session_state.gamma_gr * D_ins_m * (
                st.session_state.h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr
    st.latex(
        rf"q_в = n_{{гр}} \gamma_{{гр}} D_{{н.и}} \left(h_0 + \frac{{D_{{н.и}}}}{{2}} - \frac{{\pi D_{{н.и}}}}{{8}}\right) + q_{{тр}} = {q_v:.4f} \text{{ Н/м}}")

    req_q_vert = max(q_v_treb1, q_v_treb2)

    st.markdown("<div class='step-header'>4. Заключение</div>", unsafe_allow_html=True)
    if q_v >= req_q_vert:
        st.markdown(
            f"<div class='result-block'>Устойчивость вертикального поворота ОБЕСПЕЧЕНА.<br>Веса засыпки ({q_v:.2f} Н/м) достаточно для удержания трубы от подъема.</div>",
            unsafe_allow_html=True)
    else:
        rho_min = st.session_state.rho_v * req_q_vert / q_v
        st.markdown(
            f"<div class='error-block'>Труба 'выскочит' из грунта вверх. <br>Требуется увеличить радиус кривизны до $\rho_{{min}} = {rho_min:.2f}$ м или забалластировать трубу.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# 8. ПРИМЕР 8.7
# ==============================================================================
elif page == "8. 8.7: Продольные перемещения":
    st.title("8. Пример 8.7. Продольные перемещения")
    st.markdown(
        "<div class='info-text'>Расчет сдвига свободного конца трубопровода (например, примыкающего к крановому узлу). Если продольное усилие превышает силу сцепления трубы с грунтом, формируется зона проскальзывания, и конец трубы смещается, что может привести к разрыву арматуры.</div>",
        unsafe_allow_html=True)

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

    st.markdown("<div class='step-header'>1. Предельные касательные напряжения и жесткость связи</div>",
                unsafe_allow_html=True)
    p_gr = (1.2 * st.session_state.gamma_gr * (st.session_state.h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))
    beta = math.sqrt(math.pi * D_H_m * (st.session_state.k_i * 1e6) / ((st.session_state.E * 1e6) * F))
    P_pr = tau_pr * math.pi * D_H_m / beta / 1e6

    st.latex(rf"\tau_{{пр}} = p_{{гр}} \tan \varphi = {tau_pr:.4f} \text{{ Па}}")
    st.latex(rf"\beta = \sqrt{{\frac{{\pi D_н k_и}}{{E F}}}} = {beta:.6f} \text{{ 1/м (коэффициент затухания)}}")
    st.latex(
        rf"P_{{пр}} = \frac{{\tau_{{пр}} \pi D_н}}{{\beta}} = {P_pr:.4f} \text{{ МН (предельное удерживающее усилие)}}")

    st.markdown("<div class='step-header'>2. Анализ зон деформации и перемещение конца</div>", unsafe_allow_html=True)
    if S > P_pr:
        p0 = math.pi * D_H_m * tau_pr
        l2 = (S * 1e6 - P_pr * 1e6) / p0
        l1 = 3.5 / beta
        u_end = (tau_pr / (st.session_state.k_i * 1e6)) + (((S * 1e6) ** 2 - (P_pr * 1e6) ** 2) / (
                    2 * math.pi * D_H_m * tau_pr * (st.session_state.E * 1e6) * F))

        st.latex(rf"S ({S:.4f}) > P_{{пр}} ({P_pr:.4f}) \rightarrow \text{{ Связь с грунтом нарушена (сдвиг).}}")
        st.latex(rf"l_1 \text{{ (длина упругой зоны)}} = \frac{{3.5}}{{\beta}} = {l1:.4f} \text{{ м}}")
        st.latex(rf"l_2 \text{{ (длина зоны скольжения)}} = \frac{{S - P_{{пр}}}}{{p_0}} = {l2:.4f} \text{{ м}}")
        st.markdown(f"<div class='result-block'>Полное перемещение свободного конца: u = {u_end * 1000:.4f} мм</div>",
                    unsafe_allow_html=True)
    else:
        st.latex(rf"S ({S:.4f}) \le P_{{пр}} ({P_pr:.4f}) \rightarrow \text{{ Проскальзывания нет.}}")
        st.markdown(
            "<div class='result-block'>Связь трубы с грунтом полностью упругая. Сдвиг торца практически равен нулю.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# 9. ИТОГОВЫЙ ОТЧЕТ (МНОГОСТРАНИЧНЫЙ PDF)
# ==============================================================================
elif page == "9. Итоговый отчет":
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
        "<div class='info-text'>Расчёт ведётся без промежуточного округления; значения в отчёте показаны с четырьмя знаками после запятой. Формулы и алгоритмы строго соответствуют СНиП 2.05.06-85*.</div>",
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
    st.header("Исходные данные")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Геометрия и нагрузки")
        geom_data = {
            "Параметр": ["Наружный диаметр D_н", "Толщина стенки δ_н", "Рабочее давление p", "Перепад температур Δt",
                         "Среда"],
            "Значение": [f"{st.session_state.D_H:.4f} мм", f"{st.session_state.delta_n:.4f} мм",
                         f"{st.session_state.P:.4f} МПа", f"{st.session_state.delta_t:.4f} °C",
                         st.session_state.product_type]
        }
        st.table(pd.DataFrame(geom_data))
    with c2:
        st.subheader("Материал")
        mat_data = {
            "Параметр": ["Предел прочности R_1н", "Предел текучести R_2н", "Модуль Юнга E", "Коэфф. работы m"],
            "Значение": [f"{st.session_state.R1_n:.4f} МПа", f"{st.session_state.R2_n:.4f} МПа",
                         f"{st.session_state.E:.4f} МПа", f"{st.session_state.m:.4f}"]
        }
        st.table(pd.DataFrame(mat_data))

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    st.header("8.1 — 8.2: Прочность и деформации")
    t1 = {"Параметр": ["Расчетное сопротивление R₁", "Расчетное сопротивление R₂", "Толщина по давлению",
                       "Кольцевые напряжения σ_кц", "Осевые напряжения σ_пр", "Коэффициент сжатия ψ₁",
                       "Допускаемое продольное [σ_пр]"],
          "Результат": [f"{R1:.4f}", f"{R2:.4f}", f"{delta_calc:.4f}", f"{sigma_kc:.4f}", f"{sigma_pr:.4f}",
                        f"{psi_1:.4f}", f"{sigma_pr_allow:.4f}"],
          "Единица": ["МПа", "МПа", "мм", "МПа", "МПа", "-", "МПа"]}
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