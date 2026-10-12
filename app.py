import streamlit as st
import math
import os
import pandas as pd
import numpy as np
import pydeck as pdk

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Сопромат Трубопроводов (Учебный курс)", page_icon="🛢️", layout="wide")

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

# Расширенная база данных для покрытия климатических зон по всей России
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
    "г. Санкт-Петербург": {"t_min": -26.0, "t_max": 25.0, "lat": 59.9343, "lon": 30.3351, "snow": 3, "wind": 2},
    "г. Чита": {"t_min": -40.0, "t_max": 29.0, "lat": 52.0333, "lon": 113.55, "snow": 1, "wind": 3},
    "г. Магадан": {"t_min": -30.0, "t_max": 18.0, "lat": 59.5667, "lon": 150.8, "snow": 4, "wind": 6},
    "г. Самара": {"t_min": -30.0, "t_max": 30.0, "lat": 53.2001, "lon": 50.15, "snow": 4, "wind": 3},
    "г. Анадырь": {"t_min": -43.0, "t_max": 20.0, "lat": 64.73, "lon": 177.51, "snow": 5, "wind": 6},
    "г. Южно-Сахалинск": {"t_min": -22.0, "t_max": 24.0, "lat": 46.95, "lon": 142.73, "snow": 5, "wind": 4},
    "с. Хатанга": {"t_min": -48.0, "t_max": 20.0, "lat": 71.98, "lon": 102.50, "snow": 5, "wind": 4},
}

# --- МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ГРАНИЦ РОССИИ ---
# Полигон контуров России (для алгоритма Ray Casting)
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
    """Определяет, находится ли точка внутри контура России (Алгоритм Point in Polygon)"""
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


# Цветовые палитры для сглаженной интерполяции
WINTER_PAL = [[60, 0, 100], [0, 50, 200], [100, 150, 255], [150, 220, 200], [200, 255, 150]]
SUMMER_PAL = [[200, 255, 150], [255, 255, 150], [255, 180, 50], [255, 50, 50], [180, 0, 0]]
SNOW_PAL = [[240, 250, 255], [150, 200, 255], [0, 50, 200], [0, 0, 100]]
WIND_PAL = [[240, 255, 200], [255, 220, 100], [255, 100, 50], [200, 0, 0]]


def get_color(val, palette, min_v, max_v):
    ratio = (val - min_v) / (max_v - min_v) if max_v != min_v else 0.5
    ratio = max(0.0, min(1.0, ratio))
    n_colors = len(palette)
    if ratio == 1.0: return palette[-1] + [140]  # Альфа-канал 140 для полупрозрачности
    scaled_ratio = ratio * (n_colors - 1)
    idx = int(scaled_ratio)
    t = scaled_ratio - idx
    c1, c2 = palette[idx], palette[idx + 1]
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return [r, g, b, 140]


@st.cache_data
def generate_zone_grid(df_anchors, mode):
    """Генерация сглаженной тепловой карты высокого разрешения с маской по границам РФ"""
    if mode == "Зимние температуры (t_min)":
        col, pal, mn, mx = "t_min", WINTER_PAL, -55.0, -15.0
    elif mode == "Летние температуры (t_max)":
        col, pal, mn, mx = "t_max", SUMMER_PAL, 15.0, 35.0
    elif mode == "Снеговые районы":
        col, pal, mn, mx = "snow", SNOW_PAL, 1.0, 6.0
    else:
        col, pal, mn, mx = "wind", WIND_PAL, 1.0, 6.0

    # Высокое разрешение сетки
    step_lat, step_lon = 0.5, 1.0
    lats = np.arange(41, 80, step_lat)
    lons = np.arange(19, 191, step_lon)

    anchor_lats, anchor_lons, anchor_vals = df_anchors['lat'].values, df_anchors['lon'].values, df_anchors[col].values
    grid_data = []

    for lat in lats:
        for lon in lons:
            if not is_in_russia(lat, lon):
                continue  # Маска: обрезаем карту по контуру России!

            lon_dist = (lon - anchor_lons) * math.cos(math.radians(lat))
            lat_dist = lat - anchor_lats
            dist_sq = lon_dist ** 2 + lat_dist ** 2 + 0.5  # Коэффициент сглаживания
            weights = 1.0 / (dist_sq ** 2)
            val = np.sum(weights * anchor_vals) / np.sum(weights)

            c = get_color(val, pal, mn, mx)
            lon_real = lon if lon <= 180 else lon - 360
            grid_data.append({'lat': lat, 'lon': lon_real, 'color': c})

    return pd.DataFrame(grid_data)


def get_next_thickness(calc_thickness, min_thickness=12.0):
    target = max(calc_thickness, min_thickness)
    for t in SORTAMENT:
        if t >= target:
            return t
    return math.ceil(target)


