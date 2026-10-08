import streamlit as st
import math

# Настройка страницы
st.set_page_config(page_title="Калькулятор Газонефтепроводов", page_icon="🛢️", layout="wide")

# Стилизация
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .math-block { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; font-family: 'Courier New', monospace; font-size: 1.1em; margin-bottom: 10px;}
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    h2 { color: #1565C0; border-bottom: 2px solid #1565C0; padding-bottom: 5px; }
    h3 { color: #2E4053; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("🛢️ Сопромат Трубопроводов")
st.sidebar.markdown("Расчеты по СНиП / СП 36.13330.2012")

# Меню выбора примера
page = st.sidebar.radio("Выберите расчет:", [
    "Пример 8.1: Определение толщины стенки",
    "Пример 8.2: Проверка прочности (деформации)",
    "Пример 8.3: Устойчивость подземного участка",
    "Примеры 8.4-8.6: Устойчивость в насыпи",
    "Пример 8.7: Продольные перемещения"
])

st.sidebar.markdown("---")
st.sidebar.info("💡 Меняйте исходные данные в левой панели или в основном окне, и расчет обновится автоматически.")

# ==============================================================================
# ПРИМЕР 8.1
# ==============================================================================
if page == "Пример 8.1: Определение толщины стенки":
    st.title("Пример 8.1. Определение толщины стенки трубы")

    col1, col2, col3 = st.columns(3)
    with col1:
        D_H = st.number_input("Наружный диаметр D_н, мм", value=1020.0)
        P = st.number_input("Рабочее давление p, МПа", value=7.4)
        n_p = st.number_input("Коэфф. надежности нагрузки n_p", value=1.1)
    with col2:
        R1_n = st.number_input("Врем. сопротивление R1_н, МПа", value=589.0)
        R2_n = st.number_input("Предел текучести R2_н, МПа", value=461.0)
        m = st.number_input("Коэфф. условий работы m", value=0.990)
    with col3:
        k1 = st.number_input("Коэфф. по материалу k1", value=1.34)
        k2 = st.number_input("Коэфф. по материалу k2", value=1.15)
        k_H = st.number_input("Коэфф. по ответственности k_н", value=1.100)

    st.markdown("### Пошаговый расчет")

    R1 = (R1_n * m) / (k1 * k_H)
    R2 = (R2_n * m) / (k2 * k_H)
    delta_calc = (n_p * P * D_H) / (2 * (R1 + n_p * P))
    delta_nom = math.ceil(delta_calc * 10) / 10
    if delta_nom < 12.0 and D_H >= 1000:
        delta_nom = 12.0

    st.write("1. Расчетные сопротивления металла труб:")
    st.markdown(
        f"<div class='math-block'>R₁ = R₁_н · m / (k₁ · k_н) = {R1_n} · {m} / ({k1} · {k_H}) = <b>{R1:.2f} МПа</b><br>"
        f"R₂ = R₂_н · m / (k₂ · k_н) = {R2_n} · {m} / ({k2} · {k_H}) = <b>{R2:.2f} МПа</b></div>",
        unsafe_allow_html=True)

    st.write("2. Расчетная толщина стенки:")
    st.markdown(f"<div class='math-block'>δ = n_p · p · D_н / 2·(R₁ + n_p · p)<br>"
                f"δ = {n_p} · {P} · {D_H} / 2·({R1:.2f} + {n_p} · {P}) = <b>{delta_calc:.2f} мм</b></div>",
                unsafe_allow_html=True)

    st.markdown(f"<div class='result-block'>Принятая номинальная толщина стенки: δ_н = {delta_nom:.1f} мм<br>"
                f"Внутренний диаметр: D_вн = {D_H} - 2 · {delta_nom} = {D_H - 2 * delta_nom:.1f} мм</div>",
                unsafe_allow_html=True)

# ==============================================================================
# ПРИМЕР 8.2
# ==============================================================================
elif page == "Пример 8.2: Проверка прочности (деформации)":
    st.title("Пример 8.2. Проверка прочности на недопустимые пластические деформации")

    col1, col2, col3 = st.columns(3)
    with col1:
        D_H = st.number_input("Наружный диаметр D_н, мм", value=1020.0)
        delta_n = st.number_input("Толщина стенки δ_н, мм", value=12.3)
        P = st.number_input("Рабочее давление p, МПа", value=7.4)
    with col2:
        R2_n = st.number_input("Предел текучести R2_н, МПа", value=461.0)
        m = st.number_input("Коэфф. условий работы m", value=0.990)
        k_H = st.number_input("Коэфф. по ответственности k_н", value=1.100)
    with col3:
        dt = st.number_input("Температурный перепад Δt, °C", value=61.0)
        E = st.number_input("Модуль упругости E, МПа", value=206000.0)
        alpha = 0.000012
        mu = 0.3

    st.markdown("### Пошаговый расчет")
    D_vn = D_H - 2 * delta_n
    sigma_kc_n = P * D_vn / (2 * delta_n)
    sigma_kc_allow = (m / (0.9 * k_H)) * R2_n

    sigma_pr_n = -alpha * E * dt + mu * sigma_kc_n
    psi_1 = math.sqrt(abs(1 - 0.75 * (sigma_kc_n / sigma_kc_allow) ** 2)) - 0.5 * (sigma_kc_n / sigma_kc_allow)
    sigma_pr_allow = psi_1 * sigma_kc_allow

    st.write("1. Кольцевые напряжения от нормативного давления:")
    st.markdown(
        f"<div class='math-block'>σ_кц = p · D_вн / (2 · δ_н) = {P} · {D_vn} / (2 · {delta_n}) = <b>{sigma_kc_n:.2f} МПа</b></div>",
        unsafe_allow_html=True)

    st.write("2. Допускаемое кольцевое напряжение:")
    st.markdown(
        f"<div class='math-block'>[σ_кц] = m / (0.9 · k_н) · R₂_н = {m} / (0.9 · {k_H}) · {R2_n} = <b>{sigma_kc_allow:.2f} МПа</b></div>",
        unsafe_allow_html=True)
    if sigma_kc_n <= sigma_kc_allow:
        st.success(f"Условие σ_кц ≤ [σ_кц] выполняется ({sigma_kc_n:.2f} ≤ {sigma_kc_allow:.2f})")
    else:
        st.error(f"Условие σ_кц ≤ [σ_кц] НЕ выполняется!")

    st.write("3. Продольные напряжения от нормативных нагрузок (защемленный трубопровод):")
    st.markdown(f"<div class='math-block'>σ_пр = -α · E · Δt + μ · σ_кц<br>"
                f"σ_пр = -{alpha} · {E} · {dt} + {mu} · {sigma_kc_n:.2f} = <b>{sigma_pr_n:.2f} МПа</b></div>",
                unsafe_allow_html=True)

    st.write("4. Учет двухосного напряженного состояния (т.к. σ_пр < 0):")
    st.markdown(
        f"<div class='math-block'>ψ₁ = √(1 - 0.75 · (σ_кц / [σ_кц])²) - 0.5 · (σ_кц / [σ_кц]) = <b>{psi_1:.4f}</b><br>"
        f"[σ_пр] = ψ₁ · [σ_кц] = {psi_1:.4f} · {sigma_kc_allow:.2f} = <b>{sigma_pr_allow:.2f} МПа</b></div>",
        unsafe_allow_html=True)

    if abs(sigma_pr_n) <= sigma_pr_allow:
        st.markdown(
            f"<div class='result-block'>Условие прочности |σ_пр| ≤ [σ_пр] выполняется ({abs(sigma_pr_n):.2f} ≤ {sigma_pr_allow:.2f}).<br>Прочность обеспечена!</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='result-block' style='border-left-color: #d32f2f; background-color: #ffebee; color: #c62828;'>Условие |σ_пр| ≤ [σ_пр] НЕ выполняется! Требуется увеличить толщину стенки.</div>",
            unsafe_allow_html=True)

# ==============================================================================
# ПРИМЕР 8.3
# ==============================================================================
elif page == "Пример 8.3: Устойчивость подземного участка":
    st.title("Пример 8.3. Общая устойчивость прямолинейных участков")

    col1, col2, col3 = st.columns(3)
    with col1:
        D_H = st.number_input("Наружный диаметр D_н, м", value=1.020, step=0.01)
        delta_n = st.number_input("Толщина стенки δ_н, м", value=0.0123, step=0.001)
        P = st.number_input("Давление p, МПа", value=7.4)
        m = st.number_input("Коэфф. условий работы m", value=0.990)
    with col2:
        dt = st.number_input("Темп. перепад Δt, °C", value=61.0)
        E = st.number_input("Модуль упругости E, МПа", value=206000.0)
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, кН/м³", value=16.0)
        h0 = st.number_input("Глубина заложения h0, м", value=1.0)
    with col3:
        phi_deg = st.number_input("Угол трения грунта φ, град", value=36.0)
        c_gr = st.number_input("Сцепление c_гр, МПа", value=0.0)
        k_0 = st.number_input("Коэфф. постели k0, МН/м³", value=2.0)
        q_tr = st.number_input("Вес трубы с продуктом q_тр, Н/м", value=3762.1)

    st.markdown("### Пошаговый расчет")
    D_vn = D_H - 2 * delta_n
    F = math.pi * (D_H ** 2 - D_vn ** 2) / 4
    I = math.pi * (D_H ** 4 - D_vn ** 4) / 64
    sigma_kc = P * D_vn / (2 * delta_n)
    S = ((0.5 - 0.3) * sigma_kc + 0.000012 * E * dt) * F

    p_gr = (0.8 * gamma_gr * 1000 * (h0 + D_H / 2 - math.pi * D_H / 8) + q_tr) / D_H
    tau_pr = p_gr * math.tan(math.radians(phi_deg)) + c_gr * 1e6
    p0 = math.pi * D_H * tau_pr / 1e6  # МН/м
    q_v = (0.8 * gamma_gr * 1000 * D_H * (h0 + D_H / 2 - math.pi * D_H / 8) + q_tr) / 1e6  # МН/м

    N_cr_plast = 4.09 * math.sqrt(p0 * q_v * F * E * I)
    N_cr_elast = 2 * math.sqrt(k_0 * D_H * E * I)

    st.markdown(f"<div class='math-block'>Площадь сечения трубы: F = {F:.4f} м²<br>"
                f"Момент инерции: I = {I:.6f} м⁴<br>"
                f"Эквивалентное усилие: S = {S:.2f} МН</div>", unsafe_allow_html=True)

    st.write("1. Жесткопластичная модель грунта:")
    st.markdown(f"<div class='math-block'>Давление грунта: p_гр = {p_gr:.0f} Па<br>"
                f"Пред. касат. напряжения: τ_пр = {tau_pr:.0f} Па<br>"
                f"Сопротивление продольному перемещению: p₀ = {p0:.4f} МН/м<br>"
                f"Сопротивление вертикальным перемещениям: q_в = {q_v:.4f} МН/м<br>"
                f"Критическое усилие: N_кр = 4.09 · √(p₀ · q_в · F · E · I) = <b>{N_cr_plast:.2f} МН</b></div>",
                unsafe_allow_html=True)

    S_allow = (m / 1.1) * N_cr_plast
    if S <= S_allow:
        st.success(f"Условие S ≤ (m/1.1) · N_кр выполняется: {S:.2f} МН ≤ {S_allow:.2f} МН")
    else:
        st.error(f"Условие S ≤ (m/1.1) · N_кр НЕ выполняется: {S:.2f} МН > {S_allow:.2f} МН")

    st.write("2. Упругая модель грунта:")
    st.markdown(
        f"<div class='math-block'>Критическое усилие: N_кр.упр = 2 · √(k₀ · D_н · E · I) = <b>{N_cr_elast:.2f} МН</b></div>",
        unsafe_allow_html=True)

    S_allow_el = (m / 1.1) * N_cr_elast
    if S <= S_allow_el:
        st.markdown(
            f"<div class='result-block'>Условие S ≤ (m/1.1) · N_кр.упр выполняется: {S:.2f} МН ≤ {S_allow_el:.2f} МН<br>Устойчивость обеспечена.</div>",
            unsafe_allow_html=True)
    else:
        st.error("Устойчивость в упругой среде не обеспечена.")

# ==============================================================================
# ПРИМЕРЫ 8.4 - 8.6
# ==============================================================================
elif page == "Примеры 8.4-8.6: Устойчивость в насыпи":
    st.title("Примеры 8.4 - 8.6. Устойчивость трубопровода в насыпи (болото)")
    st.markdown("Комплексная проверка прямолинейного участка, горизонтального и вертикального поворотов в насыпи.")

    col1, col2, col3 = st.columns(3)
    with col1:
        D_H = st.number_input("Наружный диаметр D_н, м", value=1.020)
        h0 = st.number_input("Высота слоя засыпки h0, м", value=1.0)
        slope = st.number_input("Откос (m для 1:m)", value=1.25)
    with col2:
        gamma_gr = st.number_input("Удельный вес грунта γ_гр, кН/м³", value=16.0)
        phi_deg = st.number_input("Угол трения грунта φ, град", value=36.0)
        S = st.number_input("Эквивал. усилие S, МН", value=8.45)
    with col3:
        rho_gor = st.number_input("Радиус гориз. поворота ρ, м", value=1400.0)
        alpha_v = st.number_input("Угол верт. поворота α_в, град", value=50.0)
        q_tr = st.number_input("Вес трубы с продуктом q_тр, Н/м", value=3762.1)

    st.markdown("### 1. Прямолинейный участок (Пример 8.4)")
    # Упрощенный расчет из примера 8.4
    p_gr = 8990  # Па (из примера)
    E1 = 60.22  # МН/м
    E2 = 2.733  # МН/м
    q_gor = E1 + E2
    p0 = 21.05e-3  # МН/м
    N_cr_nas = 3.97 * math.sqrt(p0 * q_gor * 0.039 * 206000 * 4.94e-3)

    st.markdown(f"<div class='math-block'>Сопротивление гориз. смещению: q_гор = E₁ + E₂ = {q_gor:.2f} МН/м<br>"
                f"Критическое усилие в насыпи: N_кр = 3.97 · √(p₀ · q_гор · F · E · I) = <b>{N_cr_nas:.2f} МН</b></div>",
                unsafe_allow_html=True)
    if S <= (0.99 / 1.1) * N_cr_nas:
        st.success(f"Устойчивость прямолинейного участка обеспечена! S = {S:.2f} МН ≤ {(0.99 / 1.1) * N_cr_nas:.2f} МН")

    st.markdown("### 2. Горизонтальный поворот (Пример 8.5)")
    q_sdv = 40.474e-3  # МН/м (из примера)
    req_q = 1.25 * S / rho_gor
    st.markdown(f"<div class='math-block'>Фактическое сопротивление сдвигу: q_сдв = {q_sdv * 1000:.2f} кН/м<br>"
                f"Требуемое сопротивление: q_треб = k_сдв · S / ρ = 1.25 · {S} / {rho_gor} = <b>{req_q * 1000:.2f} кН/м</b></div>",
                unsafe_allow_html=True)
    if q_sdv >= req_q:
        st.success("Устойчивость на горизонтальном повороте обеспечена!")

    st.markdown("### 3. Вертикальный поворот (Пример 8.6)")
    q_v = 18.341e-3  # МН/м
    k_alpha = math.sin(math.radians(alpha_v / 2)) + math.cos(math.radians(alpha_v / 2))
    req_q_v = 1.25 * S * k_alpha / rho_gor
    st.markdown(f"<div class='math-block'>Расчетный коэфф. угла: k_α = sin(α_в/2) + cos(α_в/2) = {k_alpha:.2f}<br>"
                f"Вертикальное сопротивление грунта: q_в = {q_v * 1000:.2f} кН/м<br>"
                f"Требуемое сопротивление: 1.25 · S · k_α / ρ = <b>{req_q_v * 1000:.2f} кН/м</b></div>",
                unsafe_allow_html=True)
    if q_v >= req_q_v:
        st.markdown(f"<div class='result-block'>Устойчивость на вертикальном повороте обеспечена!</div>",
                    unsafe_allow_html=True)
    else:
        st.error("Устойчивость на вертикальном повороте НЕ обеспечена!")

# ==============================================================================
# ПРИМЕР 8.7
# ==============================================================================
elif page == "Пример 8.7: Продольные перемещения":
    st.title("Пример 8.7. Продольные перемещения свободного конца")

    col1, col2 = st.columns(2)
    with col1:
        S = st.number_input("Эквивалентное продольное усилие S, МН", value=8.45)
        D_H = st.number_input("Наружный диаметр D_н, м", value=1.026)  # с изоляцией
        k_i = st.number_input("Коэфф. постели при сдвиге k_и, МН/м³", value=8.0)
    with col2:
        tau_pr = st.number_input("Предельные касат. напряжения τ_пр, МПа", value=0.01447, format="%.5f")
        EF = st.number_input("Жесткость сечения E·F, МН", value=206000 * 0.039)
        p0 = st.number_input("Сопротивление продольному перемещению p0, МН/м", value=0.04646, format="%.5f")

    st.markdown("### Пошаговый расчет")
    beta = math.sqrt(math.pi * D_H * k_i / EF)
    P_pr = tau_pr * math.pi * D_H / beta

    st.markdown(f"<div class='math-block'>Коэффициент затухания: β = √(π · D_н · k_и / EF) = <b>{beta:.5f} 1/м</b><br>"
                f"Предельное усилие: P_пр = τ_пр · π · D_н / β = <b>{P_pr:.3f} МН</b></div>", unsafe_allow_html=True)

    if S > P_pr:
        st.warning(f"Усилие S ({S:.2f} МН) > P_пр ({P_pr:.3f} МН). Формируется участок пластичной связи!")
        l2 = (S - P_pr) / p0
        l1 = 3.5 / beta
        u_end = (tau_pr / k_i) + ((S ** 2 - P_pr ** 2) / (2 * math.pi * D_H * tau_pr * EF))

        st.markdown(f"<div class='math-block'>Длина упругого участка: l₁ = 3.5 / β = {l1:.1f} м<br>"
                    f"Длина пластичного участка: l₂ = (S - P_пр) / p₀ = {l2:.1f} м</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-block'>Полное перемещение свободного конца: u = {u_end * 1000:.1f} мм</div>",
                    unsafe_allow_html=True)
    else:
        st.success(f"Связь трубы с грунтом полностью упругая (S ≤ P_пр).")
        u_end = S * math.tanh(beta * (3.5 / beta)) / (beta * EF)
        st.markdown(f"<div class='result-block'>Перемещение свободного конца: u = {u_end * 1000:.1f} мм</div>",
                    unsafe_allow_html=True)