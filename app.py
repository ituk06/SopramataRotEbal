import streamlit as st
import math
import os
import pandas as pd
import plotly.express as px

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Сопромат Трубопроводов (Учебный комплекс)", page_icon="🛢️", layout="wide")

st.markdown("""
    <style>
    .math-block { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; font-family: 'Courier New', monospace; font-size: 1.1em; margin-bottom: 10px; overflow-x: auto;}
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .error-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; margin-bottom: 20px;}
    .info-text { font-size: 1.05em; color: #34495E; margin-bottom: 10px; line-height: 1.6;}
    </style>
""", unsafe_allow_html=True)

# Сортамент толщин стенок труб (мм)
SORTAMENT = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 15.7, 16.0, 17.5, 18.7, 19.1, 20.0, 21.0, 22.0, 23.0,
             24.0, 25.0, 26.0, 27.0, 28.0, 30.0, 32.0, 34.0, 36.0]

# Расширенная база климатических данных для интерактивной карты
CLIMATE_DATA = {
    "г. Губкинский (ЯНАО)": {"t_min": -50.0, "t_max": 30.0, "lat": 64.434, "lon": 76.5026},
    "г. Сургут (ХМАО)": {"t_min": -43.0, "t_max": 26.0, "lat": 61.25, "lon": 73.4167},
    "г. Уфа (Башкортостан)": {"t_min": -35.0, "t_max": 28.0, "lat": 54.7388, "lon": 55.9721},
    "г. Казань (Татарстан)": {"t_min": -32.0, "t_max": 30.0, "lat": 55.7903, "lon": 49.1204},
    "г. Якутск": {"t_min": -54.0, "t_max": 30.0, "lat": 62.0339, "lon": 129.733},
    "г. Оренбург": {"t_min": -31.0, "t_max": 30.0, "lat": 51.7666, "lon": 55.1005},
    "г. Москва": {"t_min": -28.0, "t_max": 28.0, "lat": 55.7558, "lon": 37.6173},
    "г. Новосибирск": {"t_min": -39.0, "t_max": 29.0, "lat": 55.0084, "lon": 82.9357},
    "г. Иркутск": {"t_min": -36.0, "t_max": 28.0, "lat": 52.2978, "lon": 104.296},
    "г. Владивосток": {"t_min": -24.0, "t_max": 27.0, "lat": 43.1198, "lon": 131.886},
    "г. Норильск": {"t_min": -47.0, "t_max": 24.0, "lat": 69.3558, "lon": 88.1893},
    "г. Тюмень": {"t_min": -35.0, "t_max": 27.0, "lat": 57.1522, "lon": 65.5272},
    "г. Астрахань": {"t_min": -23.0, "t_max": 33.0, "lat": 46.3497, "lon": 48.0326},
}


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

st.sidebar.title("🛢️ Навигация по расчету")
page = st.sidebar.radio("Выберите этап:", [
    "1. Климатология (Интерактивная карта)",
    "2. Пример 8.1: Толщина стенки",
    "3. Пример 8.2: Проверка прочности",
    "4. Пример 8.3: Продольная устойчивость",
    "5. Примеры 8.4-8.6: Устойчивость в насыпи",
    "6. Пример 8.7: Продольные перемещения"
])

