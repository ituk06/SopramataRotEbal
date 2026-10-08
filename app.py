import streamlit as st
import math
import os

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Сопромат Трубопроводов", page_icon="🛢️", layout="wide")

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
    """Возвращает ближайшую большую толщину стенки из сортамента."""
    target = max(calc_thickness, min_thickness)
    for t in SORTAMENT:
        if t >= target:
            return t
    return math.ceil(target)


# --- ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ (SESSION STATE) ---
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

# --- МЕНЮ НАВИГАЦИИ ---
st.sidebar.title("🛢️ Учебный комплекс")
page = st.sidebar.radio("Выберите раздел:", [
    "0. Климатология и Нагрузки",
    "1. Пример 8.1: Толщина стенки",
    "2. Пример 8.2: Проверка прочности",
    "3. Пример 8.3: Устойчивость прямого участка",
    "4. Примеры 8.4-8.6: Устойчивость в насыпи",
    "5. Пример 8.7: Продольные перемещения"
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
        psi_1 = math.sqrt(under_sqrt) - 0.5 * (sigma_kc_n / sigma_kc_allow) if under_sqrt >= 0 else 0
    else:
        psi_1 = 1.0

    sigma_pr_allow = psi_1 * sigma_kc_allow
    is_ok = (sigma_kc_n <= sigma_kc_allow) and (abs(sigma_pr_n) <= sigma_pr_allow)
    return is_ok, sigma_kc_n, sigma_kc_allow, sigma_pr_n, psi_1, sigma_pr_allow


def find_image(base_name):
    """Ищет файл картинки с расширением .png, .jpg или .jpeg"""
    for ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']:
        filename = base_name + ext
        if os.path.exists(filename):
            return filename
    return None


# ==============================================================================
# ЭТАП 0: КЛИМАТОЛОГИЯ И НАГРУЗКИ
# ==============================================================================
if page == "0. Климатология и Нагрузки":
    st.title("Определение расчетного температурного перепада (Δt)")
    st.markdown(
        "<div class='info-text'>Согласно СП 36.13330.2012, температурный перепад в металле стенок труб принимается как разница между максимально (или минимально) возможной температурой эксплуатации и температурой, при которой фиксируется расчетная схема (замыкание трубопровода).</div>",
        unsafe_allow_html=True)

    st.markdown("### 🗺️ Климатические карты (СП 131.13330)")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Макс. Температура", "Мин. Температура", "Снег", "Ветер", "Гололед"])

    with tab1:
        img = find_image("Снимок экрана 2026-10-09 в 00.49.04") or find_image("map_max")
        if img:
            st.image(img, use_container_width=True)
        else:
            st.warning("Карта максимальных температур не найдена в папке проекта.")
    with tab2:
        img = find_image("Снимок экрана 2026-10-09 в 00.49.13") or find_image("map_min")
        if img:
            st.image(img, use_container_width=True)
        else:
            st.warning("Карта минимальных температур не найдена в папке проекта.")
    with tab3:
        img = find_image("Снимок экрана 2026-10-09 в 00.49.19") or find_image("map_snow")
        if img:
            st.image(img, use_container_width=True)
        else:
            st.warning("Карта снеговых нагрузок не найдена в папке проекта.")
    with tab4:
        img = find_image("Снимок экрана 2026-10-09 в 00.49.27") or find_image("map_wind")
        if img:
            st.image(img, use_container_width=True)
        else:
            st.warning("Карта ветровых нагрузок не найдена в папке проекта.")
    with tab5:
        img = find_image("Снимок экрана 2026-10-09 в 00.49.35") or find_image("map_ice")
        if img:
            st.image(img, use_container_width=True)
        else:
            st.warning("Карта гололедных нагрузок не найдена в папке проекта.")

    st.markdown("### Ввод данных для расчета температур")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.product_type = st.radio("Тип транспортируемого продукта:", ["Нефть", "Газ"],
                                                 index=0 if st.session_state.product_type == "Нефть" else 1)
        t_product_default = 5.0 if st.session_state.product_type == "Нефть" else 6.0
        t_product = st.number_input("Температура эксплуатации продукта (t_э), °C", value=t_product_default)
        t_max_map = st.number_input("Максимальная температура по карте (t_max), °C", value=30.0)
        t_min_map = st.number_input("Минимальная температура по карте (t_min), °C", value=-50.0)

    with col2:
        t_x = t_min_map - 6.0
        t_m = t_max_map + 3.0
        dt_x = t_product - t_x
        dt_m = t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.latex(rf"t_x = t_{{min}} - 6^\circ C = {t_min_map} - 6 = {t_x}^\circ C")
        st.latex(rf"t_m = t_{{max}} + 3^\circ C = {t_max_map} + 3 = {t_m}^\circ C")
        st.latex(rf"\Delta t_x = t_{{э}} - t_x = {t_product} - ({t_x}) = {dt_x}^\circ C")
        st.latex(rf"\Delta t_m = t_{{э}} - t_m = {t_product} - ({t_m}) = {dt_m}^\circ C")

        st.success(f"**Расчетный (наихудший) температурный перепад:** Δt = **{calc_dt} °C**")
        if st.button("Сохранить Δt"):
            st.session_state.delta_t = calc_dt

# ==============================================================================
# ЭТАП 1: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "1. Пример 8.1: Толщина стенки":
    st.title("Пример 8.1. Определение расчетной толщины стенки")

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
    delta_nom = math.ceil(delta_calc)

    st.markdown("### Пошаговый расчет")
    st.write("1. Расчетные сопротивления металла труб на разрыв и по пределу текучести:")
    st.latex(
        rf"R_1 = \frac{{R_1^н \cdot m}}{{k_1 \cdot k_н}} = \frac{{{st.session_state.R1_n} \cdot {st.session_state.m}}}{{{st.session_state.k1} \cdot {st.session_state.k_H}}} = \mathbf{{{R1:.2f} \text{{ МПа}}}}")
    st.latex(
        rf"R_2 = \frac{{R_2^н \cdot m}}{{k_2 \cdot k_н}} = \frac{{{st.session_state.R2_n} \cdot {st.session_state.m}}}{{{st.session_state.k2} \cdot {st.session_state.k_H}}} = \mathbf{{{R2:.2f} \text{{ МПа}}}}")

    st.write("2. Расчетная толщина стенки трубы:")
    st.latex(
        rf"\delta = \frac{{n_p \cdot p \cdot D_н}}{{2(R_1 + n_p \cdot p)}} = \frac{{{n_p} \cdot {st.session_state.P} \cdot {st.session_state.D_H}}}{{2({R1:.2f} + {n_p} \cdot {st.session_state.P})}} = \mathbf{{{delta_calc:.2f} \text{{ мм}}}}")

    st.markdown(
        f"<div class='result-block'>Принятая по ГОСТ предварительная толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
        unsafe_allow_html=True)

    if st.button("Сохранить и перейти к проверке прочности"):
        st.session_state.delta_n = delta_nom
        st.rerun()

# ==============================================================================
# ЭТАП 2: ПРОВЕРКА ПРОЧНОСТИ (ОБЪЕДИНЕННАЯ)
# ==============================================================================
elif page == "2. Пример 8.2: Проверка прочности":
    st.title("Пример 8.2. Проверка прочности трубопровода")

    col1, col2 = st.columns(2)
    with col1:
        check_delta = st.number_input("Проверяемая толщина стенки δ_н, мм", value=float(st.session_state.delta_n),
                                      step=1.0)
    with col2:
        check_dt = st.number_input("Расчетный темп. перепад Δt, °C", value=st.session_state.delta_t)

    D_vn = st.session_state.D_H - 2 * check_delta
    sigma_kc_n = st.session_state.P * D_vn / (2 * check_delta)
    sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n

    sigma_pr_n = -st.session_state.alpha * st.session_state.E * check_dt + st.session_state.mu * sigma_kc_n

    if sigma_pr_n < 0:
        under_sqrt = 1 - 0.75 * (sigma_kc_n / sigma_kc_allow) ** 2
        psi_1 = math.sqrt(under_sqrt) - 0.5 * (sigma_kc_n / sigma_kc_allow) if under_sqrt >= 0 else 0
    else:
        psi_1 = 1.0

    sigma_pr_allow = psi_1 * sigma_kc_allow
    is_ok = (sigma_kc_n <= sigma_kc_allow) and (abs(sigma_pr_n) <= sigma_pr_allow)

    st.markdown(f"### Подробный расчет для толщины стенки $\delta_н = {check_delta}$ мм")

    st.write("1. Кольцевые напряжения от нормативного давления:")
    st.latex(
        rf"\sigma_{{кц}}^н = \frac{{p \cdot D_{{вн}}}}{{2\delta_н}} = \frac{{{st.session_state.P} \cdot {D_vn}}}{{2 \cdot {check_delta}}} = \mathbf{{{sigma_kc_n:.2f} \text{{ МПа}}}}")
    st.latex(
        rf"[\sigma_{{кц}}] = \frac{{m}}{{0.9 \cdot k_н}} \cdot R_2^н = \frac{{{st.session_state.m}}}{{0.9 \cdot {st.session_state.k_H}}} \cdot {st.session_state.R2_n} = \mathbf{{{sigma_kc_allow:.2f} \text{{ МПа}}}}")

    if sigma_kc_n <= sigma_kc_allow:
        st.markdown(
            f"**Условие 3.21 ($\sigma_{{кц}}^н \le [\sigma_{{кц}}]$):** <span style='color:green'>TRUE ✅</span> ({sigma_kc_n:.2f} ≤ {sigma_kc_allow:.2f})",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"**Условие 3.21 ($\sigma_{{кц}}^н \le [\sigma_{{кц}}]$):** <span style='color:red'>FALSE ❌</span> ({sigma_kc_n:.2f} > {sigma_kc_allow:.2f})",
            unsafe_allow_html=True)

    st.write("2. Продольные напряжения от нормативных нагрузок:")
    st.latex(
        rf"\sigma_{{пр}}^н = -\alpha \cdot E \cdot \Delta t + \mu \cdot \sigma_{{кц}}^н = -{st.session_state.alpha} \cdot {st.session_state.E} \cdot {check_dt} + {st.session_state.mu} \cdot {sigma_kc_n:.2f} = \mathbf{{{sigma_pr_n:.2f} \text{{ МПа}}}}")

    st.write("3. Учет двухосного напряженного состояния (коэффициент $\psi_1$):")
    st.latex(
        rf"\psi_1 = \sqrt{{1 - 0.75 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right)^2}} - 0.5 \left(\frac{{\sigma_{{кц}}^н}}{{[\sigma_{{кц}}]}}\right) = \sqrt{{1 - 0.75 \left(\frac{{{sigma_kc_n:.2f}}}{{{sigma_kc_allow:.2f}}}\right)^2}} - 0.5 \left(\frac{{{sigma_kc_n:.2f}}}{{{sigma_kc_allow:.2f}}}\right) = \mathbf{{{psi_1:.4f}}}")
    st.latex(
        rf"[\sigma_{{пр}}] = \psi_1 \cdot [\sigma_{{кц}}] = {psi_1:.4f} \cdot {sigma_kc_allow:.2f} = \mathbf{{{sigma_pr_allow:.2f} \text{{ МПа}}}}")

    if abs(sigma_pr_n) <= sigma_pr_allow:
        st.markdown(
            f"**Условие 3.20 ($|\sigma_{{пр}}^н| \le [\sigma_{{пр}}]$):** <span style='color:green'>TRUE ✅</span> ({abs(sigma_pr_n):.2f} ≤ {sigma_pr_allow:.2f})",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"**Условие 3.20 ($|\sigma_{{пр}}^н| \le [\sigma_{{пр}}]$):** <span style='color:red'>FALSE ❌</span> ({abs(sigma_pr_n):.2f} > {sigma_pr_allow:.2f})",
            unsafe_allow_html=True)

    st.markdown("---")

    if is_ok:
        st.success(f"Прочность обеспечена! Рекомендуемая толщина стенки: {check_delta} мм.")

        rho_min = 1000 * (D_vn / 1000)
        st.write("4. Минимальный радиус упругого изгиба для прохода СОД:")
        st.latex(
            rf"\rho_{{min}} = 1000 \cdot D_{{вн}} = 1000 \cdot {D_vn / 1000:.3f} = \mathbf{{{rho_min:.1f} \text{{ м}}}}")

        if st.button("Зафиксировать эту толщину для следующих расчетов"):
            st.session_state.delta_n = check_delta
            st.rerun()
    else:
        st.error(f"При толщине {check_delta} мм условия прочности не выполняются. Требуется увеличить толщину.")

        if st.button("🚀 Запустить автоподбор"):
            iter_delta = check_delta
            for _ in range(15):
                iter_delta = get_next_thickness(iter_delta + 0.1)
                D_v_tmp = st.session_state.D_H - 2 * iter_delta
                sk_n = st.session_state.P * D_v_tmp / (2 * iter_delta)
                sk_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n
                sp_n = -st.session_state.alpha * st.session_state.E * check_dt + st.session_state.mu * sk_n

                if sp_n < 0:
                    u_sq = 1 - 0.75 * (sk_n / sk_allow) ** 2
                    p_1 = math.sqrt(u_sq) - 0.5 * (sk_n / sk_allow) if u_sq >= 0 else 0
                else:
                    p_1 = 1.0

                sp_allow = p_1 * sk_allow
                if (sk_n <= sk_allow) and (abs(sp_n) <= sp_allow):
                    st.session_state.delta_n = iter_delta
                    st.success(
                        f"**Окончательная толщина стенки подобрана: {iter_delta} мм.** Нажмите кнопку еще раз, чтобы обновить расчет.")
                    break

# ==============================================================================
# ЭТАП 3: УСТОЙЧИВОСТЬ
# ==============================================================================
elif page == "3. Пример 8.3: Устойчивость прямого участка":
    st.title("Пример 8.3. Расчет продольной устойчивости")
    st.info(
        f"**Важно:** В расчетах используется итоговая толщина стенки $\delta_н = {st.session_state.delta_n}$ мм, подобранная на предыдущем шаге.")

    col1, col2 = st.columns(2)
    with col1:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=18000.0)
        h0 = st.number_input("Глубина заложения h0, м", value=1.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=38.0)
    with col2:
        k_0 = st.number_input("Коэфф. постели грунта k0, МН/м³", value=2.0)
        q_tr = st.number_input("Вес трубы с продуктом и изоляцией q_тр, Н/м", value=3762.1)

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins_m = D_H_m + 0.006

    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (0.8 * gamma_gr * (h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr) / D_ins_m
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_ins_m * tau_pr / 1e6
    q_v = (0.8 * gamma_gr * D_ins_m * (h0 + D_ins_m / 2 - math.pi * D_ins_m / 8) + q_tr) / 1e6

    N_cr_plast = 4.09 * math.sqrt(p0 * q_v * F * st.session_state.E * I)

    st.markdown("### Подробный расчет с подстановкой значений")

    st.write("1. Геометрические параметры:")
    st.latex(rf"F = \frac{{\pi \cdot ({D_H_m}^2 - {D_vn_m:.3f}^2)}}{{4}} = \mathbf{{{F:.4f} \text{{ м}}^2}}")
    st.latex(rf"I = \frac{{\pi \cdot ({D_H_m}^4 - {D_vn_m:.3f}^4)}}{{64}} = \mathbf{{{I:.6f} \text{{ м}}^4}}")

    st.write("2. Эквивалентное продольное усилие:")
    st.latex(
        rf"S = [(0.5 - {st.session_state.mu})\cdot{sigma_kc:.2f} + {st.session_state.alpha} \cdot {st.session_state.E} \cdot {st.session_state.delta_t}] \cdot {F:.4f} = \mathbf{{{S:.2f} \text{{ МН}}}}")

    st.write("3. Давление грунта и сопротивления:")
    st.latex(
        rf"p_{{гр}} = \frac{{0.8 \cdot {gamma_gr} \cdot ({h0} + {D_ins_m / 2:.3f} - \pi \cdot {D_ins_m}/8) + {q_tr:.0f}}}{{{D_ins_m}}} = \mathbf{{{p_gr:.0f} \text{{ Па}}}}")
    st.latex(
        rf"\tau_{{пр}} = p_{{гр}} \cdot \tan(\varphi) = {p_gr:.0f} \cdot \tan({phi_deg}^\circ) = \mathbf{{{tau_pr:.0f} \text{{ Па}}}}")
    st.latex(
        rf"p_0 = \pi \cdot D_{{н.и}} \cdot \tau_{{пр}} = 3.1416 \cdot {D_ins_m} \cdot {tau_pr:.0f} \cdot 10^{{-6}} = \mathbf{{{p0:.4f} \text{{ МН/м}}}}")
    st.latex(rf"q_в = \mathbf{{{q_v:.4f} \text{{ МН/м}}}}")

    st.write("4. Критическое усилие и проверка:")
    st.latex(
        rf"N_{{кр}} = 4.09 \cdot \sqrt{{{p0:.4f} \cdot {q_v:.4f} \cdot {F:.4f} \cdot {st.session_state.E} \cdot {I:.6f}}} = \mathbf{{{N_cr_plast:.2f} \text{{ МН}}}}")

    S_allow = (st.session_state.m / 1.1) * N_cr_plast
    st.latex(
        rf"S \le \frac{{m}}{{1.1}} \cdot N_{{кр}} \rightarrow {S:.2f} \le \frac{{{st.session_state.m}}}{{1.1}} \cdot {N_cr_plast:.2f} = {S_allow:.2f} \text{{ МН}}")

    if S <= S_allow:
        st.markdown(f"<div class='result-block'>Устойчивость ОБЕСПЕЧЕНА: {S:.2f} МН ≤ {S_allow:.2f} МН</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='error-block'>Устойчивость НЕ ОБЕСПЕЧЕНА: {S:.2f} МН > {S_allow:.2f} МН</div>",
                    unsafe_allow_html=True)

# Заглушки для 4 и 5
elif page == "4. Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("Примеры 8.4 - 8.6. Устойчивость трубопровода в насыпи")
    st.info("Раздел в разработке, аналогичен расчету 8.3.")
elif page == "5. Пример 8.7: Продольные перемещения":
    st.title("Пример 8.7. Продольные перемещения")
    st.info("Раздел в разработке.")