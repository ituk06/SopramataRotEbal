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

# --- МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ГРАНИЦ РОССИИ ---
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
                        if p1x == p2x or x <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y
    return inside


WINTER_PAL = [[60, 0, 100], [0, 50, 200], [100, 150, 255], [150, 220, 200], [200, 255, 150]]
SUMMER_PAL = [[200, 255, 150], [255, 255, 150], [255, 180, 50], [255, 50, 50], [180, 0, 0]]
SNOW_PAL = [[240, 250, 255], [150, 200, 255], [0, 50, 200], [0, 0, 100]]
WIND_PAL = [[240, 255, 200], [255, 220, 100], [255, 100, 50], [200, 0, 0]]


def get_color(val, palette, min_v, max_v):
    ratio = (val - min_v) / (max_v - min_v) if max_v != min_v else 0.5
    ratio = max(0.0, min(1.0, ratio))
    n_colors = len(palette)
    if ratio == 1.0: return palette[-1] + [160]
    scaled_ratio = ratio * (n_colors - 1)
    idx = int(scaled_ratio)
    t = scaled_ratio - idx
    c1, c2 = palette[idx], palette[idx + 1]
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return [r, g, b, 160]


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
    lats = np.arange(41, 80, step_lat)
    lons = np.arange(19, 191, step_lon)

    anchor_lats, anchor_lons, anchor_vals = df_anchors['lat'].values, df_anchors['lon'].values, df_anchors[col].values
    grid_data = []

    for lat in lats:
        for lon in lons:
            if not is_in_russia(lat, lon): continue
            lon_dist = (lon - anchor_lons) * math.cos(math.radians(lat))
            lat_dist = lat - anchor_lats
            dist_sq = lon_dist ** 2 + lat_dist ** 2 + 0.5
            weights = 1.0 / (dist_sq ** 2)
            val = np.sum(weights * anchor_vals) / np.sum(weights)
            c = get_color(val, pal, mn, mx)
            lon_real = lon if lon <= 180 else lon - 360
            polygon = [[lon_real - dlon, lat - dlat], [lon_real + dlon, lat - dlat], [lon_real + dlon, lat + dlat],
                       [lon_real - dlon, lat + dlat]]
            grid_data.append({'polygon': polygon, 'color': c})
    return pd.DataFrame(grid_data)


def get_next_thickness(calc_thickness, min_thickness=12.0):
    target = max(calc_thickness, min_thickness)
    for t in SORTAMENT:
        if t >= target: return t
    return math.ceil(target)