# Инициализация переменных сессии
if 'product_type' not in st.session_state: st.session_state.product_type = "Нефть"
if 't_product' not in st.session_state: st.session_state.t_product = 5.0
if 'D_H' not in st.session_state: st.session_state.D_H = 1020.0
if 'P' not in st.session_state: st.session_state.P = 6.0
if 'R1_n' not in st.session_state: st.session_state.R1_n = 589.0
if 'R2_n' not in st.session_state: st.session_state.R2_n = 461.0
if 'm' not in st.session_state: st.session_state.m = 0.990
if 'k1' not in st.session_state: st.session_state.k1 = 1.34
if 'k2' not in st.session_state: st.session_state.k2 = 1.15
if 'k_H' not in st.session_state: st.session_state.k_H = 1.100
if 'delta_n' not in st.session_state: st.session_state.delta_n = 12.0
if 'delta_t' not in st.session_state: st.session_state.delta_t = 61.0
if 'E' not in st.session_state: st.session_state.E = 206000.0
if 'alpha' not in st.session_state: st.session_state.alpha = 0.000012
if 'mu' not in st.session_state: st.session_state.mu = 0.3

st.sidebar.title("🛢️ Учебный комплекс")
st.sidebar.markdown("Навигация по разделам РГР:")
page = st.sidebar.radio("Выберите этап:", [
    "1. Климатология (Интерактивная зона)",
    "2. Пример 8.1: Толщина стенки",
    "3. Пример 8.2: Проверка прочности",
    "4. Пример 8.3: Продольная устойчивость",
    "5. Примеры 8.4-8.6: Устойчивость в насыпи",
    "6. Пример 8.7: Продольные перемещения"
])

st.sidebar.markdown("---")
st.sidebar.info(f"**Толщина стенки в памяти:**\n\nδ_н = {st.session_state.delta_n} мм")


def check_strength(delta, dt):
    D_vn = st.session_state.D_H - 2 * delta
    sigma_kc_n = st.session_state.P * D_vn / (2 * delta)
    sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n
    sigma_pr_n = -st.session_state.alpha * st.session_state.E * dt + st.session_state.mu * sigma_kc_n

    if sigma_pr_n < 0:
        under_sqrt = 1 - 0.75 * (sigma_kc_n / sigma_kc_allow) ** 2
        if under_sqrt < 0:
            return False, sigma_kc_n, sigma_kc_allow, sigma_pr_n, 0, 0
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
        "<div class='info-text'><b>Учебная справка:</b> Температурный перепад Δt — это разница между температурой продукта внутри трубы и температурой замыкания (когда трубу сварили в траншее). Труба стремится расшириться от тепла или сжаться от холода, но грунт ей мешает. Из-за этого возникают колоссальные продольные напряжения, которые могут разорвать или выпучить трубу.</div>",
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
            st.info(f"📍 **{region}**: Снег — {custom_snow} район, Ветер — {custom_wind} район")

    with col_map2:
        st.subheader("Режимы интерактивной карты")
        map_mode = st.radio("Отображение климатических зон:",
                            ["Зимние температуры (t_min)", "Летние температуры (t_max)", "Снеговые районы",
                             "Ветровые районы"],
                            horizontal=True)

    # ------------------ РЕНДЕР ИДЕАЛЬНОЙ КАРТЫ С КОНТУРОМ РОССИИ ------------------
    df_anchors = pd.DataFrame.from_dict(CLIMATE_DATA, orient='index').reset_index()
    df_anchors.rename(columns={'index': 'Город'}, inplace=True)

    if region == "Задать вручную (Свой город)":
        custom_data = pd.DataFrame(
            [{"Город": custom_name, "t_min": t_min_val, "t_max": t_max_val, "lat": custom_lat, "lon": custom_lon,
              "snow": custom_snow, "wind": custom_wind}])
        df_anchors = pd.concat([df_anchors, custom_data], ignore_index=True)

    df_grid = generate_zone_grid(df_anchors, map_mode)

    # Вместо блоков - используем пересекающиеся мягкие круги для идеального градиента
    layer_zones = pdk.Layer(
        "ScatterplotLayer",
        df_grid,
        get_position=["lon", "lat"],
        get_radius=55000,  # Радиус перекрытия для бесшовности
        get_fill_color="color",
        pickable=False,
    )

    layer_cities = pdk.Layer(
        "ScatterplotLayer",
        df_anchors,
        get_position=["lon", "lat"],
        get_radius=15000,
        get_fill_color=[50, 50, 50, 200],
        pickable=False,
    )

    layer_selected = pdk.Layer(
        "ScatterplotLayer",
        pd.DataFrame([{"lat": city_lat, "lon": city_lon}]),
        get_position=["lon", "lat"],
        get_radius=40000,
        get_fill_color=[255, 50, 50, 255],
        pickable=False,
    )

    view_state = pdk.ViewState(latitude=64.0, longitude=95.0, zoom=2.0, pitch=0)

    st.pydeck_chart(pdk.Deck(
        map_provider="carto",
        map_style="light",
        layers=[layer_zones, layer_cities, layer_selected],
        initial_view_state=view_state,
        tooltip={"html": "Красная точка - выбранный район строительства"}
    ))
    # -----------------------------------------------------------

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
        st.session_state.product_type = st.radio("Тип транспортируемого продукта:", ["Нефть", "Газ"],
                                                 index=0 if st.session_state.product_type == "Нефть" else 1)
        st.session_state.t_product = st.number_input("Температура эксплуатации продукта (t_э), °C",
                                                     value=5.0 if st.session_state.product_type == "Нефть" else 6.0)

    with col4:
        st.markdown(
            "<div class='info-text'><b>Логика:</b> При отсутствии точных данных о дате сварки стыков, берем наихудший сценарий. Летом: температура воздуха + 3°C (нагрев трубы солнцем). Зимой: температура воздуха - 6°C.</div>",
            unsafe_allow_html=True)
        t_x = t_min_val - 6.0
        t_m = t_max_val + 3.0
        dt_x = st.session_state.t_product - t_x
        dt_m = st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.latex(rf"t_x = {t_min_val} - 6 = {t_x}^\circ C \text{{ (Замыкание зимой)}}")
        st.latex(rf"t_m = {t_max_val} + 3 = {t_m}^\circ C \text{{ (Замыкание летом)}}")
        st.latex(rf"\Delta t_x = {st.session_state.t_product} - ({t_x}) = {dt_x}^\circ C")
        st.latex(rf"\Delta t_m = {st.session_state.t_product} - ({t_m}) = {dt_m}^\circ C")

        st.success(f"**Расчетный (наихудший) температурный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить Δt"):
            st.session_state.delta_t = calc_dt
            st.success("Перепад сохранен! Переходите к Этапу 2.")

    with st.expander("Посмотреть оригинальные карты из СНиП"):
        tab_img1, tab_img2, tab_img3, tab_img4, tab_img5 = st.tabs(["t_max", "t_min", "Снег", "Ветер", "Гололед"])
        with tab_img1:
            img = find_image("Снимок экрана 2026-10-09 в 00.49.04") or find_image("map_max")
            if img: st.image(img, caption="Карта максимальных температур", use_container_width=True)
        with tab_img2:
            img2 = find_image("Снимок экрана 2026-10-09 в 00.49.13") or find_image("map_min")
            if img2: st.image(img2, caption="Карта минимальных температур", use_container_width=True)
        with tab_img3:
            img3 = find_image("Снимок экрана 2026-10-09 в 00.49.19") or find_image("map_snow")
            if img3: st.image(img3, caption="Снеговые районы", use_container_width=True)
        with tab_img4:
            img4 = find_image("Снимок экрана 2026-10-09 в 00.49.27") or find_image("map_wind")
            if img4: st.image(img4, caption="Ветровые районы", use_container_width=True)
        with tab_img5:
            img5 = find_image("Снимок экрана 2026-10-09 в 00.49.35") or find_image("map_ice")
            if img5: st.image(img5, caption="Гололедные районы", use_container_width=True)