st.sidebar.markdown("---")
st.sidebar.info(f"**Текущая толщина стенки в памяти:**\n\nδ_н = {st.session_state.delta_n} мм")


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
if page == "1. Климатология (Интерактивная карта)":
    st.title("1. Определение расчетного температурного перепада (Δt)")
    st.markdown(
        "<div class='info-text'>Температурный перепад $\Delta t$ — это разница между температурой эксплуатации и температурой, при которой трубу сваривали (замыкали) в траншее. Здесь вы можете выбрать регион на интерактивной карте, и программа сама подтянет климатические данные по СНиП 23-01-99.</div>",
        unsafe_allow_html=True)

    st.markdown("### 🗺️ Интерактивная тепловая карта районов строительства")

    # Отрисовка карты с помощью Plotly (исправлена ошибка цвета ice -> px.colors.sequential.ice)
    df_map = pd.DataFrame.from_dict(CLIMATE_DATA, orient='index').reset_index()
    df_map.rename(columns={'index': 'Город'}, inplace=True)
    fig = px.scatter_mapbox(df_map, lat="lat", lon="lon", hover_name="Город",
                            hover_data={"t_min": True, "t_max": True, "lat": False, "lon": False},
                            color="t_min", color_continuous_scale=px.colors.sequential.ice,
                            size_max=15, zoom=2.5, mapbox_style="carto-positron",
                            title="Тепловая карта минимальных температур (синий = холоднее)")
    fig.update_traces(marker=dict(size=12))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Ввод данных для расчета температур")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.product_type = st.radio("Тип транспортируемого продукта:", ["Нефть", "Газ"],
                                                 index=0 if st.session_state.product_type == "Нефть" else 1)
        t_product_default = 5.0 if st.session_state.product_type == "Нефть" else 6.0
        st.session_state.t_product = st.number_input("Температура эксплуатации продукта (t_э), °C",
                                                     value=t_product_default)

        region = st.selectbox("Выберите район из базы (данные подставятся автоматически):",
                              list(CLIMATE_DATA.keys()) + ["Задать вручную"])
        if region != "Задать вручную":
            t_max_val = CLIMATE_DATA[region]["t_max"]
            t_min_val = CLIMATE_DATA[region]["t_min"]
        else:
            t_max_val = 30.0
            t_min_val = -50.0

        t_max_map = st.number_input("Максимальная температура (t_max), °C", value=t_max_val)
        t_min_map = st.number_input("Минимальная температура (t_min), °C", value=t_min_val)

    with col2:
        st.markdown(
            "<div class='info-text'><b>Логика расчета:</b> При отсутствии точных данных о дате сварки стыков, нормативная температура замыкания берется с запасом: летом на 3°C выше максимума ($t_m$), зимой на 6°C ниже минимума ($t_x$).</div>",
            unsafe_allow_html=True)
        t_x = t_min_map - 6.0
        t_m = t_max_map + 3.0
        dt_x = st.session_state.t_product - t_x
        dt_m = st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.latex(rf"t_x = t_{{min}} - 6^\circ C = {t_min_map} - 6 = \mathbf{{{t_x}^\circ C}} \text{{ (Зима)}}")
        st.latex(rf"t_m = t_{{max}} + 3^\circ C = {t_max_map} + 3 = \mathbf{{{t_m}^\circ C}} \text{{ (Лето)}}")
        st.latex(rf"\Delta t_x = t_{{э}} - t_x = {st.session_state.t_product} - ({t_x}) = \mathbf{{{dt_x}^\circ C}}")
        st.latex(rf"\Delta t_m = t_{{э}} - t_m = {st.session_state.t_product} - ({t_m}) = \mathbf{{{dt_m}^\circ C}}")

        st.success(f"**Расчетный (наихудший) температурный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить Δt"):
            st.session_state.delta_t = calc_dt

    with st.expander("Посмотреть оригинальные карты из СНиП"):
        img = find_image("Снимок экрана 2026-10-09 в 00.49.04") or find_image("map_max")
        if img: st.image(img, caption="Карта максимальных температур", use_container_width=True)
        img2 = find_image("Снимок экрана 2026-10-09 в 00.49.13") or find_image("map_min")
        if img2: st.image(img2, caption="Карта минимальных температур", use_container_width=True)