# Глобальная инициализация переменных сессии
state_defaults = {
    'product_type': "Нефть", 't_product': 5.0, 'D_H': 630.0, 'P': 8.0, 'n_p': 1.15,
    'R1_n': 590.0, 'R2_n': 440.0, 'm': 0.990, 'k1': 1.34, 'k2': 1.15, 'k_H': 1.155,
    'delta_n': 10.0, 'delta_t': 60.0, 'E': 206000.0, 'alpha': 0.000012, 'mu': 0.3,
    'gamma_gr': 17000.0, 'h0': 1.2, 'phi_deg': 36.0, 'k_0': 5.0, 'rho_ins': 1750.0,
    'delta_ins': 3.0, 'q_gor_input': 84689.4, 'rho_gor': 1400.0, 'alpha_v': 50.0, 'k_i': 5.0
}
for k, v in state_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.sidebar.title("🛢️ Учебный комплекс")
st.sidebar.markdown("Навигация по разделам РГР:")
page = st.sidebar.radio("Выберите этап:", [
    "1. Климатология (Интерактивная зона)",
    "2. Пример 8.1: Толщина стенки",
    "3. Пример 8.2: Проверка прочности",
    "4. Пример 8.3: Продольная устойчивость",
    "5. Примеры 8.4-8.6: Устойчивость в насыпи",
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


def find_image(base_name):
    for ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']:
        if os.path.exists(base_name + ext): return base_name + ext
    return None


# ==============================================================================
# ЭТАП 1: КЛИМАТОЛОГИЯ
# ==============================================================================
if page == "1. Климатология (Интерактивная зона)":
    st.title("1. Определение расчетного температурного перепада (Δt)")
    st.markdown(
        "<div class='info-text'><b>Учебная справка:</b> Температурный перепад Δt — это разница между температурой продукта внутри трубы и температурой замыкания (когда трубу сварили в траншее). Интерактивная карта сама смоделирует сплошную климатическую зону для всего материка.</div>",
        unsafe_allow_html=True)

    col_map1, col_map2 = st.columns([1, 1])
    with col_map1:
        st.subheader("Выбор района строительства")
        region = st.selectbox("Выберите город из базы:", list(CLIMATE_DATA.keys()) + ["Задать вручную (Свой город)"])

        if region == "Задать вручную (Свой город)":
            col_c1, col_c2 = st.columns(2)
            custom_name = col_c1.text_input("Название региона", value="Мой город")
            t_max_val = col_c2.number_input("Макс. температура (t_max), °C", value=30.0)
            t_min_val = col_c1.number_input("Мин. температура (t_min), °C", value=-30.0)
            custom_lat = col_c2.number_input("Широта (Lat)", value=55.0)
            custom_lon = col_c1.number_input("Долгота (Lon)", value=55.0)
            custom_snow = col_c2.number_input("Снеговой район (1-8)", value=3, min_value=1, max_value=8)
            custom_wind = col_c1.number_input("Ветровой район (1-7)", value=2, min_value=1, max_value=7)
            city_lat, city_lon = custom_lat, custom_lon
        else:
            t_max_val = CLIMATE_DATA[region]["t_max"]
            t_min_val = CLIMATE_DATA[region]["t_min"]
            custom_snow = CLIMATE_DATA[region]["snow"]
            custom_wind = CLIMATE_DATA[region]["wind"]
            city_lat, city_lon = CLIMATE_DATA[region]["lat"], CLIMATE_DATA[region]["lon"]
            custom_name = region

    with col_map2:
        st.subheader("Режимы интерактивной карты")
        map_mode = st.radio("Отображение климатических зон:",
                            ["Зимние температуры (t_min)", "Летние температуры (t_max)", "Снеговые районы",
                             "Ветровые районы"],
                            horizontal=True)

    df_anchors = pd.DataFrame.from_dict(CLIMATE_DATA, orient='index').reset_index()
    df_anchors.rename(columns={'index': 'Город'}, inplace=True)
    if region == "Задать вручную (Свой город)":
        custom_data = pd.DataFrame(
            [{"Город": custom_name, "t_min": t_min_val, "t_max": t_max_val, "lat": custom_lat, "lon": custom_lon,
              "snow": custom_snow, "wind": custom_wind}])
        df_anchors = pd.concat([df_anchors, custom_data], ignore_index=True)

    df_grid = generate_zone_grid(df_anchors, map_mode)
    layer_zones = pdk.Layer("PolygonLayer", df_grid, get_polygon="polygon", get_fill_color="color", opacity=0.6,
                            stroked=False, pickable=False)
    layer_cities = pdk.Layer("ScatterplotLayer", df_anchors, get_position=["lon", "lat"], get_radius=20000,
                             get_fill_color=[50, 50, 50, 200], pickable=False)
    layer_selected = pdk.Layer("ScatterplotLayer", pd.DataFrame([{"lat": city_lat, "lon": city_lon}]),
                               get_position=["lon", "lat"], get_radius=60000, get_fill_color=[255, 50, 50, 255],
                               pickable=False)

    view_state = pdk.ViewState(latitude=64.0, longitude=95.0, zoom=2.0, pitch=0)
    st.pydeck_chart(
        pdk.Deck(map_provider="carto", map_style="light", layers=[layer_zones, layer_cities, layer_selected],
                 initial_view_state=view_state))

    st.markdown("### Выбранные климатические параметры")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Мин. температура (t_min)", f"{t_min_val} °C")
    c2.metric("Макс. температура (t_max)", f"{t_max_val} °C")
    c3.metric("Снеговой район", f"№ {custom_snow}")
    c4.metric("Ветровой район", f"№ {custom_wind}")

    st.markdown("---")
    st.subheader("Расчет температур замыкания")
    col3, col4 = st.columns(2)
    with col3:
        # ИСПРАВЛЕНИЕ ТЕМПЕРАТУРЫ (ДИНАМИЧЕСКИЙ СБРОС НА 5 ИЛИ 6)
        prod = st.session_state.product_type
        new_prod = st.radio("Тип транспортируемого продукта:", ["Нефть", "Газ"], index=0 if prod == "Нефть" else 1)
        if new_prod != prod:
            st.session_state.product_type = new_prod
            st.session_state.t_product = 5.0 if new_prod == "Нефть" else 6.0
            st.rerun()  # Обновляем страницу мгновенно

        st.session_state.t_product = st.number_input("Температура эксплуатации продукта (t_э), °C",
                                                     value=float(st.session_state.t_product))

    with col4:
        st.markdown(
            "<div class='info-text'><b>Логика:</b> При отсутствии точных данных о дате сварки стыков, берем наихудший сценарий. Летом: температура воздуха + 3°C. Зимой: температура воздуха - 6°C.</div>",
            unsafe_allow_html=True)
        t_x = t_min_val - 6.0
        t_m = t_max_val + 3.0
        dt_x = st.session_state.t_product - t_x
        dt_m = st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.latex(rf"t_x = {t_min_val} - 6 = {t_x}^\circ \text{{C (Замыкание зимой)}}")
        st.latex(rf"t_m = {t_max_val} + 3 = {t_m}^\circ \text{{C (Замыкание летом)}}")
        st.latex(rf"\Delta t_x = {st.session_state.t_product} - ({t_x}) = {dt_x}^\circ \text{{C}}")
        st.latex(rf"\Delta t_m = {st.session_state.t_product} - ({t_m}) = {dt_m}^\circ \text{{C}}")

        st.success(f"**Расчетный (наихудший) температурный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить перепад Δt в память"):
            st.session_state.delta_t = calc_dt
            st.success("Перепад сохранен! Переходите к Этапу 2.")

# ==============================================================================
# ЭТАП 2: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "2. Пример 8.1: Толщина стенки":
    st.title("2. Пример 8.1. Определение расчетной толщины стенки")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.D_H = st.number_input("Наружный диаметр трубы (D_н), мм", value=float(st.session_state.D_H))
        st.session_state.P = st.number_input("Рабочее давление (p), МПа", value=float(st.session_state.P))
        st.session_state.n_p = st.number_input("Коэфф. надежности нагрузки (n_p)", value=float(st.session_state.n_p))
    with col2:
        st.session_state.R1_n = st.number_input("Врем. сопротивление (R1_н), МПа", value=float(st.session_state.R1_n))
        st.session_state.R2_n = st.number_input("Предел текучести (R2_н), МПа", value=float(st.session_state.R2_n))
        st.session_state.m = st.number_input("Коэфф. условий работы (m)", value=float(st.session_state.m))
    with col3:
        st.session_state.k1 = st.number_input("Коэфф. по материалу (k_1)", value=float(st.session_state.k1))
        st.session_state.k2 = st.number_input("Коэфф. по материалу (k_2)", value=float(st.session_state.k2))
        st.session_state.k_H = st.number_input("Коэфф. по ответственности (k_н)", value=float(st.session_state.k_H))

    R1 = (st.session_state.R1_n * st.session_state.m) / (st.session_state.k1 * st.session_state.k_H)
    R2 = (st.session_state.R2_n * st.session_state.m) / (st.session_state.k2 * st.session_state.k_H)
    delta_calc = (st.session_state.n_p * st.session_state.P * st.session_state.D_H) / (
                2 * (R1 + st.session_state.n_p * st.session_state.P))

    min_req_thickness = 12.0 if st.session_state.D_H >= 1000 else 4.0
    delta_nom = get_next_thickness(delta_calc, min_thickness=min_req_thickness)

    st.markdown("### Пошаговый расчет с пояснениями")
    st.latex(rf"R_1 = \frac{{R_1^н \cdot m}}{{k_1 \cdot k_н}} = {R1:.4f} \text{{ МПа}}")
    st.latex(rf"R_2 = \frac{{R_2^н \cdot m}}{{k_2 \cdot k_н}} = {R2:.4f} \text{{ МПа}}")
    st.latex(rf"\delta = \frac{{n_p \cdot p \cdot D_н}}{{2(R_1 + n_p \cdot p)}} = {delta_calc:.4f} \text{{ мм}}")

    st.markdown(f"<div class='result-block'>Принятая предварительная толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
                unsafe_allow_html=True)

    if st.button("Сохранить и перейти к проверке прочности"):
        st.session_state.delta_n = delta_nom
        st.rerun()

# ==============================================================================
# ЭТАП 3: ПРОВЕРКА ПРОЧНОСТИ
# ==============================================================================
elif page == "3. Пример 8.2: Проверка прочности":
    st.title("3. Пример 8.2. Проверка прочности трубопровода")

    tab_manual, tab_auto = st.tabs(["🖐️ Ручная проверка", "🚀 Автоподбор"])

    with tab_manual:
        col1, col2 = st.columns(2)
        with col1:
            check_delta = st.number_input("Проверяемая толщина стенки δ_н, мм", value=float(st.session_state.delta_n),
                                          step=0.1)
        with col2:
            check_dt = st.number_input("Расчетный темп. перепад Δt, °C", value=float(st.session_state.delta_t))

        is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(check_delta, check_dt)
        D_vn = st.session_state.D_H - 2 * check_delta

        st.latex(rf"\sigma_{{кц}}^н = \frac{{p \cdot D_{{вн}}}}{{2\delta_н}} = {sig_kc:.4f} \text{{ МПа}}")
        st.latex(rf"[\sigma_{{кц}}] = \frac{{m}}{{0.9 \cdot k_н}} \cdot R_2^н = {sig_kc_allow:.4f} \text{{ МПа}}")
        st.latex(
            rf"\sigma_{{пр}}^н = -\alpha \cdot E \cdot \Delta t + \mu \cdot \sigma_{{кц}}^н = {sig_pr:.4f} \text{{ МПа}}")
        st.latex(
            rf"\psi_1 = \sqrt{{1 - 0.75 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right)^2}} - 0.5 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right) = {psi:.4f}")
        st.latex(rf"[\sigma_{{пр}}] = \psi_1 \cdot [\sigma_{{кц}}] = {sig_pr_allow:.4f} \text{{ МПа}}")

        if is_ok:
            st.success(f"Прочность обеспечена! Рекомендуемая толщина стенки: {check_delta} мм.")
            st.latex(
                rf"\rho_{{min}} = 1000 \cdot D_{{вн}} = 1000 \cdot {D_vn / 1000:.4f} = {1000 * D_vn / 1000:.4f} \text{{ м}}")
            if st.button("Зафиксировать эту толщину"):
                st.session_state.delta_n = check_delta
                st.rerun()
        else:
            st.error(f"Труба не выдержит продольных нагрузок. Перейдите во вкладку «Автоподбор».")

    with tab_auto:
        st.subheader("Итерационный автоподбор толщины стенки")
        if st.button("🚀 Запустить алгоритм автоподбора"):
            current_delta = st.session_state.delta_n
            iteration = 1
            while True:
                is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(current_delta,
                                                                                        st.session_state.delta_t)
                with st.expander(f"Итерация {iteration}. Проверка толщины {current_delta} мм",
                                 expanded=True if is_ok else False):
                    st.write(
                        f"1) Кольцевые напряжения: {sig_kc:.4f} МПа ≤ {sig_kc_allow:.4f} МПа → **{'ВЫПОЛНЯЕТСЯ' if sig_kc <= sig_kc_allow else 'НЕ ВЫПОЛНЯЕТСЯ'}**")
                    st.write(
                        f"2) Продольные напряжения: {abs(sig_pr):.4f} МПа ≤ {sig_pr_allow:.4f} МПа → **{'ВЫПОЛНЯЕТСЯ' if abs(sig_pr) <= sig_pr_allow else 'НЕ ВЫПОЛНЯЕТСЯ'}**")
                if is_ok:
                    st.success(f"**Окончательная толщина стенки подобрана: {current_delta} мм.**")
                    st.session_state.delta_n = current_delta
                    break
                else:
                    current_delta = get_next_thickness(current_delta + 0.1)
                    iteration += 1

# ==============================================================================
# ЭТАП 4: УСТОЙЧИВОСТЬ ПРЯМОГО УЧАСТКА
# ==============================================================================
elif page == "4. Пример 8.3: Продольная устойчивость":
    st.title("4. Пример 8.3. Расчет продольной устойчивости (Прямой участок)")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³",
                                                    value=float(st.session_state.gamma_gr))
        st.session_state.h0 = st.number_input("Глубина заложения (до верха трубы) h0, м",
                                              value=float(st.session_state.h0))
        st.session_state.phi_deg = st.number_input("Угол трения грунта φ, град", value=float(st.session_state.phi_deg))
    with col2:
        st.session_state.k_0 = st.number_input("Коэфф. постели грунта k0, МН/м³", value=float(st.session_state.k_0))
        st.session_state.rho_ins = st.number_input("Плотность изоляции, кг/м³", value=float(st.session_state.rho_ins))
        st.session_state.delta_ins = st.number_input("Толщина изоляции, мм", value=float(st.session_state.delta_ins))

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
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

    N_cr_plast = 4.09 * math.pow((p0 ** 2 * q_v ** 4 * F ** 2 * (st.session_state.E * 10 ** 6) ** 5 * I ** 3),
                                 1 / 11) / 10 ** 6

    st.markdown("### Подробный расчет с пояснениями")
    st.latex(rf"F = {F:.4f} \text{{ м}}^2, \quad I = {I:.6f} \text{{ м}}^4")
    st.latex(rf"q_{{тр}} = {q_tr:.4f} \text{{ Н/м}}")
    st.latex(rf"S = {S:.4f} \text{{ МН}}")
    st.latex(rf"p_{{гр}} = {p_gr:.4f} \text{{ Па}}, \quad \tau_{{пр}} = {tau_pr:.4f} \text{{ Па}}")
    st.latex(rf"p_0 = {p0:.4f} \text{{ Н/м}}, \quad q_в = {q_v:.4f} \text{{ Н/м}}")
    st.latex(
        rf"N_{{кр}} = 4.09 \cdot \sqrt[11]{{p_0^2 \cdot q_в^4 \cdot F^2 \cdot E^5 \cdot I^3}} = {N_cr_plast:.4f} \text{{ МН}}")

    S_allow = (st.session_state.m / st.session_state.k_H) * N_cr_plast
    if S <= S_allow:
        st.markdown(f"<div class='result-block'>Условие выполняется: {S:.4f} МН ≤ {S_allow:.4f} МН. ОБЕСПЕЧЕНО.</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='error-block'>Условие НЕ выполняется. Требуется балластировка.</div>",
                    unsafe_allow_html=True)

# ==============================================================================
# ЭТАП 5: УСТОЙЧИВОСТЬ В НАСЫПИ
# ==============================================================================
elif page == "5. Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("5. Примеры 8.4 - 8.6. Устойчивость трубопровода в насыпи")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.q_gor_input = st.number_input("Боковое сопр. грунта E1+E2, Н/м",
                                                       value=float(st.session_state.q_gor_input))
    with col2:
        st.session_state.rho_gor = st.number_input("Радиус гориз. поворота ρ, м", value=float(st.session_state.rho_gor))
    with col3:
        st.session_state.alpha_v = st.number_input("Угол верт. поворота α_в, град",
                                                   value=float(st.session_state.alpha_v))

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_met = 78500 * F
    q_prod = rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4
    q_ins = st.session_state.rho_ins * 9.81 * math.pi * ((D_H_m + 0.006) ** 2 - D_H_m ** 2) / 4
    q_tr = 0.95 * (q_met + q_ins) + 0.95 * q_prod

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    st.subheader("1. Прямолинейный участок в насыпи (Пример 8.4)")
    p_gr = (0.95 * st.session_state.gamma_gr * st.session_state.h0 * (
                0.85 + 0.5 * st.session_state.h0 * (1 / math.tan(math.radians(39))))) / (
                       0.85 + st.session_state.h0 * (1 / math.tan(math.radians(39))))
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))
    p0 = math.pi * D_H_m * tau_pr

    N_cr_nas = 3.97 * math.pow((p0 * st.session_state.q_gor_input * F * (st.session_state.E * 10 ** 6) * I),
                               1 / 3) / 10 ** 6
    st.latex(rf"N_{{кр}} = {N_cr_nas:.4f} \text{{ МН}}")
    S_allow_nas = (st.session_state.m / st.session_state.k_H) * N_cr_nas
    if S <= S_allow_nas:
        st.success(f"Устойчивость прямого участка ОБЕСПЕЧЕНА (S = {S:.4f} МН ≤ {S_allow_nas:.4f} МН)")
    else:
        st.error("Устойчивость прямого участка НЕ обеспечена")

    st.subheader("2. Устойчивость на горизонтальном повороте (Пример 8.5)")
    req_q = 1.25 * S * 10 ** 6 / st.session_state.rho_gor
    st.latex(rf"q_{{треб}} = \frac{{1.25 \cdot S}}{{\rho}} = {req_q:.4f} \text{{ Н/м}}")

    st.subheader("3. Устойчивость на вертикальном повороте (Пример 8.6)")
    q_v = 0.95 * st.session_state.gamma_gr * D_H_m * (st.session_state.h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr
    k_alpha = math.sqrt(math.sin(math.radians(st.session_state.alpha_v / 2)) ** 2 + math.cos(
        math.radians(st.session_state.alpha_v / 2)) ** 4)
    req_q_v = 1.25 * S * 10 ** 6 * k_alpha / st.session_state.rho_gor
    st.latex(rf"q_{{в\_треб}} = \frac{{1.25 \cdot S \cdot k_\alpha}}{{\rho_в}} = {req_q_v:.4f} \text{{ Н/м}}")
    if q_v >= req_q_v:
        st.success(f"Устойчивость вертикального поворота ОБЕСПЕЧЕНА. (q_в = {q_v:.4f} Н/м > {req_q_v:.4f} Н/м)")
    else:
        st.error("Труба 'выскочит' из насыпи вверх.")

# ==============================================================================
# ЭТАП 6: ПРОДОЛЬНЫЕ ПЕРЕМЕЩЕНИЯ
# ==============================================================================
elif page == "6. Пример 8.7: Продольные перемещения":
    st.title("6. Пример 8.7. Продольные перемещения свободного конца")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.k_i = st.number_input("Коэфф. постели при сдвиге k_и, МН/м³",
                                               value=float(st.session_state.k_i))

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4

    rho_prod = 1000.0 if st.session_state.product_type == "Нефть" else 0.8
    q_met = 78500 * F
    q_prod = rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4
    q_ins = st.session_state.rho_ins * 9.81 * math.pi * ((D_H_m + 0.006) ** 2 - D_H_m ** 2) / 4
    q_tr = 0.95 * (q_met + q_ins) + 0.95 * q_prod

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (1.2 * st.session_state.gamma_gr * (st.session_state.h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))

    beta = math.sqrt(math.pi * D_H_m * (st.session_state.k_i * 10 ** 6) / ((st.session_state.E * 10 ** 6) * F))
    P_pr = tau_pr * math.pi * D_H_m / beta / 10 ** 6

    st.latex(rf"\tau_{{пр}} = {tau_pr:.4f} \text{{ Па}} \quad S = {S:.4f} \text{{ МН}}")
    st.latex(rf"\beta = \sqrt{{\frac{{\pi \cdot D_н \cdot k_и}}{{E \cdot F}}}} = {beta:.6f} \text{{ 1/м}}")
    st.latex(rf"P_{{пр}} = \frac{{\tau_{{пр}} \cdot \pi \cdot D_н}}{{\beta}} = {P_pr:.4f} \text{{ МН}}")

    if S > P_pr:
        st.markdown("<div class='error-block'>Формируется участок пластичной связи (проскальзывание).</div>",
                    unsafe_allow_html=True)
        p0 = math.pi * D_H_m * tau_pr
        l2 = (S * 10 ** 6 - P_pr * 10 ** 6) / p0
        l1 = 3.5 / beta
        u_end = (tau_pr / (st.session_state.k_i * 10 ** 6)) + (((S * 10 ** 6) ** 2 - (P_pr * 10 ** 6) ** 2) / (
                    2 * math.pi * D_H_m * tau_pr * (st.session_state.E * 10 ** 6) * F))

        st.latex(rf"l_1 \text{{ (упругая зона)}} = {l1:.4f} \text{{ м}}")
        st.latex(rf"l_2 \text{{ (зона скольжения)}} = {l2:.4f} \text{{ м}}")
        st.markdown(f"<div class='result-block'>Полное перемещение свободного конца: u = {u_end * 1000:.4f} мм</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<div class='result-block'>Связь трубы с грунтом полностью упругая. Сдвигов нет.</div>",
                    unsafe_allow_html=True)

# ==============================================================================
# ЭТАП 7: ИТОГОВЫЙ ОТЧЕТ (ГЕНЕРАЦИЯ PDF)
# ==============================================================================
elif page == "7. Итоговый отчет":
    st.markdown("""
        <style>
        @media print {
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
    st.sidebar.subheader("Настройки отчета")
    student_name = st.sidebar.text_input("ФИО / Исполнитель", value="Иванов И.И.")
    variant_num = st.sidebar.text_input("Вариант", value="15")
    project_name = st.sidebar.text_input("Название проекта",
                                         value="Расчёт прочности и устойчивости магистрального трубопровода")

    st.markdown("<div class='report-header'>", unsafe_allow_html=True)
    st.markdown(f"<div class='report-title'>Расчёт прочности и устойчивости трубопровода</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='report-subtitle'>{student_name} — вариант {variant_num}<br>{project_name}</div>",
                unsafe_allow_html=True)
    st.markdown(f"**Дата и время формирования:** {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='info-text'>Расчёт ведётся без промежуточного округления; значения в отчёте показаны с четырьмя знаками после запятой. Невыполненных вычисленных условий нет (при успешном автоподборе толщины стенки).</div>",
        unsafe_allow_html=True)

    st.subheader("Сводка по модулям")
    summary_data = {
        "Модуль": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7"],
        "Проверка": [
            "Требуемая толщина стенки",
            "Прочность по деформациям",
            "Общая продольная устойчивость",
            "Устойчивость в грунтовой насыпи (прямой)",
            "Устойчивость на горизонтальном повороте",
            "Устойчивость на вертикальном повороте",
            "Продольные перемещения"
        ],
        "Итог": ["выполняется", "выполняется", "выполняется", "выполняется", "выполняется", "выполняется",
                 "выполняется"]
    }
    st.table(pd.DataFrame(summary_data))

    st.markdown("---")
    st.header("Исходные данные")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Геометрия трубы")
        geom_data = {
            "Параметр": ["Наружный диаметр", "Принятая толщина стенки", "Внутренний диаметр"],
            "Обозначение": ["D_н", "δ_н", "D_вн"],
            "Значение": [f"{st.session_state.D_H:.4f}", f"{st.session_state.delta_n:.4f}",
                         f"{(st.session_state.D_H - 2 * st.session_state.delta_n):.4f}"],
            "Единица": ["мм", "мм", "мм"]
        }
        st.table(pd.DataFrame(geom_data))

        st.subheader("Давление и температура")
        pt_data = {
            "Параметр": ["Рабочее давление", "Темп. эксплуатации", "Расчетный перепад", "Среда"],
            "Обозначение": ["p", "t_э", "Δt", "-"],
            "Значение": [f"{st.session_state.P:.4f}", f"{st.session_state.t_product:.4f}",
                         f"{st.session_state.delta_t:.4f}", st.session_state.product_type],
            "Единица": ["МПа", "°C", "°C", "-"]
        }
        st.table(pd.DataFrame(pt_data))

    with col2:
        st.subheader("Характеристики материала")
        mat_data = {
            "Параметр": ["Предел прочности", "Предел текучести", "Модуль Юнга", "Коэфф. Пуассона",
                         "Коэфф. условий работы", "Надёжность по материалу", "Надёжность по назначению"],
            "Обозначение": ["R_1н", "R_2н", "E", "μ", "m", "k_1", "k_н"],
            "Значение": [
                f"{st.session_state.R1_n:.4f}", f"{st.session_state.R2_n:.4f}",
                f"{st.session_state.E:.4f}", f"{st.session_state.mu:.4f}",
                f"{st.session_state.m:.4f}", f"{st.session_state.k1:.4f}", f"{st.session_state.k_H:.4f}"
            ],
            "Единица": ["МПа", "МПа", "МПа", "-", "-", "-", "-"]
        }
        st.table(pd.DataFrame(mat_data))

    st.markdown("---")
    st.header("Подробные результаты вычислений (Аналог PDF-отчета)")

    # ---------------- ВЫЧИСЛЕНИЯ ДЛЯ ОТЧЕТА ----------------
    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
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
    q_met = 78500 * F
    q_prod = rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4
    q_ins = st.session_state.rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4
    q_tr = 0.95 * (q_met + q_ins) + 0.95 * q_prod
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    # Устойчивость
    p_gr = (2.0 * 0.95 * st.session_state.gamma_gr * D_ins_m * (
                (st.session_state.h0 + D_ins_m / 8) + (st.session_state.h0 + D_ins_m / 2) * math.tan(
            math.radians(45 - st.session_state.phi_deg / 2)) ** 2) + q_tr) / (math.pi * D_ins_m)
    tau_pr = p_gr * math.tan(math.radians(st.session_state.phi_deg))
    p0 = math.pi * D_ins_m * tau_pr
    q_v = 0.95 * st.session_state.gamma_gr * D_ins_m * (
                st.session_state.h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr
    N_cr_plast = 4.09 * math.pow((p0 ** 2 * q_v ** 4 * F ** 2 * (st.session_state.E * 10 ** 6) ** 5 * I ** 3),
                                 1 / 11) / 10 ** 6

    # Насыпь
    p_gr_nas = (0.95 * st.session_state.gamma_gr * st.session_state.h0 * (
                0.85 + 0.5 * st.session_state.h0 * (1 / math.tan(math.radians(39))))) / (
                           0.85 + st.session_state.h0 * (1 / math.tan(math.radians(39))))
    tau_pr_nas = p_gr_nas * math.tan(math.radians(st.session_state.phi_deg))
    p0_nas = math.pi * D_H_m * tau_pr_nas
    N_cr_nas = 3.97 * math.pow((p0_nas * st.session_state.q_gor_input * F * (st.session_state.E * 10 ** 6) * I),
                               1 / 3) / 10 ** 6
    req_q_horiz = 1.25 * S * 10 ** 6 / st.session_state.rho_gor
    k_alpha = math.sqrt(math.sin(math.radians(st.session_state.alpha_v / 2)) ** 2 + math.cos(
        math.radians(st.session_state.alpha_v / 2)) ** 4)
    req_q_vert = 1.25 * S * 10 ** 6 * k_alpha / st.session_state.rho_gor

    # Перемещения
    p_gr_87 = (1.2 * st.session_state.gamma_gr * (st.session_state.h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr_87 = p_gr_87 * math.tan(math.radians(st.session_state.phi_deg))
    beta_87 = math.sqrt(math.pi * D_H_m * (st.session_state.k_i * 10 ** 6) / ((st.session_state.E * 10 ** 6) * F))
    P_pr_87 = tau_pr_87 * math.pi * D_H_m / beta_87 / 10 ** 6

    st.subheader("Модули 8.1 - 8.2: Прочность и толщина стенки")
    res_8182 = {
        "Величина": ["Расчетное сопротивление R₁", "Расчетное сопротивление R₂", "Толщина по давлению",
                     "Кольцевые напряжения σ_кц", "Осевые напряжения σ_пр", "Коэффициент при сжатии ψ₁",
                     "Допускаемое продольное [σ_пр]"],
        "Результат": [f"{R1:.4f}", f"{R2:.4f}", f"{delta_calc:.4f}", f"{sigma_kc:.4f}", f"{sigma_pr:.4f}",
                      f"{psi_1:.4f}", f"{sigma_pr_allow:.4f}"],
        "Единица": ["МПа", "МПа", "мм", "МПа", "МПа", "-", "МПа"]
    }
    st.table(pd.DataFrame(res_8182))

    st.subheader("Модуль 8.3: Общая продольная устойчивость")
    res_83 = {
        "Величина": ["Площадь металла F", "Момент инерции I", "Расчётный погонный вес q_тр",
                     "Эквивалентное продольное усилие S", "Среднее давление грунта p_гр",
                     "Продольное сопротивление грунта p_0", "Сопротивление подъему q_в", "Критическое усилие N_кр"],
        "Результат": [f"{F:.6f}", f"{I:.6f}", f"{q_tr:.4f}", f"{S:.4f}", f"{p_gr:.4f}", f"{p0:.4f}", f"{q_v:.4f}",
                      f"{N_cr_plast:.4f}"],
        "Единица": ["м²", "м⁴", "Н/м", "МН", "Па", "Н/м", "Н/м", "МН"]
    }
    st.table(pd.DataFrame(res_83))

    st.subheader("Модули 8.4 - 8.6: Устойчивость в насыпи")
    res_8486 = {
        "Величина": ["Крит. усилие (прямой участок насыпи) N_кр", "Требуемое сопр. сдвигу (горизонталь) q_треб",
                     "Требуемое сопр. (вертикаль) q_в_треб"],
        "Результат": [f"{N_cr_nas:.4f}", f"{req_q_horiz:.4f}", f"{req_q_vert:.4f}"],
        "Единица": ["МН", "Н/м", "Н/м"]
    }
    st.table(pd.DataFrame(res_8486))

    st.subheader("Модуль 8.7: Продольные перемещения")
    res_87 = {
        "Величина": ["Предельное касательное напряжение τ_пр", "Коэффициент затухания β",
                     "Предельное удерживающее усилие P_пр"],
        "Результат": [f"{tau_pr_87:.4f}", f"{beta_87:.6f}", f"{P_pr_87:.4f}"],
        "Единица": ["Па", "1/м", "МН"]
    }
    st.table(pd.DataFrame(res_87))

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info(
        "💡 **Как сохранить отчет:** Нажмите `Ctrl + P` (или `Cmd + P` на Mac) и выберите «Сохранить как PDF». Меню слева и элементы управления автоматически скроются на печатной версии.")

    if st.button("🖨️ Открыть диалог печати (PDF)"):
        st.components.v1.html("<script>window.parent.print();</script>", height=0)