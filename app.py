import streamlit as st
import math
import os

st.set_page_config(page_title="Сопромат Трубопроводов", page_icon="🛢️", layout="wide")

st.markdown("""
    <style>
    .math-block { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; font-family: 'Courier New', monospace; font-size: 1.1em; margin-bottom: 10px; overflow-x: auto;}
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .error-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; margin-bottom: 20px;}
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
if 'R1_n' not in st.session_state: st.session_state.R1_n = 490.0
if 'R2_n' not in st.session_state: st.session_state.R2_n = 345.0
if 'm' not in st.session_state: st.session_state.m = 0.990
if 'k1' not in st.session_state: st.session_state.k1 = 1.34
if 'k2' not in st.session_state: st.session_state.k2 = 1.15
if 'k_H' not in st.session_state: st.session_state.k_H = 1.100
if 'delta_n' not in st.session_state: st.session_state.delta_n = 11.0
if 'delta_t' not in st.session_state: st.session_state.delta_t = 75.0
if 'E' not in st.session_state: st.session_state.E = 206000.0
if 'alpha' not in st.session_state: st.session_state.alpha = 0.000012
if 'mu' not in st.session_state: st.session_state.mu = 0.3

st.sidebar.title("🛢️ Меню расчетов")
page = st.sidebar.radio("Выберите этап:", [
    "0. Расчет температур (По картам)",
    "1. Пример 8.1: Толщина стенки",
    "2. Пример 8.2: Проверка прочности (Ручная/Excel)",
    "3. Автоподбор толщины стенки",
    "4. Пример 8.3: Расчет общей устойчивости"
])

st.sidebar.markdown("---")
st.sidebar.info(f"**Текущая толщина стенки в памяти:** {st.session_state.delta_n} мм")


# Функция проверки прочности (используется в нескольких местах)
def check_strength(delta, dt):
    D_vn = st.session_state.D_H - 2 * delta
    sigma_kc_n = st.session_state.P * D_vn / (2 * delta)
    sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n

    # Худший случай - сжатие (отрицательный перепад)
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
# ЭТАП 0: КЛИМАТОЛОГИЯ
# ==============================================================================
if page == "0. Расчет температур (По картам)":
    st.title("Определение расчетного температурного перепада (Δt)")

    st.markdown("### 🗺️ Карты СП 131.13330 (СНиП 23-01-99)")
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        if os.path.exists("map_max.png"):
            st.image("map_max.png", caption="Карта максимальных температур", use_container_width=True)
        elif os.path.exists("map_max.jpg"):
            st.image("map_max.jpg", caption="Карта максимальных температур", use_container_width=True)

    with col_img2:
        if os.path.exists("map_min.png"):
            st.image("map_min.png", caption="Карта минимальных температур", use_container_width=True)
        elif os.path.exists("map_min.jpg"):
            st.image("map_min.jpg", caption="Карта минимальных температур", use_container_width=True)

    st.markdown("### Ввод данных")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.product_type = st.radio("Тип транспортируемого продукта:", ["Нефть", "Газ"],
                                                 index=0 if st.session_state.product_type == "Нефть" else 1)
        # Автоматическая установка температуры
        t_product_default = 5.0 if st.session_state.product_type == "Нефть" else 6.0
        st.session_state.t_product = st.number_input("Температура эксплуатации продукта (t_э), °C",
                                                     value=t_product_default)

        t_max_map = st.number_input("Максимальная температура по карте (t_max), °C", value=30.0)
        t_min_map = st.number_input("Минимальная температура по карте (t_min), °C", value=-50.0)

    with col2:
        st.markdown("#### Расчет температур замыкания")
        t_x = t_min_map - 6.0
        t_m = t_max_map + 3.0
        dt_x = st.session_state.t_product - t_x
        dt_m = st.session_state.t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.latex(rf"t_x = t_{{min}} - 6^\circ C = {t_min_map} - 6 = {t_x}^\circ C")
        st.latex(rf"t_m = t_{{max}} + 3^\circ C = {t_max_map} + 3 = {t_m}^\circ C")
        st.latex(rf"\Delta t_x = t_{{э}} - t_x = {st.session_state.t_product} - ({t_x}) = {dt_x}^\circ C")
        st.latex(rf"\Delta t_m = t_{{э}} - t_m = {st.session_state.t_product} - ({t_m}) = {dt_m}^\circ C")

        st.success(f"**Расчетный (максимальный) перепад:** Δt = **{calc_dt} °C**")

        if st.button("Сохранить Δt"):
            st.session_state.delta_t = calc_dt
            st.success("Перепад сохранен!")

# ==============================================================================
# ЭТАП 1: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "1. Пример 8.1: Толщина стенки":
    st.title("Пример 8.1. Определение расчетной толщины стенки")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.D_H = st.number_input("Наружный диаметр D_н, мм", value=st.session_state.D_H)
        st.session_state.P = st.number_input("Рабочее давление p, МПа", value=st.session_state.P)
        n_p = st.number_input("Коэфф. надежности нагрузки n", value=1.1)
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

    # Округление "как в Excel" (вверх до ближайшего целого)
    delta_nom = math.ceil(delta_calc)

    st.markdown("### Вычисления")
    st.write("1. Расчетные сопротивления:")
    st.markdown(
        f"<div class='math-block'>R₁ = R₁_н · m / (k₁ · k_н) = {st.session_state.R1_n} · {st.session_state.m} / ({st.session_state.k1} · {st.session_state.k_H}) = <b>{R1:.2f} МПа</b><br>"
        f"R₂ = R₂_н · m / (k₂ · k_н) = {st.session_state.R2_n} · {st.session_state.m} / ({st.session_state.k2} · {st.session_state.k_H}) = <b>{R2:.2f} МПа</b></div>",
        unsafe_allow_html=True)

    st.write("2. Расчетная толщина стенки:")
    st.markdown(
        f"<div class='math-block'>δ = n · p · D_н / 2·(R₁ + n · p) = {n_p} · {st.session_state.P} · {st.session_state.D_H} / 2·({R1:.2f} + {n_p} · {st.session_state.P}) = <b>{delta_calc:.2f} мм</b></div>",
        unsafe_allow_html=True)

    st.markdown(f"<div class='result-block'>Принятая номинальная толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
                unsafe_allow_html=True)

    if st.button("Сохранить толщину в память"):
        st.session_state.delta_n = delta_nom
        st.success(f"Толщина {delta_nom} мм сохранена!")

# ==============================================================================
# ЭТАП 2: РУЧНАЯ ПРОВЕРКА ПРОЧНОСТИ (КАК В EXCEL)
# ==============================================================================
elif page == "2. Пример 8.2: Проверка прочности (Ручная/Excel)":
    st.title("Пример 8.2. Проверка прочности (как в таблице)")
    st.markdown("Здесь выполняется разовая проверка условий прочности для заданной толщины стенки (без автоподбора).")

    col1, col2 = st.columns(2)
    with col1:
        check_delta = st.number_input("Проверяемая толщина стенки δ_н, мм", value=float(st.session_state.delta_n),
                                      step=1.0)
    with col2:
        st.session_state.delta_t = st.number_input("Расчетный темп. перепад Δt, °C", value=st.session_state.delta_t)

    is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(check_delta, st.session_state.delta_t)

    st.markdown("### Результаты проверки:")
    st.markdown(f"<div class='math-block'>"
                f"<b>Кольцевые напряжения:</b><br>"
                f"σ_кц = {sig_kc:.2f} МПа<br>"
                f"Допускаемое [σ_кц] = {sig_kc_allow:.2f} МПа<br>"
                f"<b>Условие 3.21 (σ_кц ≤ [σ_кц]): {'TRUE ✅' if sig_kc <= sig_kc_allow else 'FALSE ❌'}</b><br><br>"
                f"<b>Продольные напряжения:</b><br>"
                f"σ_пр = {sig_pr:.2f} МПа<br>"
                f"ψ₁ = {psi:.4f}<br>"
                f"Допускаемое [σ_пр] = {sig_pr_allow:.2f} МПа<br>"
                f"<b>Условие 3.20 (|σ_пр| ≤ [σ_пр]): {'TRUE ✅' if abs(sig_pr) <= sig_pr_allow else 'FALSE ❌'}</b>"
                f"</div>", unsafe_allow_html=True)

    if is_ok:
        st.success("Условия выполняются! Можно переходить к устойчивости.")
    else:
        st.error("Условия НЕ выполняются! Перейдите в раздел «Автоподбор толщины стенки».")

    if st.button("Сделать эту толщину основной"):
        st.session_state.delta_n = check_delta
        st.success("Толщина сохранена в память!")

# ==============================================================================
# ЭТАП 3: АВТОПОДБОР ТОЛЩИНЫ
# ==============================================================================
elif page == "3. Автоподбор толщины стенки":
    st.title("Автоматический подбор толщины по сортаменту")
    st.markdown(
        "Алгоритм автоматически увеличивает толщину стенки до тех пор, пока оба условия прочности не станут `TRUE`.")

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

                # Радиус очистных устройств
                D_vn_m = (st.session_state.D_H - 2 * current_delta) / 1000
                rho_min = 1000 * D_vn_m
                st.info(
                    f"Минимальный радиус изгиба для СОД: ρ_min = 1000 · D_вн = 1000 · {D_vn_m:.3f} = **{rho_min:.1f} м**")
                break
            else:
                current_delta = get_next_thickness(current_delta + 0.1)
                iteration += 1
                if iteration > 15:
                    st.error("Ошибка! Превышен лимит итераций.")
                    break

# ==============================================================================
# ЭТАП 4: УСТОЙЧИВОСТЬ
# ==============================================================================
elif page == "4. Пример 8.3: Расчет общей устойчивости":
    st.title("Пример 8.3. Расчет продольной устойчивости")
    st.info(
        f"**Важно:** В расчетах используется толщина стенки $\delta_н = {st.session_state.delta_n}$ мм, подобранная на предыдущих шагах.")

    col1, col2 = st.columns(2)
    with col1:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, Н/м³", value=18000.0)
        h0 = st.number_input("Глубина заложения h0, м", value=1.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=38.0)
    with col2:
        q_tr = st.number_input("Вес трубы с продуктом и изоляцией q_тр, Н/м", value=6070.0)

    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins = D_H_m + 0.006  # с изоляцией

    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64
    sigma_kc = st.session_state.P * D_vn_m / (2 * delta_m)
    S = ((
                     0.5 - st.session_state.mu) * sigma_kc + st.session_state.alpha * st.session_state.E * st.session_state.delta_t) * F

    p_gr = (0.8 * gamma_gr * (h0 + D_ins / 2 - math.pi * D_ins / 8) + q_tr) / D_ins
    tau_pr = p_gr * math.tan(math.radians(phi_deg))
    p0 = math.pi * D_ins * tau_pr / 1e6  # в МН/м
    q_v = (0.8 * gamma_gr * D_ins * (h0 + D_ins / 2 - math.pi * D_ins / 8) + q_tr) / 1e6  # в МН/м

    N_cr_plast = 4.09 * math.sqrt(p0 * q_v * F * st.session_state.E * I)

    st.markdown("### Вычисления")
    st.markdown(f"<div class='math-block'>"
                f"<b>1. Геометрические параметры:</b><br>"
                f"F = {F:.4f} м², I = {I:.6f} м⁴<br><br>"
                f"<b>2. Эквивалентное продольное усилие:</b><br>"
                f"S = [(0.5 - \mu)\sigma_{{кц}} + \\alpha E \Delta t] \cdot F = <b>{S:.2f} МН</b><br><br>"
                f"<b>3. Давление грунта и сопротивления:</b><br>"
                f"p_{{гр}} = <b>{p_gr:.0f} Па</b><br>"
                f"\\tau_{{пр}} = p_{{гр}} \cdot tg(\\varphi) = <b>{tau_pr:.0f} Па</b><br>"
                f"p_0 = \pi \cdot D_н \cdot \\tau_{{пр}} = <b>{p0:.4f} МН/м</b><br>"
                f"q_в = <b>{q_v:.4f} МН/м</b><br><br>"
                f"<b>4. Критическое усилие:</b><br>"
                f"N_{{кр}} = 4.09 \cdot \sqrt{{p_0 \cdot q_в \cdot F \cdot E \cdot I}} = <b>{N_cr_plast:.2f} МН</b>"
                f"</div>", unsafe_allow_html=True)

    S_allow = (st.session_state.m / 1.1) * N_cr_plast
    if S <= S_allow:
        st.success(f"**Устойчивость обеспечена:** S ({S:.2f} МН) ≤ [S] ({S_allow:.2f} МН)")
    else:
        st.error(f"**Устойчивость НЕ обеспечена:** S ({S:.2f} МН) > [S] ({S_allow:.2f} МН). Требуется балластировка.")