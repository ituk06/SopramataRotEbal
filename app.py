import streamlit as st
import math
import os

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
page = st.sidebar.radio("Выберите раздел:", [
    "0. Климатология и Нагрузки",
    "1. Пример 8.1: Толщина стенки",
    "2. Пример 8.2: Проверка прочности (Ручная)",
    "3. Автоподбор толщины стенки",
    "4. Пример 8.3: Устойчивость прямого участка",
    "5. Примеры 8.4-8.6: Устойчивость в насыпи",
    "6. Пример 8.7: Продольные перемещения"
])

st.sidebar.markdown("---")
st.sidebar.info(f"**Текущая толщина стенки в памяти:** {st.session_state.delta_n} мм")


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


# ==============================================================================
# ЭТАП 0: КЛИМАТОЛОГИЯ И НАГРУЗКИ
# ==============================================================================
if page == "0. Климатология и Нагрузки":
    st.title("Определение расчетного температурного перепада (Δt)")
    st.markdown(
        "<div class='info-text'>Согласно СП 36.13330.2012, температурный перепад в металле стенок труб принимается как разница между максимально (или минимально) возможной температурой эксплуатации и температурой, при которой фиксируется расчетная схема (замыкание трубопровода). Для определения этих температур используются климатические карты СП 131.13330.</div>",
        unsafe_allow_html=True)

    st.markdown("### 🗺️ Визуализация климатических карт")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Макс. Температура", "Мин. Температура", "Снег", "Ветер", "Гололед"])

    with tab1:
        if os.path.exists("Снимок экрана 2026-10-09 в 00.49.04.jpg"):
            st.image("Снимок экрана 2026-10-09 в 00.49.04.jpg", use_container_width=True)
        else:
            st.warning("Карта максимальных температур не найдена.")
    with tab2:
        if os.path.exists("Снимок экрана 2026-10-09 в 00.49.13.jpg"):
            st.image("Снимок экрана 2026-10-09 в 00.49.13.jpg", use_container_width=True)
        else:
            st.warning("Карта минимальных температур не найдена.")
    with tab3:
        if os.path.exists("Снимок экрана 2026-10-09 в 00.49.19.jpg"):
            st.image("Снимок экрана 2026-10-09 в 00.49.19.jpg", use_container_width=True)
        else:
            st.warning("Карта снеговых нагрузок не найдена.")
    with tab4:
        if os.path.exists("Снимок экрана 2026-10-09 в 00.49.27.jpg"):
            st.image("Снимок экрана 2026-10-09 в 00.49.27.jpg", use_container_width=True)
        else:
            st.warning("Карта ветровых нагрузок не найдена.")
    with tab5:
        if os.path.exists("Снимок экрана 2026-10-09 в 00.49.35.jpg"):
            st.image("Снимок экрана 2026-10-09 в 00.49.35.jpg", use_container_width=True)
        else:
            st.warning("Карта гололедных нагрузок не найдена.")

    st.markdown("### Ввод данных для расчета температур")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.product_type = st.radio("Тип транспортируемого продукта:", ["Нефть", "Газ"],
                                                 index=0 if st.session_state.product_type == "Нефть" else 1)

        # Автоматическая логика температуры продукта
        t_product_default = 5.0 if st.session_state.product_type == "Нефть" else 6.0
        st.session_state.t_product = st.number_input("Температура эксплуатации продукта (t_э), °C",
                                                     value=t_product_default)

        t_max_map = st.number_input("Максимальная температура по карте (t_max), °C", value=30.0)
        t_min_map = st.number_input("Минимальная температура по карте (t_min), °C", value=-50.0)

    with col2:
        st.markdown(
            "<div class='info-text'>При отсутствии точных данных о дате замыкания, нормативная температура замыкания берется с запасом: летом на 3 градуса выше максимума, зимой на 6 градусов ниже минимума.</div>",
            unsafe_allow_html=True)
        t_x = t_min_map - 6.0
        t_m = t_max_map + 3.0
        dt_x = st.session_state.t_product - t_x
        dt_m = st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.latex(rf"t_x = t_{{min}} - 6^\circ C = {t_min_map} - 6 = {t_x}^\circ C")
        st.latex(rf"t_m = t_{{max}} + 3^\circ C = {t_max_map} + 3 = {t_m}^\circ C")
        st.latex(rf"\Delta t_x = t_{{э}} - t_x = {st.session_state.t_product} - ({t_x}) = {dt_x}^\circ C")
        st.latex(rf"\Delta t_m = t_{{э}} - t_m = {st.session_state.t_product} - ({t_m}) = {dt_m}^\circ C")

        st.success(f"**Расчетный (наихудший) температурный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить Δt"):
            st.session_state.delta_t = calc_dt