# ==============================================================================
# ЭТАП 2: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "2. Пример 8.1: Толщина стенки":
    st.title("2. Пример 8.1. Определение расчетной толщины стенки")
    st.markdown(
        "<div class='info-text'><b>Учебная справка:</b> Здесь определяется минимально необходимая толщина стенки трубы по безмоментной теории оболочек. Она рассчитывается только на <b>внутреннее давление продукта</b> (распирание). Затем мы берем ближайшую стандартную толщину по ГОСТ. Эта базовая толщина позже будет проверяться на температурные перепады.</div>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.D_H = st.number_input("Наружный диаметр D_н, мм", value=st.session_state.D_H)
        st.session_state.P = st.number_input("Рабочее давление p, МПа", value=st.session_state.P)
        n_p = st.number_input("Коэфф. надежности нагрузки n_p", value=1.1)
    with col2:
        st.session_state.R1_n = st.number_input("Врем. сопротивление R1_н, МПа", value=st.session_state.R1_n)
        st.session_state.R2_n = st.number_input("Предел текучести R2_н, МПа", value=st.session_state.R2_n)
        st.session_state.m = st.number_input("Коэфф. условий работы m", value=st.session_state.m)
    with col3:
        st.session_state.k1 = st.number_input("Коэфф. по материалу k1", value=st.session_state.k1)
        st.session_state.k2 = st.number_input("Коэфф. по материалу k2", value=st.session_state.k2)
        st.session_state.k_H = st.number_input("Коэфф. по ответственности k_н", value=st.session_state.k_H)

    R1 = (st.session_state.R1_n * st.session_state.m) / (st.session_state.k1 * st.session_state.k_H)
    R2 = (st.session_state.R2_n * st.session_state.m) / (st.session_state.k2 * st.session_state.k_H)
    delta_calc = (n_p * st.session_state.P * st.session_state.D_H) / (2 * (R1 + n_p * st.session_state.P))

    min_req_thickness = 12.0 if st.session_state.D_H >= 1000 else 4.0
    delta_nom = get_next_thickness(delta_calc, min_thickness=min_req_thickness)

    st.markdown("### Пошаговый расчет с пояснениями")
    st.write("1. Находим расчетные сопротивления материала труб R₁ (по пределу прочности) и R₂ (по пределу текучести):")
    st.latex(
        rf"R_1 = \frac{{R_1^н \cdot m}}{{k_1 \cdot k_н}} = \frac{{{st.session_state.R1_n} \cdot {st.session_state.m}}}{{{st.session_state.k1} \cdot {st.session_state.k_H}}} = {R1:.2f} \text{{ МПа}}")
    st.latex(
        rf"R_2 = \frac{{R_2^н \cdot m}}{{k_2 \cdot k_н}} = \frac{{{st.session_state.R2_n} \cdot {st.session_state.m}}}{{{st.session_state.k2} \cdot {st.session_state.k_H}}} = {R2:.2f} \text{{ МПа}}")

    st.write("2. Определяем расчетную (теоретическую) толщину стенки:")
    st.latex(
        rf"\delta = \frac{{n_p \cdot p \cdot D_н}}{{2(R_1 + n_p \cdot p)}} = \frac{{{n_p} \cdot {st.session_state.P} \cdot {st.session_state.D_H}}}{{2({R1:.2f} + {n_p} \cdot {st.session_state.P})}} = {delta_calc:.2f} \text{{ мм}}")

    st.markdown(
        f"<div class='result-block'>3. Округляем в большую сторону до стандартного значения по ГОСТ. Для труб с наружным диаметром от 1000 мм толщина стенки не может быть менее 12 мм.<br><br><b>Принятая предварительная толщина стенки: δ_н = {delta_nom:.1f} мм</b></div>",
        unsafe_allow_html=True)

    if st.button("Сохранить и перейти к проверке прочности"):
        st.session_state.delta_n = delta_nom
        st.rerun()

# ==============================================================================
# ЭТАП 3: ПРОВЕРКА ПРОЧНОСТИ (ОБЪЕДИНЕННАЯ)
# ==============================================================================
elif page == "3. Пример 8.2: Проверка прочности":
    st.title("3. Пример 8.2. Проверка прочности трубопровода")
    st.markdown(
        "<div class='info-text'><b>Учебная справка:</b> Трубопровод защемлен грунтом. При охлаждении он хочет сжаться, но грунт держит его, вызывая <b>продольные растягивающие напряжения</b>. При нагреве он расширяется, вызывая <b>сжимающие напряжения</b>. Сжатие наиболее опасно, так как может привести к местной потере устойчивости (гофрам). Здесь мы проверяем, выдержит ли металл совместное действие кольцевых и продольных напряжений.</div>",
        unsafe_allow_html=True)

    tab_manual, tab_auto = st.tabs(
        ["🖐️ Ручная проверка (для текущей толщины)", "🚀 Итерационный Автоподбор (Умный алгоритм)"])

    # --- РУЧНАЯ ПРОВЕРКА ---
    with tab_manual:
        st.subheader("Детальный расчет для заданного сечения")
        col1, col2 = st.columns(2)
        with col1:
            check_delta = st.number_input("Проверяемая толщина стенки δ_н, мм", value=float(st.session_state.delta_n),
                                          step=1.0)
        with col2:
            check_dt = st.number_input("Расчетный темп. перепад Δt, °C", value=st.session_state.delta_t)

        is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(check_delta, check_dt)
        D_vn = st.session_state.D_H - 2 * check_delta

        st.write("1. Кольцевые напряжения (распирание от давления):")
        st.latex(
            rf"\sigma_{{кц}}^н = \frac{{p \cdot D_{{вн}}}}{{2\delta_н}} = \frac{{{st.session_state.P} \cdot {D_vn}}}{{2 \cdot {check_delta}}} = {sig_kc:.2f} \text{{ МПа}}")
        st.latex(
            rf"[\sigma_{{кц}}] = \frac{{m}}{{0.9 \cdot k_н}} \cdot R_2^н = \frac{{{st.session_state.m}}}{{0.9 \cdot {st.session_state.k_H}}} \cdot {st.session_state.R2_n} = {sig_kc_allow:.2f} \text{{ МПа}}")

        if sig_kc <= sig_kc_allow:
            st.markdown(
                f"**Условие 3.21 ($\sigma_{{кц}}^н \le [\sigma_{{кц}}]$):** <span style='color:green'>ВЫПОЛНЯЕТСЯ ✅ (TRUE)</span>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"**Условие 3.21 ($\sigma_{{кц}}^н \le [\sigma_{{кц}}]$):** <span style='color:red'>НЕ ВЫПОЛНЯЕТСЯ ❌ (FALSE)</span>",
                unsafe_allow_html=True)

        st.write("2. Продольные напряжения (температура + эффект Пуассона):")
        st.latex(
            rf"\sigma_{{пр}}^н = -\alpha \cdot E \cdot \Delta t + \mu \cdot \sigma_{{кц}}^н = -{st.session_state.alpha} \cdot {st.session_state.E} \cdot {check_dt} + {st.session_state.mu} \cdot {sig_kc:.2f} = {sig_pr:.2f} \text{{ МПа}}")

        st.write("3. Учет двухосного напряженного состояния (поправка $\psi_1$ на сжатие):")
        st.latex(
            rf"\psi_1 = \sqrt{{1 - 0.75 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right)^2}} - 0.5 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right) = \sqrt{{1 - 0.75 \left(\frac{{{sig_kc:.2f}}}{{{sig_kc_allow:.2f}}}\right)^2}} - 0.5 \left(\frac{{{sig_kc:.2f}}}{{{sig_kc_allow:.2f}}}\right) = {psi:.4f}")
        st.latex(
            rf"[\sigma_{{пр}}] = \psi_1 \cdot [\sigma_{{кц}}] = {psi:.4f} \cdot {sig_kc_allow:.2f} = {sig_pr_allow:.2f} \text{{ МПа}}")

        if abs(sig_pr) <= sig_pr_allow:
            st.markdown(
                f"**Условие 3.20 ($|\sigma_{{пр}}^н| \le [\sigma_{{пр}}]$):** <span style='color:green'>ВЫПОЛНЯЕТСЯ ✅ (TRUE)</span>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"**Условие 3.20 ($|\sigma_{{пр}}^н| \le [\sigma_{{пр}}]$):** <span style='color:red'>НЕ ВЫПОЛНЯЕТСЯ ❌ (FALSE)</span>",
                unsafe_allow_html=True)

        st.markdown("---")

        if is_ok:
            st.success(f"Прочность обеспечена! Рекомендуемая толщина стенки: {check_delta} мм.")

            rho_min = 1000 * (D_vn / 1000)
            st.write("4. Минимальный радиус упругого изгиба для прохода СОД:")
            st.latex(rf"\rho_{{min}} = 1000 \cdot D_{{вн}} = 1000 \cdot {D_vn / 1000:.3f} = {rho_min:.1f} \text{{ м}}")

            if st.button("Зафиксировать эту толщину для следующих расчетов"):
                st.session_state.delta_n = check_delta
                st.rerun()
        else:
            st.error(
                f"При толщине {check_delta} мм труба не выдержит продольных нагрузок. Перейдите во вкладку «Автоподбор».")

    # --- АВТОПОДБОР ---
    with tab_auto:
        st.subheader("Итерационный автоподбор толщины стенки")
        st.markdown(
            "<div class='info-text'>Если при текущей толщине труба не проходит проверку, алгоритм автоматически начнет перебирать стандартные толщины по ГОСТ в сторону увеличения, пока оба условия не станут <b>TRUE</b>.</div>",
            unsafe_allow_html=True)

        if st.button("🚀 Запустить алгоритм автоподбора"):
            current_delta = st.session_state.delta_n
            iteration = 1
            while True:
                is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(current_delta,
                                                                                        st.session_state.delta_t)

                with st.expander(f"Итерация {iteration}. Проверка толщины стенки {current_delta} мм",
                                 expanded=True if is_ok else False):
                    st.write(
                        f"1) Условие кольцевых напряжений: $\sigma_{{кц}} = {sig_kc:.2f}$ МПа $\le$ $[\sigma_{{кц}}] = {sig_kc_allow:.2f}$ МПа $\\rightarrow$ **{'ВЫПОЛНЯЕТСЯ' if sig_kc <= sig_kc_allow else 'НЕ ВЫПОЛНЯЕТСЯ'}**")
                    st.write(
                        f"2) Условие продольных напряжений: $|\sigma_{{пр}}| = {abs(sig_pr):.2f}$ МПа $\le$ $[\sigma_{{пр}}] = {sig_pr_allow:.2f}$ МПа $\\rightarrow$ **{'ВЫПОЛНЯЕТСЯ' if abs(sig_pr) <= sig_pr_allow else 'НЕ ВЫПОЛНЯЕТСЯ'}**")

                if is_ok:
                    st.success(
                        f"**РАСЧЕТ УСПЕШНО ОКОНЧЕН. Окончательная толщина стенки подобрана: {current_delta} мм.**")
                    st.session_state.delta_n = current_delta

                    st.markdown("---")
                    st.markdown("### Определение радиуса упругого изгиба")
                    D_vn_m = (st.session_state.D_H - 2 * current_delta) / 1000
                    rho_min = 1000 * D_vn_m
                    st.markdown(
                        "<div class='info-text'>Согласно п.8.3, минимальный радиус упругого изгиба трубопровода из условия беспрепятственного прохождения внутритрубных очистных устройств (СОД) должен составлять не менее 1000 внутренних диаметров трубы.</div>",
                        unsafe_allow_html=True)
                    st.latex(
                        rf"\rho_{{min}} = 1000 \cdot D_{{вн}} = 1000 \cdot {D_vn_m:.3f} = {rho_min:.1f} \text{{ м}}")
                    break
                else:
                    st.warning(
                        f"Условие не выполнилось для {current_delta} мм. Проверяем следующую толщину по сортаменту...")
                    current_delta = get_next_thickness(current_delta + 0.1)
                    iteration += 1

# ==============================================================================
# ЭТАП 4: УСТОЙЧИВОСТЬ ПРЯМОГО УЧАСТКА
# ==============================================================================
elif page == "4. Пример 8.3: Продольная устойчивость":
    st.title("4. Пример 8.3. Расчет продольной устойчивости (Прямой участок)")
    st.info(f"**Используется окончательная толщина стенки:** δ_н = {st.session_state.delta_n} мм")
    st.markdown(
        "<div class='info-text'><b>Учебная справка:</b> Сжатая продольными силами труба может потерять устойчивость (изогнуться дугой и выскочить из земли). Засыпка сверху ($q_в$) и сопротивление сдвигу в грунте ($p_0$) удерживают ее. На этом этапе мы проверяем, достаточно ли веса засыпки.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=18000.0)
        h0 = st.number_input("Глубина заложения (до верха трубы) h0, м", value=1.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=38.0)
    with col2:
        k_0 = st.number_input("Коэфф. постели грунта k0, МН/м³", value=2.0)
        rho_ins = st.number_input("Плотность изоляции, кг/м³", value=1500.0)
        delta_ins = st.number_input("Толщина изоляции, мм", value=3.0)

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 2 * (delta_ins / 1000)

    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    rho_prod = 870.0 if st.session_state.product_type == "Нефть" else 0.8
    q_met = 78500 * F
    q_prod = rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4
    q_ins = rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4
    q_tr = q_met + q_prod + q_ins

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (0.8 * gamma_gr * (h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr) / D_ins_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_ins_m * tau_pr / 1e6
    q_v = (0.8 * gamma_gr * D_ins_m * (h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr) / 1e6

    N_cr_plast = 4.09 * math.sqrt(p0 * q_v * F * st.session_state.E * I)

    st.markdown("### Подробный расчет с пояснениями")

    st.write(
        "1. Вычисление геометрических характеристик сечения трубы (считаем площадь и момент инерции металлического кольца):")
    st.latex(
        rf"F = \frac{{\pi \cdot (D_н^2 - D_{{вн}}^2)}}{{4}} = \frac{{3.1416 \cdot ({D_H_m}^2 - {D_vn_m:.3f}^2)}}{{4}} = {F:.4f} \text{{ м}}^2")
    st.latex(
        rf"I = \frac{{\pi \cdot (D_н^4 - D_{{вн}}^4)}}{{64}} = \frac{{3.1416 \cdot ({D_H_m}^4 - {D_vn_m:.3f}^4)}}{{64}} = {I:.6f} \text{{ м}}^4")

    st.write("2. Сбор весовых нагрузок (металл, продукт, изоляция):")
    st.latex(
        rf"q_{{тр}} = q_{{мет}} + q_{{прод}} + q_{{из}} = {q_met:.0f} + {q_prod:.0f} + {q_ins:.0f} = {q_tr:.0f} \text{{ Н/м}}")

    st.write("3. Определение эквивалентного продольного сжимающего усилия S (вызывает продольный изгиб):")
    st.latex(
        rf"S = [(0.5 - \mu)\sigma_{{кц}} + \alpha E \Delta t] \cdot F = [(0.5 - 0.3) \cdot {sigma_kc:.2f} + {st.session_state.alpha} \cdot {st.session_state.E} \cdot {st.session_state.delta_t}] \cdot {F:.4f} = {S:.2f} \text{{ МН}}")

    st.write("4. Давление грунта и сопротивления (модель Прандтля-Кулона):")
    st.latex(
        rf"p_{{гр}} = \frac{{0.8 \cdot \gamma_{{гр}} \cdot (h_0 + D_{{н.и}}/2 - \pi D_{{н.и}}/8) + q_{{тр}}}}{{D_{{н.и}}}} = \frac{{0.8 \cdot {gamma_gr} \cdot ({h0} + {D_ins_m / 2:.3f} - \pi \cdot {D_ins_m}/8) + {q_tr:.0f}}}{{{D_ins_m}}} = {p_gr:.0f} \text{{ Па}}")
    st.latex(
        rf"\tau_{{пр}} = p_{{гр}} \cdot \tan(\varphi) = {p_gr:.0f} \cdot \tan({phi_deg}^\circ) = {tau_pr:.0f} \text{{ Па}}")
    st.latex(
        rf"p_0 = \pi \cdot D_{{н.и}} \cdot \tau_{{пр}} = 3.1416 \cdot {D_ins_m} \cdot {tau_pr:.0f} \cdot 10^{{-6}} = {p0:.4f} \text{{ МН/м}}")
    st.latex(
        rf"q_в = \frac{{0.8 \cdot \gamma_{{гр}} \cdot D_{{н.и}} \cdot (h_0 + D_{{н.и}}/2 - \pi D_{{н.и}}/8) + q_{{тр}}}}{{10^6}} = {q_v:.4f} \text{{ МН/м}}")

    st.write("5. Вычисление критической силы (наступление потери устойчивости):")
    st.latex(
        rf"N_{{кр}} = 4.09 \cdot \sqrt{{p_0 \cdot q_в \cdot F \cdot E \cdot I}} = 4.09 \cdot \sqrt{{{p0:.4f} \cdot {q_v:.4f} \cdot {F:.4f} \cdot {st.session_state.E} \cdot {I:.6f}}} = {N_cr_plast:.2f} \text{{ МН}}")

    S_allow = (st.session_state.m / 1.1) * N_cr_plast
    st.write("6. Проверка условия продольной устойчивости:")
    st.latex(
        rf"S \le \frac{{m}}{{1.1}} \cdot N_{{кр}} \rightarrow {S:.2f} \le \frac{{{st.session_state.m}}}{{1.1}} \cdot {N_cr_plast:.2f} = {S_allow:.2f} \text{{ МН}}")

    if S <= S_allow:
        st.markdown(
            f"<div class='result-block'>Условие выполняется: {S:.2f} МН ≤ {S_allow:.2f} МН. <br>Устойчивость подземного трубопровода ОБЕСПЕЧЕНА.</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='error-block'>Условие не выполняется: {S:.2f} МН > {S_allow:.2f} МН. <br>Устойчивость НЕ ОБЕСПЕЧЕНА. Требуется увеличить глубину заложения $h_0$ или применить утяжелители.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# ЭТАП 5: УСТОЙЧИВОСТЬ В НАСЫПИ
# ==============================================================================
elif page == "5. Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("5. Примеры 8.4 - 8.6. Устойчивость трубопровода в насыпи (болото)")
    st.markdown(
        "<div class='info-text'><b>Учебная справка:</b> При прокладке в наземной насыпи (на болотах) устойчивость зависит от геометрии самой насыпи. Здесь проверяются сразу три сценария: 1) прямолинейный участок (сжатие), 2) поворот по горизонтали (попытка трубы 'распрямиться' и сдвинуть насыпь в бок), 3) поворот по вертикали (выпучивание вверх через тонкий слой засыпки).</div>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        h0 = st.number_input("Высота слоя засыпки h0, м", value=1.0)
        q_gor_input = st.number_input("Суммарное боковое сопр. грунта E1+E2, МН/м", value=62.95)
    with col2:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=16000.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=36.0)
    with col3:
        rho_gor = st.number_input("Радиус гориз. поворота ρ, м", value=1400.0)
        alpha_v = st.number_input("Угол верт. поворота α_в, град", value=50.0)

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    rho_prod = 870.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 78500 * F + rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4 + 1500 * 9.81 * math.pi * (
                (D_H_m + 0.006) ** 2 - D_H_m ** 2) / 4

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    st.subheader("1. Прямолинейный участок в насыпи (Пример 8.4)")
    st.markdown(
        "<div class='info-text'>Продольное критическое усилие для насыпи считается с учетом бокового отпора грунта отвалов $q_{гор}$ (пассивное сопротивление грунта).</div>",
        unsafe_allow_html=True)
    p_gr = (0.8 * gamma_gr * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_H_m * tau_pr / 1e6

    N_cr_nas = 3.97 * math.sqrt(p0 * q_gor_input * F * st.session_state.E * I)
    st.latex(
        rf"N_{{кр}} = 3.97 \cdot \sqrt{{p_0 \cdot q_{{гор}} \cdot F \cdot E \cdot I}} = {N_cr_nas:.2f} \text{{ МН}}")
    if S <= (st.session_state.m / 1.1) * N_cr_nas:
        st.success(
            f"Устойчивость прямого участка в насыпи ОБЕСПЕЧЕНА (S = {S:.2f} МН ≤ {(st.session_state.m / 1.1) * N_cr_nas:.2f} МН)")
    else:
        st.error("Устойчивость прямого участка в насыпи НЕ обеспечена")

    st.subheader("2. Устойчивость на горизонтальном повороте (Пример 8.5)")
    st.markdown(
        "<div class='info-text'>Труба, изогнутая в горизонтальной плоскости, под давлением пытается выпрямиться. Возникает сдвигающая сила, направленная наружу кривой. Проверяем, удержит ли берма насыпи трубу от сдвига.</div>",
        unsafe_allow_html=True)
    q_sdv = 40.47  # Условно
    req_q = 1.25 * S / rho_gor
    st.latex(
        rf"q_{{треб}} = \frac{{1.25 \cdot S}}{{\rho}} = \frac{{1.25 \cdot {S:.2f}}}{{{rho_gor}}} = {req_q * 1000:.2f} \text{{ кН/м}}")
    if q_sdv >= req_q:
        st.success(
            f"Устойчивость поворота ОБЕСПЕЧЕНА (Фактическое сопротивление грунта сдвигу {q_sdv * 1000:.2f} кН/м > {req_q * 1000:.2f} кН/м)")
    else:
        st.error("Устойчивость горизонтального поворота НЕ обеспечена")

    st.subheader("3. Устойчивость на вертикальном повороте (Пример 8.6)")
    st.markdown(
        "<div class='info-text'>Труба, изогнутая выпуклостью вверх (например, на перегибе рельефа), под давлением пытается распрямиться и выскочить из траншеи вверх. Единственное, что ее держит — вес грунта засыпки.</div>",
        unsafe_allow_html=True)
    q_v = (0.8 * gamma_gr * D_H_m * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / 1e6
    k_alpha = math.sin(math.radians(alpha_v / 2)) + math.cos(math.radians(alpha_v / 2)) if alpha_v > 45 else 1.0
    req_q_v = 1.25 * S * k_alpha / rho_gor
    st.latex(rf"q_{{в\_треб}} = \frac{{1.25 \cdot S \cdot k_\alpha}}{{\rho}} = {req_q_v * 1000:.2f} \text{{ кН/м}}")
    if q_v >= req_q_v:
        st.success(
            f"Устойчивость вертикального поворота (выпуклостью вверх) обеспечена. Веса грунта над трубой (q_в = {q_v * 1000:.2f} кН/м) достаточно для удержания.")
    else:
        st.error("Труба 'выскочит' из насыпи вверх. Увеличьте радиус поворота или вес засыпки.")

# ==============================================================================
# ЭТАП 6: ПРОДОЛЬНЫЕ ПЕРЕМЕЩЕНИЯ
# ==============================================================================
elif page == "6. Пример 8.7: Продольные перемещения":
    st.title("6. Пример 8.7. Продольные перемещения свободного конца")
    st.markdown(
        "<div class='info-text'><b>Учебная справка:</b> Этот расчет позволяет определить, насколько трубопровод сдвинется в продольном направлении (например, при выходе на поверхность к крановому узлу или на надземном переходе) из-за температурного расширения и давления. Это критически важно в местах, где труба выходит на поверхность, чтобы не оторвало арматуру.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        k_i = st.number_input("Коэфф. постели при сдвиге k_и, МН/м³", value=8.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=36.0)
    with col2:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=16000.0)
        h0 = st.number_input("Глубина заложения h0, м", value=1.0)

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4

    rho_prod = 870.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 78500 * F + rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4 + 1500 * 9.81 * math.pi * (
                (D_H_m + 0.006) ** 2 - D_H_m ** 2) / 4

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (1.2 * gamma_gr * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg)) / 1e6  # МПа

    beta = math.sqrt(math.pi * D_H_m * k_i / (st.session_state.E * F))
    P_pr = tau_pr * math.pi * D_H_m / beta

    st.markdown("### Вычисления")
    st.write("1. Предельные касательные напряжения и эквивалентное усилие:")
    st.latex(
        rf"\tau_{{пр}} = p_{{гр}} \cdot \tan(\varphi) = {tau_pr * 1e6:.0f} \text{{ Па}} \quad S = {S:.2f} \text{{ МН}}")

    st.write("2. Коэффициент затухания (жесткость) и предельное удерживающее усилие грунта:")
    st.latex(rf"\beta = \sqrt{{\frac{{\pi \cdot D_н \cdot k_и}}{{E \cdot F}}}} = {beta:.4f} \text{{ 1/м}}")
    st.latex(rf"P_{{пр}} = \frac{{\tau_{{пр}} \cdot \pi \cdot D_н}}{{\beta}} = {P_pr:.3f} \text{{ МН}}")

    if S > P_pr:
        st.markdown(
            "<div class='error-block'>Усилие S > P_пр. Связь трубы с грунтом нарушена. Труба начинает скользить в грунте (формируется участок пластичной связи).</div>",
            unsafe_allow_html=True)
        p0 = math.pi * D_H_m * tau_pr
        l2 = (S - P_pr) / p0
        l1 = 3.5 / beta
        u_end = (tau_pr / k_i) + ((S ** 2 - P_pr ** 2) / (2 * math.pi * D_H_m * tau_pr * st.session_state.E * F))

        st.write("3. Длины зон деформации и перемещение свободного конца:")
        st.latex(rf"l_1 \text{{ (длина упругой зоны)}} = 3.5 / \beta = {l1:.1f} \text{{ м}}")
        st.latex(rf"l_2 \text{{ (длина зоны скольжения)}} = \frac{{S - P_{{пр}}}}{{p_0}} = {l2:.1f} \text{{ м}}")
        st.markdown(f"<div class='result-block'>Полное перемещение свободного конца: u = {u_end * 1000:.1f} мм</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<div class='result-block'>Связь трубы с грунтом полностью упругая (S ≤ P_пр). Сдвигов нет.</div>",
                    unsafe_allow_html=True)