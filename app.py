import streamlit as st
import math

st.set_page_config(page_title="Сопромат Трубопроводов", page_icon="🛢️", layout="wide")

st.markdown("""
    <style>
    .math-block { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; font-family: 'Courier New', monospace; font-size: 1.1em; margin-bottom: 10px;}
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .alert-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; margin-bottom: 20px;}
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
if 'D_H' not in st.session_state: st.session_state.D_H = 1020.0
if 'P' not in st.session_state: st.session_state.P = 6.0
if 'R1_n' not in st.session_state: st.session_state.R1_n = 490.0
if 'R2_n' not in st.session_state: st.session_state.R2_n = 345.0
if 'm' not in st.session_state: st.session_state.m = 0.990
if 'k1' not in st.session_state: st.session_state.k1 = 1.34  # Пример
if 'k2' not in st.session_state: st.session_state.k2 = 1.15  # Пример
if 'k_H' not in st.session_state: st.session_state.k_H = 1.100
if 'delta_n' not in st.session_state: st.session_state.delta_n = 11.0
if 'delta_t' not in st.session_state: st.session_state.delta_t = 75.0
if 'E' not in st.session_state: st.session_state.E = 206000.0
if 'alpha' not in st.session_state: st.session_state.alpha = 0.000012
if 'mu' not in st.session_state: st.session_state.mu = 0.3

st.sidebar.title("🛢️ Меню расчетов")
page = st.sidebar.radio("Выберите этап:", [
    "0. Расчет температур (По картам)",
    "1. Определение толщины стенки",
    "2. Проверка прочности (Автоподбор)",
    "3. Расчет общей устойчивости"
])

st.sidebar.markdown("---")
st.sidebar.info(f"**Текущая толщина стенки:** {st.session_state.delta_n} мм")

# ==============================================================================
# ЭТАП 0: КЛИМАТОЛОГИЯ
# ==============================================================================
if page == "0. Расчет температур (По картам)":
    st.title("Определение расчетного температурного перепада (Δt)")
    st.markdown("Здесь вычисляются температуры замыкания по картам СНиП 23-01-99 (СП 131.13330).")

    col1, col2 = st.columns(2)
    with col1:
        t_max_map = st.number_input("Максимальная температура по карте (t_max), °C", value=30.0)
        t_min_map = st.number_input("Минимальная температура по карте (t_min), °C", value=-50.0)
        t_product = st.number_input("Температура эксплуатации продукта (t_э), °C", value=5.0)

    with col2:
        t_x = t_min_map - 6.0
        t_m = t_max_map + 3.0
        dt_x = t_product - t_x
        dt_m = t_product - t_m
        calc_dt = max(abs(dt_x), abs(dt_m))

        st.write("**Температуры замыкания:**")
        st.markdown(f"t_x = t_min - 6 = {t_min_map} - 6 = **{t_x} °C**")
        st.markdown(f"t_m = t_max + 3 = {t_max_map} + 3 = **{t_m} °C**")

        st.write("**Температурные перепады:**")
        st.markdown(f"Δt_x = t_э - t_x = {t_product} - ({t_x}) = **{dt_x} °C**")
        st.markdown(f"Δt_m = t_э - t_m = {t_product} - ({t_m}) = **{dt_m} °C**")

        st.success(f"**Расчетный (максимальный) перепад:** Δt = **{calc_dt} °C**")

        if st.button("Сохранить Δt"):
            st.session_state.delta_t = calc_dt
            st.success("Перепад сохранен! Переходите к следующему шагу.")

# ==============================================================================
# ЭТАП 1: ТОЛЩИНА СТЕНКИ
# ==============================================================================
elif page == "1. Определение толщины стенки":
    st.title("Пример 8.1. Определение толщины стенки трубы")

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

    # Стартовая толщина (без ограничения в 12 мм, чтобы показать логику проверки)
    delta_nom = get_next_thickness(delta_calc, min_thickness=4.0)

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

    st.markdown(f"<div class='result-block'>Принятая по сортаменту толщина стенки: δ_н = {delta_nom:.1f} мм</div>",
                unsafe_allow_html=True)

    if st.button("Сохранить и проверить прочность"):
        st.session_state.delta_n = delta_nom
        st.success(f"Толщина {delta_nom} мм сохранена. Переходите к Этапу 2.")

# ==============================================================================
# ЭТАП 2: ПРОВЕРКА ПРОЧНОСТИ (С АВТОПОДБОРОМ)
# ==============================================================================
elif page == "2. Проверка прочности (Автоподбор)":
    st.title("Пример 8.2. Проверка прочности и автоподбор толщины")
    st.markdown(
        "Если условие не выполняется, толщина будет увеличиваться по сортаменту, пока расчет не сойдется (например, до 23 мм).")


    def check_strength(delta):
        D_vn = st.session_state.D_H - 2 * delta
        sigma_kc_n = st.session_state.P * D_vn / (2 * delta)
        sigma_kc_allow = (st.session_state.m / (0.9 * st.session_state.k_H)) * st.session_state.R2_n

        # Продольные напряжения
        sigma_pr_n_pos = -st.session_state.alpha * st.session_state.E * st.session_state.delta_t + st.session_state.mu * sigma_kc_n
        sigma_pr_n_neg = -st.session_state.alpha * st.session_state.E * (
            -25.0) + st.session_state.mu * sigma_kc_n  # для примера (летнее замыкание)

        # Проверяем худший случай (сжатие)
        sigma_pr_n = min(sigma_pr_n_pos, sigma_pr_n_neg)

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


    current_delta = st.session_state.delta_n
    iteration = 1

    while True:
        st.markdown(f"#### Итерация {iteration}. Проверяем толщину стенки δ_н = {current_delta} мм")
        D_vn = st.session_state.D_H - 2 * current_delta
        is_ok, sig_kc, sig_kc_allow, sig_pr, psi, sig_pr_allow = check_strength(current_delta)

        st.markdown(f"<div class='math-block'>"
                    f"<b>1. Кольцевые напряжения от нормативного давления:</b><br>"
                    f"σ_кц = p · D_вн / (2 · δ_н) = {st.session_state.P} · {D_vn} / (2 · {current_delta}) = <b>{sig_kc:.2f} МПа</b><br><br>"
                    f"<b>2. Допускаемое кольцевое напряжение:</b><br>"
                    f"[σ_кц] = m / (0.9 · k_н) · R2_н = {st.session_state.m} / (0.9 · {st.session_state.k_H}) · {st.session_state.R2_n} = <b>{sig_kc_allow:.2f} МПа</b><br><br>"
                    f"<b>3. Продольные напряжения (худший случай - сжатие):</b><br>"
                    f"σ_пр = -α · E · Δt + μ · σ_кц = <b>{sig_pr:.2f} МПа</b><br><br>"
                    f"<b>4. Коэффициент двухосного состояния:</b><br>"
                    f"ψ₁ = √(1 - 0.75·(σ_кц / [σ_кц])²) - 0.5·(σ_кц / [σ_кц]) = <b>{psi:.4f}</b><br><br>"
                    f"<b>5. Допускаемое продольное напряжение:</b><br>"
                    f"[σ_пр] = ψ₁ · [σ_кц] = {psi:.4f} · {sig_kc_allow:.2f} = <b>{sig_pr_allow:.2f} МПа</b>"
                    f"</div>", unsafe_allow_html=True)

        if is_ok:
            st.markdown(
                f"<div class='result-block'>Условие прочности |σ_пр| ≤ [σ_пр] ВЫПОЛНЯЕТСЯ ({abs(sig_pr):.2f} ≤ {sig_pr_allow:.2f})<br>"
                f"Окончательная толщина стенки: {current_delta} мм.</div>", unsafe_allow_html=True)
            st.session_state.delta_n = current_delta

            # Вывод радиуса изгиба для прохода СОД
            rho_min = 1000 * (D_vn / 1000)
            st.write("---")
            st.write("**Минимальный радиус упругого изгиба для прохождения очистных устройств:**")
            st.markdown(
                f"<div class='math-block'>ρ_min = 1000 · D_вн = 1000 · {D_vn / 1000:.3f} = <b>{rho_min:.1f} м</b></div>",
                unsafe_allow_html=True)
            break
        else:
            st.markdown(
                f"<div class='alert-block'>Условие прочности НЕ ВЫПОЛНЯЕТСЯ ({abs(sig_pr):.2f} > {sig_pr_allow:.2f}). "
                f"Увеличиваем толщину стенки.</div>", unsafe_allow_html=True)
            current_delta = get_next_thickness(current_delta + 0.1)
            iteration += 1
            if iteration > 15:
                st.error("Превышен лимит итераций.")
                break

# ==============================================================================
# ЭТАП 3: УСТОЙЧИВОСТЬ
# ==============================================================================
elif page == "3. Расчет общей устойчивости":
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
        rho_izg = st.number_input("Радиус кривизны оси ρ, м", value=1500.0)

    # Геометрия
    D_H_m = st.session_state.D_H / 1000
    delta_m = st.session_state.delta_n / 1000
    D_vn_m = D_H_m - 2 * delta_m
    D_ins = D_H_m + 0.006  # D_н.и с учетом изоляции

    F = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4
    I = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64

    # Нагрузки
    q_met = 78500 * F
    q_prod = 870 * 9.81 * math.pi * D_vn_m ** 2 / 4  # плотность нефти 870
    q_ins = 165.5  # примерный вес изоляции
    q_tr = q_met + q_prod + q_ins

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
                f"<b>1. Геометрические параметры (при $\delta_н = {st.session_state.delta_n}$ мм):</b><br>"
                f"F = {F:.4f} м², I = {I:.6f} м⁴<br><br>"
                f"<b>2. Нагрузки:</b><br>"
                f"Вес трубы с продуктом: q_тр = {q_tr:.2f} Н/м<br>"
                f"Эквивалентное продольное усилие: S = <b>{S:.2f} МН</b><br><br>"
                f"<b>3. Характеристики взаимодействия с грунтом:</b><br>"
                f"Давление грунта: p_гр = {p_gr:.0f} Па<br>"
                f"Касательные напряжения: τ_пр = p_гр · tg({phi_deg}°) = {tau_pr:.0f} Па<br>"
                f"Сопротивление продольному сдвигу: p_0 = \pi · D_{{н.и}} · τ_пр = <b>{p0:.4f} МН/м</b><br>"
                f"Сопротивление вертикальным перемещениям: q_в = <b>{q_v:.4f} МН/м</b><br><br>"
                f"<b>4. Критическое усилие (прямолинейный участок):</b><br>"
                f"N_кр = 4.09 · √(p_0 · q_в · F · E · I) = <b>{N_cr_plast:.2f} МН</b>"
                f"</div>", unsafe_allow_html=True)

    S_allow = (st.session_state.m / 1.1) * N_cr_plast
    if S <= S_allow:
        st.success(f"**Устойчивость обеспечена:** S ({S:.2f} МН) ≤ [S] ({S_allow:.2f} МН)")
    else:
        st.error(f"**Устойчивость НЕ обеспечена:** S ({S:.2f} МН) > [S] ({S_allow:.2f} МН). Требуется балластировка!")

    st.markdown("---")
    st.write("**5. Устойчивость упругоизогнутого участка (ρ = 1500 м)**")
    N_cr_izg = 0.375 * q_v * rho_izg
    S_allow_izg = (st.session_state.m / 1.1) * N_cr_izg
    st.markdown(
        f"<div class='math-block'>N_кр.изг = 0.375 · q_в · ρ = 0.375 · {q_v:.4f} · {rho_izg} = <b>{N_cr_izg:.2f} МН</b></div>",
        unsafe_allow_html=True)
    if S <= S_allow_izg:
        st.success(f"Устойчивость кривой обеспечена: {S:.2f} ≤ {S_allow_izg:.2f} МН")
    else:
        st.error(f"Устойчивость кривой НЕ обеспечена: {S:.2f} > {S_allow_izg:.2f} МН")