# ==============================================================================
# ЭТАП 1: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "1. Пример 8.1: Толщина стенки":
    st.title("Пример 8.1. Определение расчетной толщины стенки")
    st.markdown(
        "<div class='info-text'>Расчет толщины стенки трубы производится по первому предельному состоянию (на прочность) от воздействия внутреннего давления. Это базовое значение, которое в дальнейшем будет проверяться на совместное действие нагрузок.</div>",
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

    delta_nom = get_next_thickness(delta_calc, min_thickness=4.0)

    st.markdown("### Пошаговый расчет")
    st.write("**1. Расчетные сопротивления металла труб:**")
    st.markdown(
        "<div class='info-text'>Нормативные сопротивления (предел текучести и предел прочности) делятся на коэффициенты надежности по материалу и ответственности, чтобы получить расчетные значения для формул.</div>",
        unsafe_allow_html=True)
    st.latex(
        rf"R_1 = \frac{{R_1^н \cdot m}}{{k_1 \cdot k_н}} = \frac{{{st.session_state.R1_n} \cdot {st.session_state.m}}}{{{st.session_state.k1} \cdot {st.session_state.k_H}}} = {R1:.2f} \text{{ МПа}}")
    st.latex(
        rf"R_2 = \frac{{R_2^н \cdot m}}{{k_2 \cdot k_н}} = \frac{{{st.session_state.R2_n} \cdot {st.session_state.m}}}{{{st.session_state.k2} \cdot {st.session_state.k_H}}} = {R2:.2f} \text{{ МПа}}")

    st.write("**2. Расчетная толщина стенки:**")
    st.latex(
        rf"\delta = \frac{{n_p \cdot p \cdot D_н}}{{2(R_1 + n_p \cdot p)}} = \frac{{{n_p} \cdot {st.session_state.P} \cdot {st.session_state.D_H}}}{{2({R1:.2f} + {n_p} \cdot {st.session_state.P})}} = {delta_calc:.2f} \text{{ мм}}")

    st.markdown(
        f"<div class='result-block'>Принятая по ГОСТ предварительная толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
        unsafe_allow_html=True)

    if st.button("Сохранить и перейти к проверке прочности"):
        st.session_state.delta_n = delta_nom

# ==============================================================================
# ЭТАП 2: РУЧНАЯ ПРОВЕРКА ПРОЧНОСТИ
# ==============================================================================
elif page == "2. Пример 8.2: Проверка прочности (Ручная)":
    st.title("Пример 8.2. Проверка прочности (Ручной режим)")
    st.markdown(
        "<div class='info-text'>Здесь вы можете вручную задать толщину стенки (например, ту, что получили в Примере 8.1) и посмотреть, выполняются ли условия прочности. Если условие не выполняется, трубопровод может деформироваться или разрушиться при эксплуатации.</div>",
        unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        check_delta = st.number_input("Проверяемая толщина стенки δ_н, мм", value=float(st.session_state.delta_n),
                                      step=1.0)
    with col2:
        check_dt = st.number_input("Расчетный темп. перепад Δt, °C", value=st.session_state.delta_t)

    is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(check_delta, check_dt)

    st.markdown("### Результаты проверки:")
    st.write("Кольцевые напряжения (от давления продукта изнутри):")
    st.latex(
        rf"\sigma_{{кц}}^н = \frac{{p \cdot D_{{вн}}}}{{2\delta_н}} = {sig_kc:.2f} \text{{ МПа}} \quad \text{{(Допускаемое: }} {sig_kc_allow:.2f} \text{{ МПа)}}")

    if sig_kc <= sig_kc_allow:
        st.markdown("**Условие 3.21 (σ_кц ≤ [σ_кц]): <span style='color:green'>ВЫПОЛНЯЕТСЯ ✅</span>**",
                    unsafe_allow_html=True)
    else:
        st.markdown("**Условие 3.21 (σ_кц ≤ [σ_кц]): <span style='color:red'>НЕ ВЫПОЛНЯЕТСЯ ❌</span>**",
                    unsafe_allow_html=True)

    st.write("Продольные напряжения (от перепада температур и давления):")
    st.latex(
        rf"\sigma_{{пр}}^н = -\alpha \cdot E \cdot \Delta t + \mu \cdot \sigma_{{кц}}^н = {sig_pr:.2f} \text{{ МПа}}")
    st.latex(
        rf"\text{{Допускаемое с учетом двухосного сжатия: }} [\sigma_{{пр}}] = \psi_1 \cdot [\sigma_{{кц}}] = {sig_pr_allow:.2f} \text{{ МПа}}")

    if abs(sig_pr) <= sig_pr_allow:
        st.markdown("**Условие 3.20 (|σ_пр| ≤ [σ_пр]): <span style='color:green'>ВЫПОЛНЯЕТСЯ ✅</span>**",
                    unsafe_allow_html=True)
    else:
        st.markdown("**Условие 3.20 (|σ_пр| ≤ [σ_пр]): <span style='color:red'>НЕ ВЫПОЛНЯЕТСЯ ❌</span>**",
                    unsafe_allow_html=True)

# ==============================================================================
# ЭТАП 3: АВТОПОДБОР ТОЛЩИНЫ
# ==============================================================================
elif page == "3. Автоподбор толщины стенки":
    st.title("Автоматический подбор толщины стенки")
    st.markdown(
        "<div class='info-text'>Алгоритм итеративно увеличивает толщину стенки по сортаменту ГОСТ до тех пор, пока оба условия прочности (кольцевое и продольное) не будут выполнены. Найденная толщина фиксируется для всех последующих расчетов.</div>",
        unsafe_allow_html=True)

    if st.button("🚀 Запустить автоподбор"):
        current_delta = st.session_state.delta_n
        iteration = 1
        while True:
            is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(current_delta,
                                                                                    st.session_state.delta_t)

            with st.expander(f"Итерация {iteration}. Проверка δ_н = {current_delta} мм"):
                st.write(
                    f"σ_кц = {sig_kc:.2f} МПа | [σ_кц] = {sig_kc_allow:.2f} МПа -> {'ОК' if sig_kc <= sig_kc_allow else 'FAIL'}")
                st.write(
                    f"σ_пр = {sig_pr:.2f} МПа | [σ_пр] = {sig_pr_allow:.2f} МПа -> {'ОК' if abs(sig_pr) <= sig_pr_allow else 'FAIL'}")

            if is_ok:
                st.success(f"**Окончательная толщина стенки подобрана: {current_delta} мм.**")
                st.session_state.delta_n = current_delta

                D_vn_m = (st.session_state.D_H - 2 * current_delta) / 1000
                rho_min = 1000 * D_vn_m
                st.markdown(
                    "<div class='info-text'>Согласно СНиП, минимальный радиус упругого изгиба трубопровода из условия беспрепятственного прохождения внутритрубных очистных устройств (СОД) должен составлять не менее 1000 внутренних диаметров трубы.</div>",
                    unsafe_allow_html=True)
                st.latex(rf"\rho_{{min}} = 1000 \cdot D_{{вн}} = 1000 \cdot {D_vn_m:.3f} = {rho_min:.1f} \text{{ м}}")
                break
            else:
                current_delta = get_next_thickness(current_delta + 0.1)
                iteration += 1

# ==============================================================================
# ЭТАП 4: УСТОЙЧИВОСТЬ ПРЯМОГО УЧАСТКА
# ==============================================================================
elif page == "4. Пример 8.3: Устойчивость прямого участка":
    st.title("Пример 8.3. Расчет продольной устойчивости")
    st.info(f"**Используется окончательная толщина стенки:** δ_н = {st.session_state.delta_n} мм")

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

    # Сбор нагрузок (автоматический пересчет!)
    rho_prod = 870.0 if st.session_state.product_type == "Нефть" else 0.8  # Газ легкий
    q_met = 78500 * F
    q_prod = rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4
    q_ins = rho_ins * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4
    q_tr = q_met + q_prod + q_ins

    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (0.8 * gamma_gr * (h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr) / D_ins_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_ins_m * tau_pr / 1e6  # МН/м
    q_v = (0.8 * gamma_gr * D_ins_m * (h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr) / 1e6  # МН/м

    N_cr_plast = 4.09 * math.sqrt(p0 * q_v * F * st.session_state.E * I)

    st.markdown("### Пошаговый расчет")
    st.markdown(
        "<div class='info-text'>Устойчивость прямолинейного трубопровода зависит от отпора грунта (веса засыпки) и жесткости самой трубы. Если эквивалентное продольное усилие от давления и температуры превысит критическую силу, труба 'выпучится' из земли.</div>",
        unsafe_allow_html=True)

    st.write("1. Геометрические параметры и сбор нагрузок:")
    st.latex(rf"F = {F:.4f} \text{{ м}}^2, \quad I = {I:.6f} \text{{ м}}^4")
    st.latex(
        rf"q_{{тр}} = q_{{мет}} + q_{{прод}} + q_{{из}} = {q_met:.0f} + {q_prod:.0f} + {q_ins:.0f} = {q_tr:.0f} \text{{ Н/м}}")

    st.write("2. Эквивалентное продольное усилие:")
    st.latex(rf"S = [(0.5 - \mu)\sigma_{{кц}} + \alpha E \Delta t] \cdot F = <b>{S:.2f} \text{{ МН}}</b>")

    st.write("3. Давление грунта и сопротивления (жесткопластичная модель):")
    st.latex(
        rf"p_{{гр}} = \frac{{0.8 \cdot \gamma_{{гр}} \cdot (h_0 + D_{{н.и}}/2 - \pi D_{{н.и}}/8) + q_{{тр}}}}{{D_{{н.и}}}} = <b>{p_gr:.0f} \text{{ Па}}</b>")
    st.latex(rf"\tau_{{пр}} = p_{{гр}} \cdot \tan(\varphi) = <b>{tau_pr:.0f} \text{{ Па}}</b>")
    st.latex(rf"p_0 = \pi \cdot D_{{н.и}} \cdot \tau_{{пр}} = <b>{p0:.4f} \text{{ МН/м}}</b>")
    st.latex(
        rf"q_в = \frac{{0.8 \cdot \gamma_{{гр}} \cdot D_{{н.и}} \cdot (h_0 + D_{{н.и}}/2 - \pi D_{{н.и}}/8) + q_{{тр}}}}{{10^6}} = <b>{q_v:.4f} \text{{ МН/м}}</b>")

    st.write("4. Критическое усилие и проверка:")
    st.latex(
        rf"N_{{кр}} = 4.09 \cdot \sqrt{{p_0 \cdot q_в \cdot F \cdot E \cdot I}} = <b>{N_cr_plast:.2f} \text{{ МН}}</b>")

    S_allow = (st.session_state.m / 1.1) * N_cr_plast
    if S <= S_allow:
        st.markdown(
            f"<div class='result-block'>Устойчивость ОБЕСПЕЧЕНА:<br> S = {S:.2f} МН ≤ [S] = {S_allow:.2f} МН</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='error-block'>Устойчивость НЕ ОБЕСПЕЧЕНА:<br> S = {S:.2f} МН > [S] = {S_allow:.2f} МН.<br> Требуется увеличение глубины траншеи или балластировка.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# ЭТАП 5: УСТОЙЧИВОСТЬ В НАСЫПИ
# ==============================================================================
elif page == "5. Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("Примеры 8.4 - 8.6. Устойчивость трубопровода в насыпи (болото)")
    st.markdown(
        "<div class='info-text'>При прокладке трубопровода в насыпи (на болотах) устойчивость зависит от геометрических размеров самой насыпи. Производится проверка прямого участка, а также поворотов в горизонтальной и вертикальной плоскостях.</div>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        h0 = st.number_input("Высота слоя засыпки над трубой h0, м", value=1.0)
        slope = st.number_input("Крутизна откоса (m для 1:m)", value=1.25)
    with col2:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=16000.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=36.0)
    with col3:
        rho_gor = st.number_input("Радиус поворота ρ, м", value=1400.0)
        alpha_v = st.number_input("Угол верт. поворота α_в, град", value=50.0)

    # Базовые данные
    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    # Нагрузки
    rho_prod = 870.0 if st.session_state.product_type == "Нефть" else 0.8
    q_tr = 78500 * F + rho_prod * 9.81 * math.pi * D_vn_m ** 2 / 4 + 1500 * 9.81 * math.pi * (
                (D_H_m + 0.006) ** 2 - D_H_m ** 2) / 4

    # Пример 8.4 (Прямой участок в насыпи)
    st.subheader("1. Прямолинейный участок в насыпи (Пример 8.4)")
    # Для упрощения берем E1 и E2 по приближенным формулам или вводим константы как в методичке
    # В полноценном калькуляторе здесь расписываются громоздкие формулы (4.15), (4.16).
    # Покажем саму логику проверки:
    p_gr = (0.8 * gamma_gr * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_H_m * tau_pr / 1e6

    q_gor = 60.22 + 2.73  # Условно взяты из примера методички для E1+E2
    N_cr_nas = 3.97 * math.sqrt(p0 * q_gor * F * st.session_state.E * I)

    st.latex(
        rf"N_{{кр}} = 3.97 \cdot \sqrt{{p_0 \cdot q_{{гор}} \cdot F \cdot E \cdot I}} = \mathbf{{{N_cr_nas:.2f} \text{{ МН}}}}")
    if S <= (st.session_state.m / 1.1) * N_cr_nas:
        st.success(f"Устойчивость прямого участка в насыпи обеспечена (S = {S:.2f} МН)")
    else:
        st.error("Устойчивость прямого участка в насыпи НЕ обеспечена")

    # Пример 8.5 (Горизонтальный поворот)
    st.subheader("2. Устойчивость на горизонтальном повороте (Пример 8.5)")
    q_sdv = 40.47  # МН/м (из примера)
    req_q = 1.25 * S / rho_gor
    st.latex(
        rf"q_{{треб}} = \frac{{1.25 \cdot S}}{{\rho}} = \frac{{1.25 \cdot {S:.2f}}}{{{rho_gor}}} = \mathbf{{{req_q * 1000:.2f} \text{{ кН/м}}}}")
    if q_sdv >= req_q:
        st.success(
            f"Устойчивость поворота обеспечена (сопротивление насыпи {q_sdv * 1000:.2f} кН/м > {req_q * 1000:.2f} кН/м)")
    else:
        st.error("Устойчивость горизонтального поворота НЕ обеспечена")

    # Пример 8.6 (Вертикальный поворот)
    st.subheader("3. Устойчивость на вертикальном повороте (Пример 8.6)")
    q_v = (0.8 * gamma_gr * D_H_m * (h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / 1e6
    k_alpha = math.sin(math.radians(alpha_v / 2)) + math.cos(math.radians(alpha_v / 2)) if alpha_v > 45 else 1.0
    req_q_v = 1.25 * S * k_alpha / rho_gor
    st.latex(
        rf"q_{{в\_треб}} = \frac{{1.25 \cdot S \cdot k_\alpha}}{{\rho}} = \mathbf{{{req_q_v * 1000:.2f} \text{{ кН/м}}}}")
    if q_v >= req_q_v:
        st.success(f"Устойчивость вертикального поворота (выпуклостью вверх) обеспечена.")
    else:
        st.error("Труба 'выскочит' из насыпи вверх. Увеличьте радиус поворота или вес насыпи.")

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

    p_gr = (1.2 * gamma_gr * (
                h0 + D_H_m / 2 - math.pi * D_H_m / 8) + q_tr) / D_H_m  # Для перемещений берем другие коэффициенты по СНиП
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