# ==============================================================================
# ЭТАП 2: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "2. Пример 8.1: Толщина стенки":
    st.title("Пример 8.1. Определение расчетной толщины стенки")
    st.markdown(
        "<div class='info-text'>Здесь мы определяем минимально необходимую толщину стенки трубы по безмоментной теории оболочек (формула котла) от воздействия только внутреннего давления продукта. Это базовая величина, которую мы затем будем проверять на продольные напряжения.</div>",
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

    delta_nom = get_next_thickness(delta_calc, min_thickness=12.0 if st.session_state.D_H >= 1000 else 4.0)

    st.markdown("### Пошаговый расчет с пояснениями")
    st.markdown(
        "<div class='info-text'>1. Находим расчетные сопротивления материала труб $R_1$ (по пределу прочности) и $R_2$ (по пределу текучести). Для этого нормативные значения умножаем на коэффициент условий работы $m$ и делим на коэффициенты надежности.</div>",
        unsafe_allow_html=True)
    st.latex(
        rf"R_1 = \frac{{R_1^н \cdot m}}{{k_1 \cdot k_н}} = \frac{{{st.session_state.R1_n} \cdot {st.session_state.m}}}{{{st.session_state.k1} \cdot {st.session_state.k_H}}} = \mathbf{{{R1:.2f} \text{{ МПа}}}}")
    st.latex(
        rf"R_2 = \frac{{R_2^н \cdot m}}{{k_2 \cdot k_н}} = \frac{{{st.session_state.R2_n} \cdot {st.session_state.m}}}{{{st.session_state.k2} \cdot {st.session_state.k_H}}} = \mathbf{{{R2:.2f} \text{{ МПа}}}}")

    st.markdown(
        "<div class='info-text'>2. Определяем расчетную толщину стенки $\delta$. Это чисто теоретическое значение.</div>",
        unsafe_allow_html=True)
    st.latex(
        rf"\delta = \frac{{n_p \cdot p \cdot D_н}}{{2(R_1 + n_p \cdot p)}} = \frac{{{n_p} \cdot {st.session_state.P} \cdot {st.session_state.D_H}}}{{2({R1:.2f} + {n_p} \cdot {st.session_state.P})}} = \mathbf{{{delta_calc:.2f} \text{{ мм}}}}")

    st.markdown(
        f"<div class='result-block'>3. Согласно требованиям, округляем полученное значение в большую сторону до ближайшего по ГОСТ/ТУ. Для труб $D_N \ge 1000$ мм толщина не может быть меньше 12 мм.<br><br><b>Принятая предварительная толщина стенки: δ_н = {delta_nom:.1f} мм</b></div>",
        unsafe_allow_html=True)

    if st.button("Сохранить и перейти к проверке прочности"):
        st.session_state.delta_n = delta_nom
        st.rerun()

# ==============================================================================
# ЭТАП 3: ПРОВЕРКА ПРОЧНОСТИ (ОБЪЕДИНЕННАЯ)
# ==============================================================================
elif page == "3. Пример 8.2: Проверка прочности":
    st.title("Пример 8.2. Проверка прочности трубопровода")
    st.markdown(
        "<div class='info-text'>Подземный трубопровод зажат в грунте. При изменении температуры металла или давления он стремится изменить свою длину, но грунт ему не дает. Из-за этого в трубе возникают огромные <b>продольные напряжения</b>. В этом разделе мы проверяем, выдержит ли металл совместное воздействие кольцевых (распирающих) и продольных напряжений.</div>",
        unsafe_allow_html=True)

    tab_manual, tab_auto = st.tabs(["🖐️ Ручная проверка (Один расчет)", "🚀 Итерационный Автоподбор"])

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

        st.markdown(
            "<div class='info-text'><b>1. Кольцевые напряжения от нормативного давления:</b><br>Это напряжения, которые растягивают трубу по кругу. Они не должны превышать допускаемое значение.</div>",
            unsafe_allow_html=True)
        st.latex(
            rf"\sigma_{{кц}}^н = \frac{{p \cdot D_{{вн}}}}{{2\delta_н}} = \frac{{{st.session_state.P} \cdot {D_vn}}}{{2 \cdot {check_delta}}} = \mathbf{{{sig_kc:.2f} \text{{ МПа}}}}")
        st.latex(
            rf"[\sigma_{{кц}}] = \frac{{m}}{{0.9 \cdot k_н}} \cdot R_2^н = \frac{{{st.session_state.m}}}{{0.9 \cdot {st.session_state.k_H}}} \cdot {st.session_state.R2_n} = \mathbf{{{sig_kc_allow:.2f} \text{{ МПа}}}}")

        if sig_kc <= sig_kc_allow:
            st.markdown(
                f"**Условие 3.21 ($\sigma_{{кц}}^н \le [\sigma_{{кц}}]$):** <span style='color:green'>ВЫПОЛНЯЕТСЯ ✅ (TRUE)</span>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"**Условие 3.21 ($\sigma_{{кц}}^н \le [\sigma_{{кц}}]$):** <span style='color:red'>НЕ ВЫПОЛНЯЕТСЯ ❌ (FALSE)</span>",
                unsafe_allow_html=True)

        st.markdown(
            "<div class='info-text'><b>2. Продольные напряжения от нормативных нагрузок:</b><br>Здесь учитывается температурный перепад $\Delta t$ и эффект Пуассона $\mu$ от кольцевых напряжений.</div>",
            unsafe_allow_html=True)
        st.latex(
            rf"\sigma_{{пр}}^н = -\alpha \cdot E \cdot \Delta t + \mu \cdot \sigma_{{кц}}^н = -{st.session_state.alpha} \cdot {st.session_state.E} \cdot {check_dt} + {st.session_state.mu} \cdot {sig_kc:.2f} = \mathbf{{{sig_pr:.2f} \text{{ МПа}}}}")

        st.markdown(
            "<div class='info-text'><b>3. Учет двухосного напряженного состояния:</b><br>Поскольку труба испытывает сжатие ($\sigma_{{пр}}^н < 0$), прочность металла снижается. Это учитывается коэффициентом $\psi_1$.</div>",
            unsafe_allow_html=True)
        st.latex(
            rf"\psi_1 = \sqrt{{1 - 0.75 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right)^2}} - 0.5 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right) = \sqrt{{1 - 0.75 \left(\frac{{{sig_kc:.2f}}}{{{sig_kc_allow:.2f}}}\right)^2}} - 0.5 \left(\frac{{{sig_kc:.2f}}}{{{sig_kc_allow:.2f}}}\right) = \mathbf{{{psi:.4f}}}")
        st.latex(
            rf"[\sigma_{{пр}}] = \psi_1 \cdot [\sigma_{{кц}}] = {psi:.4f} \cdot {sig_kc_allow:.2f} = \mathbf{{{sig_pr_allow:.2f} \text{{ МПа}}}}")

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
            if st.button("Зафиксировать эту толщину для следующих расчетов"):
                st.session_state.delta_n = check_delta
                st.rerun()
        else:
            st.error(f"При толщине {check_delta} мм труба не выдерживает нагрузок. Требуется увеличить толщину.")

    # --- АВТОПОДБОР ---
    with tab_auto:
        st.subheader("Итерационный автоподбор толщины стенки")
        st.markdown(
            "<div class='info-text'>Если при первичной толщине труба не выдерживает продольных напряжений, алгоритм автоматически начнет перебирать стандартные толщины по ГОСТ в сторону увеличения, пока оба условия не станут <b>TRUE</b>.</div>",
            unsafe_allow_html=True)

        if st.button("🚀 Запустить алгоритм автоподбора"):
            current_delta = st.session_state.delta_n
            iteration = 1
            while True:
                is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(current_delta,
                                                                                        st.session_state.delta_t)

                with st.expander(f"Итерация {iteration}. Проверка δ_н = {current_delta} мм",
                                 expanded=True if is_ok else False):
                    st.write(
                        f"1) Условие кольцевых напряжений: $\sigma_{{кц}} = {sig_kc:.2f}$ МПа $\le$ $[\sigma_{{кц}}] = {sig_kc_allow:.2f}$ МПа $\\rightarrow$ **{'ОК' if sig_kc <= sig_kc_allow else 'FAIL'}**")
                    st.write(
                        f"2) Условие продольных напряжений: $|\sigma_{{пр}}| = {abs(sig_pr):.2f}$ МПа $\le$ $[\sigma_{{пр}}] = {sig_pr_allow:.2f}$ МПа $\\rightarrow$ **{'ОК' if abs(sig_pr) <= sig_pr_allow else 'FAIL'}**")

                if is_ok:
                    st.success(
                        f"**РАСЧЕТ УСПЕШНО ОКОНЧЕН. Окончательная толщина стенки подобрана: {current_delta} мм.**")
                    st.session_state.delta_n = current_delta

                    st.markdown("---")
                    st.markdown("### Определение радиуса упругого изгиба")
                    D_vn_m = (st.session_state.D_H - 2 * current_delta) / 1000
                    rho_min = 1000 * D_vn_m
                    st.markdown(
                        "<div class='info-text'>Согласно п.8.3, минимальный радиус упругого изгиба трубопровода из условия беспрепятственного прохождения внутритрубных очистных устройств (СОД) должен составлять не менее 1000 внутренних диаметров трубы ($\rho_{min} = 1000 \cdot D_{вн}$).</div>",
                        unsafe_allow_html=True)
                    st.latex(
                        rf"\rho_{{min}} = 1000 \cdot D_{{вн}} = 1000 \cdot {D_vn_m:.3f} = \mathbf{{{rho_min:.1f} \text{{ м}}}}")
                    break
                else:
                    st.warning(
                        f"Условие не выполнилось для {current_delta} мм. Берем следующую толщину по сортаменту...")
                    current_delta = get_next_thickness(current_delta + 0.1)
                    iteration += 1

# ==============================================================================
# ЭТАП 4: УСТОЙЧИВОСТЬ ПРЯМОГО УЧАСТКА
# ==============================================================================
elif page == "4. Пример 8.3: Продольная устойчивость":
    st.title("Пример 8.3. Расчет продольной устойчивости (Прямой участок)")
    st.info(f"**Используется окончательная толщина стенки:** δ_н = {st.session_state.delta_n} мм")
    st.markdown(
        "<div class='info-text'>Подземный трубопровод, сжатый продольными силами от температуры и давления, может потерять устойчивость (выпучиться из земли вверх), если вес засыпающего его грунта окажется недостаточным. Здесь мы определяем, выдержит ли труба это воздействие.</div>",
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

    st.write("1. Вычисление геометрических характеристик сечения трубы:")
    st.latex(
        rf"F = \frac{{\pi \cdot (D_н^2 - D_{{вн}}^2)}}{{4}} = \frac{{3.1416 \cdot ({D_H_m}^2 - {D_vn_m:.3f}^2)}}{{4}} = \mathbf{{{F:.4f} \text{{ м}}^2}}")
    st.latex(
        rf"I = \frac{{\pi \cdot (D_н^4 - D_{{вн}}^4)}}{{64}} = \frac{{3.1416 \cdot ({D_H_m}^4 - {D_vn_m:.3f}^4)}}{{64}} = \mathbf{{{I:.6f} \text{{ м}}^4}}")

    st.write("2. Сбор весовых нагрузок (металл, продукт, изоляция):")
    st.latex(
        rf"q_{{тр}} = q_{{мет}} + q_{{прод}} + q_{{из}} = {q_met:.0f} + {q_prod:.0f} + {q_ins:.0f} = \mathbf{{{q_tr:.0f} \text{{ Н/м}}}}")

    st.write("3. Определение эквивалентного продольного сжимающего усилия $S$:")
    st.latex(
        rf"S = [(0.5 - \mu)\sigma_{{кц}} + \alpha E \Delta t] \cdot F = [(0.5 - 0.3) \cdot {sigma_kc:.2f} + {st.session_state.alpha} \cdot {st.session_state.E} \cdot {st.session_state.delta_t}] \cdot {F:.4f} = \mathbf{{{S:.2f} \text{{ МН}}}}")

    st.write("4. Давление грунта и сопротивления (жесткопластичная модель сдвига):")
    st.latex(
        rf"p_{{гр}} = \frac{{0.8 \cdot \gamma_{{гр}} \cdot (h_0 + D_{{н.и}}/2 - \pi D_{{н.и}}/8) + q_{{тр}}}}{{D_{{н.и}}}} = \frac{{0.8 \cdot {gamma_gr} \cdot ({h0} + {D_ins_m / 2:.3f} - \pi \cdot {D_ins_m}/8) + {q_tr:.0f}}}{{{D_ins_m}}} = \mathbf{{{p_gr:.0f} \text{{ Па}}}}")
    st.latex(
        rf"\tau_{{пр}} = p_{{гр}} \cdot \tan(\varphi) = {p_gr:.0f} \cdot \tan({phi_deg}^\circ) = \mathbf{{{tau_pr:.0f} \text{{ Па}}}}")
    st.latex(
        rf"p_0 = \pi \cdot D_{{н.и}} \cdot \tau_{{пр}} = 3.1416 \cdot {D_ins_m} \cdot {tau_pr:.0f} \cdot 10^{{-6}} = \mathbf{{{p0:.4f} \text{{ МН/м}}}}")
    st.latex(
        rf"q_в = \frac{{0.8 \cdot \gamma_{{гр}} \cdot D_{{н.и}} \cdot (h_0 + D_{{н.и}}/2 - \pi D_{{н.и}}/8) + q_{{тр}}}}{{10^6}} = \mathbf{{{q_v:.4f} \text{{ МН/м}}}}")

    st.write("5. Вычисление критической силы выпучивания $N_{кр}$:")
    st.latex(
        rf"N_{{кр}} = 4.09 \cdot \sqrt{{p_0 \cdot q_в \cdot F \cdot E \cdot I}} = 4.09 \cdot \sqrt{{{p0:.4f} \cdot {q_v:.4f} \cdot {F:.4f} \cdot {st.session_state.E} \cdot {I:.6f}}} = \mathbf{{{N_cr_plast:.2f} \text{{ МН}}}}")

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
            f"<div class='error-block'>Условие не выполняется: {S:.2f} МН > {S_allow:.2f} МН. <br>Устойчивость НЕ ОБЕСПЕЧЕНА. Требуется увеличить глубину заложения $h_0$ или выполнить балластировку (пригрузы).</div>",
            unsafe_allow_html=True)

# ==============================================================================
# ЭТАП 5: УСТОЙЧИВОСТЬ В НАСЫПИ
# ==============================================================================
elif page == "5. Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("Примеры 8.4 - 8.6. Устойчивость трубопровода в насыпи (болото)")
    st.markdown(
        "<div class='info-text'>В данном разделе выполняется комплексная проверка трубопровода, уложенного в наземную насыпь (часто применяется на болотах). Проверяется прямой участок на продольное выпучивание, а также криволинейные участки (повороты) на сдвиг в бок и вверх.</div>",
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
        "<div class='info-text'>Критическая сила для насыпи считается с учетом бокового отпора грунта отвалов $q_{гор}$.</div>",
        unsafe_allow_html=True)
    p_gr = (0.8 * gamma_gr * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_H_m * tau_pr / 1e6

    N_cr_nas = 3.97 * math.sqrt(p0 * q_gor_input * F * st.session_state.E * I)
    st.latex(
        rf"N_{{кр}} = 3.97 \cdot \sqrt{{p_0 \cdot q_{{гор}} \cdot F \cdot E \cdot I}} = \mathbf{{{N_cr_nas:.2f} \text{{ МН}}}}")
    if S <= (st.session_state.m / 1.1) * N_cr_nas:
        st.success(
            f"Устойчивость прямого участка в насыпи обеспечена (S = {S:.2f} МН ≤ {(st.session_state.m / 1.1) * N_cr_nas:.2f} МН)")
    else:
        st.error("Устойчивость прямого участка в насыпи НЕ обеспечена")

    st.subheader("2. Устойчивость на горизонтальном повороте (Пример 8.5)")
    st.markdown(
        "<div class='info-text'>Труба, изогнутая в горизонтальной плоскости, под давлением пытается выпрямиться и сдвинуть насыпь вбок. Проверяем, удержит ли грунт трубу.</div>",
        unsafe_allow_html=True)
    q_sdv = 40.47  # Условно
    req_q = 1.25 * S / rho_gor
    st.latex(
        rf"q_{{треб}} = \frac{{1.25 \cdot S}}{{\rho}} = \frac{{1.25 \cdot {S:.2f}}}{{{rho_gor}}} = \mathbf{{{req_q * 1000:.2f} \text{{ кН/м}}}}")
    if q_sdv >= req_q:
        st.success(
            f"Устойчивость поворота обеспечена (Фактическое сопротивление грунта сдвигу {q_sdv * 1000:.2f} кН/м > {req_q * 1000:.2f} кН/м)")
    else:
        st.error("Устойчивость горизонтального поворота НЕ обеспечена")

    st.subheader("3. Устойчивость на вертикальном повороте (Пример 8.6)")
    st.markdown(
        "<div class='info-text'>Труба, изогнутая вверх (например, на перегибе рельефа), под давлением пытается выскочить из траншеи вверх.</div>",
        unsafe_allow_html=True)
    q_v = (0.8 * gamma_gr * D_H_m * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / 1e6
    k_alpha = math.sin(math.radians(alpha_v / 2)) + math.cos(math.radians(alpha_v / 2)) if alpha_v > 45 else 1.0
    req_q_v = 1.25 * S * k_alpha / rho_gor
    st.latex(
        rf"q_{{в\_треб}} = \frac{{1.25 \cdot S \cdot k_\alpha}}{{\rho}} = \mathbf{{{req_q_v * 1000:.2f} \text{{ кН/м}}}}")
    if q_v >= req_q_v:
        st.success(
            f"Устойчивость вертикального поворота (выпуклостью вверх) обеспечена. Веса грунта q_в = {q_v * 1000:.2f} кН/м достаточно.")
    else:
        st.error("Труба 'выскочит' из насыпи вверх. Увеличьте радиус поворота или вес засыпки.")

# ==============================================================================
# ЭТАП 6: ПРОДОЛЬНЫЕ ПЕРЕМЕЩЕНИЯ
# ==============================================================================
elif page == "6. Пример 8.7: Продольные перемещения":
    st.title("Пример 8.7. Продольные перемещения свободного конца")
    st.markdown(
        "<div class='info-text'>Расчет позволяет определить, насколько трубопровод сдвинется в продольном направлении (например, при выходе на поверхность к крановому узлу или на надземном переходе) из-за температурного расширения и давления.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        k_i = st.number_input("Коэфф. постели при сдвиге k_и, МН/м³", value=8.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=36.0)
    with col2:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=16000.0)
        h0 = st.number_input("Глубина заложения h0, м", value=1.0)

    # Подтягиваем геометрию
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
    st.latex(rf"\tau_{{пр}} = \mathbf{{{tau_pr * 1e6:.0f} \text{{ Па}}}} \quad S = \mathbf{{{S:.2f} \text{{ МН}}}}")

    st.write("2. Коэффициент затухания и предельное удерживающее усилие грунта:")
    st.latex(rf"\beta = \sqrt{{\frac{{\pi \cdot D_н \cdot k_и}}{{E \cdot F}}}} = \mathbf{{{beta:.4f} \text{{ 1/м}}}}")
    st.latex(rf"P_{{пр}} = \frac{{\tau_{{пр}} \cdot \pi \cdot D_н}}{{\beta}} = \mathbf{{{P_pr:.3f} \text{{ МН}}}}")

    if S > P_pr:
        st.markdown(
            "<div class='error-block'>Усилие S > P_пр. Связь трубы с грунтом нарушена (срыв). Формируется участок пластичной связи (проскальзывание).</div>",
            unsafe_allow_html=True)
        p0 = math.pi * D_H_m * tau_pr
        l2 = (S - P_pr) / p0
        l1 = 3.5 / beta
        u_end = (tau_pr / k_i) + ((S ** 2 - P_pr ** 2) / (2 * math.pi * D_H_m * tau_pr * st.session_state.E * F))

        st.write("3. Длины зон деформации и перемещение:")
        st.latex(rf"l_1 \text{{ (упругая зона)}} = 3.5 / \beta = \mathbf{{{l1:.1f} \text{{ м}}}}")
        st.latex(rf"l_2 \text{{ (зона скольжения)}} = (S - P_{{пр}}) / p_0 = \mathbf{{{l2:.1f} \text{{ м}}}}")
        st.markdown(f"<div class='result-block'>Полное перемещение свободного конца: u = {u_end * 1000:.1f} мм</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<div class='result-block'>Связь трубы с грунтом полностью упругая (S ≤ P_пр). Сдвигов нет.</div>",
                    unsafe_allow_html=True)