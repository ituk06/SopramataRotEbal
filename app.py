import streamlit as st
import math
import os
import pandas as pd
import numpy as np
import pydeck as pdk
import datetime

# --- НАСТРОЙКА СТРАНИЦЫ И СТИЛИ ---
st.set_page_config(page_title="Расчёт трубопровода 8.1–8.6", page_icon="🛢️", layout="wide")

st.markdown("""
    <style>
    .step-box { background-color: #f8f9fa; padding: 12px 16px; border-radius: 6px; border-left: 4px solid #2C3E50; margin-bottom: 12px; }
    .step-title { font-weight: bold; color: #1a252f; margin-bottom: 4px; font-size: 1.05em; }
    .sub-line { color: #555; font-size: 0.95em; margin: 4px 0; font-family: monospace; }
    .ans-line { font-weight: bold; color: #1b5e20; font-size: 1.05em; margin-top: 4px; }
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .error-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; font-weight: bold; margin-bottom: 20px;}
    .info-text { font-size: 1.02em; color: #34495E; margin-bottom: 15px; line-height: 1.5; background-color: #e3f2fd; padding: 12px; border-radius: 5px; border-left: 4px solid #1976d2;}
    .svg-chart { width: 100%; max-width: 820px; margin: 12px auto; background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 8px; }

    @media print {
        .page-break { page-break-before: always; }
        .no-break { page-break-inside: avoid; }
        header, footer, .stButton, section[data-testid="stSidebar"] { display: none !important; }
        .step-box { border: 1px solid #ddd; border-left: 3px solid #000; background-color: #fff !important; }
        .svg-chart { border: none; page-break-inside: avoid; }
    }
    </style>
""", unsafe_allow_html=True)

SORTAMENT = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.3, 11.0, 12.0, 12.3, 14.0, 15.7, 16.0, 17.5, 18.7, 19.1, 20.0, 21.0,
             22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 30.0, 32.0, 34.0, 36.0]

CLIMATE_DATA = {
    "г. Сургут (ХМАО)": {"t_min": -43.0, "t_max": 26.0, "lat": 61.25, "lon": 73.4167, "snow": 4, "wind": 2},
    "г. Уфа (Башкортостан)": {"t_min": -35.0, "t_max": 28.0, "lat": 54.7388, "lon": 55.9721, "snow": 5, "wind": 2},
    "г. Губкинский (ЯНАО)": {"t_min": -50.0, "t_max": 30.0, "lat": 64.434, "lon": 76.5026, "snow": 5, "wind": 3},
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


def get_next_thickness(calc_thickness, min_thickness=4.0):
    target = max(calc_thickness, min_thickness)
    for t in SORTAMENT:
        if t >= target: return t
    return float(math.ceil(target))


# --- ФУНКЦИЯ ОКРУГЛЕНИЯ ДО ЗНАЧАЩИХ ЦИФР (БЕЗ ЛИШНИХ НУЛЕЙ) ---
def fmt(val):
    if val is None:
        return "—"
    if isinstance(val, str):
        return val
    try:
        val = float(val)
        if val == 0.0:
            return "0"
        if abs(val - round(val)) < 1e-7:
            return str(int(round(val)))
        abs_v = abs(val)
        if abs_v < 0.0001:
            s = f"{val:.7f}"
        elif abs_v < 0.01:
            s = f"{val:.5f}"
        elif abs_v < 10:
            s = f"{val:.4f}"
        else:
            s = f"{val:.2f}"
        s = s.rstrip('0').rstrip('.')
        return s.replace('.', ',')
    except:
        return str(val)


# --- ПРЕДУСТАНОВКИ ВАРИАНТОВ ---
PRESET_TETRAD = {
    'product_type': "Нефть", 't_product': 5.0, 't_x': -45.0, 't_m': 30.0,
    'D_H': 1020.0, 'delta_n': 11.0, 'rho_izg': 1020.0,
    'P': 6.0, 'n_p': 1.1,
    'R1_n': 490.0, 'R2_n': 345.0, 'E': 206000.0, 'mu': 0.3, 'alpha': 0.000012,
    'm': 0.990, 'k1': 1.34, 'k2': 1.15, 'k_H': 1.100, 'gamma_m': 78.5,
    'gamma_gr': 17.0, 'phi_deg': 36.0, 'c_gr': 0.0, 'k_0': 5.0, 'k_i': 5.0,
    'h0': 1.2, 'n_gr': 0.95, 'h1': 1.026, 'H': 2.2, 'b': 0.85, 'alpha_H': 39.0, 'beta_nom': 19.5,
    'delta_ins': 3.0, 'rho_ins': 1750.0, 'n_sv': 0.95, 'n_pr': 0.95, 'rho_prod': 870.0,
    'rho_gor': 1400.0, 'f_gr': 0.3, 'k_sdv': 1.25,
    'rho_v': 1400.0, 'alpha_v': 50.0, 'k_np': 1.25
}

PRESET_DOCX = {
    'product_type': "Нефть", 't_product': 20.0, 't_x': -40.0, 't_m': 32.0,
    'D_H': 630.0, 'delta_n': 10.0, 'rho_izg': 1000.0,
    'P': 8.0, 'n_p': 1.15,
    'R1_n': 590.0, 'R2_n': 440.0, 'E': 206000.0, 'mu': 0.3, 'alpha': 0.000012,
    'm': 0.990, 'k1': 1.34, 'k2': 1.15, 'k_H': 1.155, 'gamma_m': 78.5,
    'gamma_gr': 17.0, 'phi_deg': 36.0, 'c_gr': 0.0, 'k_0': 5.0, 'k_i': 5.0,
    'h0': 1.2, 'n_gr': 0.95, 'h1': 1.026, 'H': 2.2, 'b': 0.85, 'alpha_H': 39.0, 'beta_nom': 19.5,
    'delta_ins': 3.0, 'rho_ins': 1750.0, 'n_sv': 0.95, 'n_pr': 0.95, 'rho_prod': 1000.0,
    'rho_gor': 1400.0, 'f_gr': 0.3, 'k_sdv': 1.25,
    'rho_v': 1400.0, 'alpha_v': 50.0, 'k_np': 1.25
}

if 'params' not in st.session_state:
    st.session_state.params = PRESET_TETRAD.copy()


def p_input(label, key, step=None):
    w_key = f"w_{key}"
    st.session_state[w_key] = float(st.session_state.params[key])

    def _sync():
        st.session_state.params[key] = float(st.session_state[w_key])

    return st.number_input(label, key=w_key, step=step, format="%g", on_change=_sync)


# --- ЕДИНЫЙ МАТЕМАТИЧЕСКИЙ ДВИЖОК ПО МЕТОДИЧКЕ (8.1 - 8.7) ---
def calculate_all(p):
    c = {}
    # 8.1
    c['R1'] = p['R1_n'] * p['m'] / (p['k1'] * p['k_H'])
    c['R2'] = p['R2_n'] * p['m'] / (p['k2'] * p['k_H'])
    c['delta_p'] = (p['n_p'] * p['P'] * p['D_H']) / (2.0 * (c['R1'] + p['n_p'] * p['P']))
    c['d_min_1000'] = 12.0 if p['D_H'] >= 1000.0 else 0.0
    c['delta_min'] = max(p['D_H'] / 100.0, 4.0, c['d_min_1000'])
    c['delta_treb'] = max(c['delta_p'], c['delta_min'])
    c['delta_sort'] = get_next_thickness(c['delta_treb'], c['delta_min'])
    c['dt_x'] = p['t_product'] - p['t_x']
    c['dt_m'] = p['t_product'] - p['t_m']
    c['D_vn'] = p['D_H'] - 2.0 * p['delta_n']
    c['ok_81'] = p['delta_n'] >= c['delta_treb']

    # 8.2
    D_H_m = p['D_H'] / 1000.0
    D_vn_m = c['D_vn'] / 1000.0
    delta_m = p['delta_n'] / 1000.0
    D_ins_m = (p['D_H'] + 2.0 * p['delta_ins']) / 1000.0
    c['D_H_m'], c['D_vn_m'], c['delta_m'], c['D_ins_m'] = D_H_m, D_vn_m, delta_m, D_ins_m

    c['sig_kc_n'] = p['P'] * D_vn_m / (2.0 * delta_m)
    c['sig_kc'] = p['n_p'] * c['sig_kc_n']
    c['sig_pr_N'] = -p['alpha'] * p['E'] * c['dt_x'] + p['mu'] * c['sig_kc']
    c['R2_d'] = p['m'] * p['R2_n'] / (0.9 * p['k_H'])

    ratio_kc = c['sig_kc_n'] / c['R2_d'] if c['R2_d'] > 0 else 0
    under = max(0.0, 1.0 - 0.75 * (ratio_kc ** 2))
    c['psi_1'] = math.sqrt(under) - 0.5 * ratio_kc if (1.0 - 0.75 * (ratio_kc ** 2)) >= 0 else 0.0
    c['bend_stress'] = p['E'] * D_H_m / (2.0 * p['rho_izg'])

    # Холодное замыкание (оба края)
    base_x = p['mu'] * c['sig_kc_n'] - p['alpha'] * p['E'] * c['dt_x']
    c['sig_pr_x_minus'] = base_x - c['bend_stress']
    c['sig_pr_x_plus'] = base_x + c['bend_stress']
    c['sig_pr_x'] = c['sig_pr_x_minus'] if abs(c['sig_pr_x_minus']) >= abs(c['sig_pr_x_plus']) else c['sig_pr_x_plus']

    # Теплое замыкание (оба края)
    base_m = p['mu'] * c['sig_kc_n'] - p['alpha'] * p['E'] * c['dt_m']
    c['sig_pr_m_minus'] = base_m - c['bend_stress']
    c['sig_pr_m_plus'] = base_m + c['bend_stress']
    c['sig_pr_m'] = c['sig_pr_m_plus'] if abs(c['sig_pr_m_plus']) >= abs(c['sig_pr_m_minus']) else c['sig_pr_m_minus']

    c['allow_x_minus'] = (c['psi_1'] if c['sig_pr_x_minus'] < 0 else 1.0) * c['R2_d']
    c['allow_x_plus'] = (c['psi_1'] if c['sig_pr_x_plus'] < 0 else 1.0) * c['R2_d']
    c['allow_m_minus'] = (c['psi_1'] if c['sig_pr_m_minus'] < 0 else 1.0) * c['R2_d']
    c['allow_m_plus'] = (c['psi_1'] if c['sig_pr_m_plus'] < 0 else 1.0) * c['R2_d']

    c['ok_82_kc'] = c['sig_kc_n'] <= c['R2_d']
    c['ok_82_xm'] = abs(c['sig_pr_x_minus']) <= c['allow_x_minus']
    c['ok_82_xp'] = abs(c['sig_pr_x_plus']) <= c['allow_x_plus']
    c['ok_82_mm'] = abs(c['sig_pr_m_minus']) <= c['allow_m_minus']
    c['ok_82_mp'] = abs(c['sig_pr_m_plus']) <= c['allow_m_plus']
    c['ok_82'] = all([c['ok_82_kc'], c['ok_82_xm'], c['ok_82_xp'], c['ok_82_mm'], c['ok_82_mp']])

    # 8.3
    c['F'] = math.pi * (D_H_m ** 2 - D_vn_m ** 2) / 4.0
    c['I'] = math.pi * (D_H_m ** 4 - D_vn_m ** 4) / 64.0
    c['q_m_n'] = (p['gamma_m'] * 1000.0) * c['F']
    c['q_iz_n'] = p['rho_ins'] * 9.81 * math.pi * (D_ins_m ** 2 - D_H_m ** 2) / 4.0
    c['q_pr_n'] = (p['rho_prod'] if p['product_type'] == "Нефть" else 0.8) * 9.81 * math.pi * (D_vn_m ** 2) / 4.0
    c['q_tr'] = p['n_sv'] * (c['q_m_n'] + c['q_iz_n']) + p['n_pr'] * c['q_pr_n']

    c['S'] = ((0.5 - p['mu']) * c['sig_kc'] + p['alpha'] * p['E'] * c['dt_x']) * c['F']
    c['tan2_45_phi'] = math.tan(math.radians(45.0 - p['phi_deg'] / 2.0)) ** 2
    gamma_gr_N = p['gamma_gr'] * 1000.0
    c['gamma_gr_N'] = gamma_gr_N

    c['p_gr_83'] = (2.0 * p['n_gr'] * gamma_gr_N * D_ins_m * (
                (p['h0'] + D_ins_m / 8.0) + (p['h0'] + D_ins_m / 2.0) * c['tan2_45_phi']) + c['q_tr']) / (
                               math.pi * D_ins_m)
    c['tau_pr_83'] = c['p_gr_83'] * math.tan(math.radians(p['phi_deg'])) + p['c_gr'] * 1000.0
    c['p0_83'] = math.pi * D_ins_m * c['tau_pr_83']
    c['q_v_83'] = p['n_gr'] * gamma_gr_N * D_ins_m * (p['h0'] + D_ins_m / 2.0 - math.pi * D_ins_m / 8.0) + c['q_tr']

    E_Pa = p['E'] * 1e6
    k0_Pa = p['k_0'] * 1e6
    c['N_kr_pl'] = 4.09 * (
                (c['p0_83'] ** 2 * c['q_v_83'] ** 4 * c['F'] ** 2 * E_Pa ** 5 * c['I'] ** 3) ** (1.0 / 11.0)) / 1e6
    c['N_kr_up'] = 2.0 * math.sqrt(k0_Pa * D_H_m * E_Pa * c['I']) / 1e6
    c['lam'] = 2.0 * math.pi * ((E_Pa * c['I'] / (k0_Pa * D_H_m)) ** 0.25)

    qv_EI_13 = (c['q_v_83'] / (E_Pa * c['I'])) ** (1.0 / 3.0)
    c['theta'] = 1.0 / (p['rho_izg'] * qv_EI_13)
    c['Z'] = math.sqrt(c['p0_83'] * c['F'] / (c['q_v_83'] * c['I'])) / qv_EI_13
    c['N_kr_nom'] = p['beta_nom'] * ((c['q_v_83'] ** 2 * E_Pa * c['I']) ** (1.0 / 3.0)) / 1e6
    c['N_kr_izg'] = 0.375 * c['q_v_83'] * p['rho_izg'] / 1e6
    c['N_kr_min'] = min(c['N_kr_nom'], c['N_kr_izg'])
    c['rho_treb'] = 1.1 * (c['S'] * 1e6) / (p['m'] * 0.375 * c['q_v_83'])
    c['N_kr_1400'] = 0.375 * c['q_v_83'] * 1400.0 / 1e6

    c['allow_83_pl'] = (p['m'] / 1.1) * c['N_kr_pl']
    c['allow_83_up'] = (p['m'] / 1.1) * c['N_kr_up']
    c['allow_83_min'] = (p['m'] / 1.1) * c['N_kr_min']
    c['ok_83_pl'] = c['S'] <= c['allow_83_pl']
    c['ok_83_up'] = c['S'] <= c['allow_83_up']
    c['ok_83_izg'] = c['S'] <= c['allow_83_min']
    c['ok_83'] = all([c['ok_83_pl'], c['ok_83_up'], c['ok_83_izg']])

    # 8.4
    c['cot_aH'] = 1.0 / math.tan(math.radians(p['alpha_H']))
    c['tan_45_phi2'] = math.tan(math.radians(45.0 - p['phi_deg'] / 2.0))
    c['Kp'] = math.tan(math.radians(45.0 + p['phi_deg'] / 2.0)) ** 2
    c['Ka'] = c['tan2_45_phi']

    c['h2'] = p['h1'] - (p['b'] + p['h0'] * c['cot_aH'] - 0.5 * p['h1']) * c['tan_45_phi2']
    c['p_gr_84'] = p['n_gr'] * gamma_gr_N * p['h0'] * (p['b'] + 0.5 * p['h0'] * c['cot_aH']) / (
                p['b'] + p['h0'] * c['cot_aH'])
    c['E1'] = p['n_gr'] * gamma_gr_N * (p['h1'] ** 2 - c['h2'] ** 2) * c['Kp'] / 2.0 + c['p_gr_84'] * p['h1'] * c[
        'Kp'] + 2.0 * p['n_gr'] * (p['c_gr'] * 1000.0) * (p['h1'] - c['h2']) * math.sqrt(c['Kp'])
    c['E_akt'] = (p['n_gr'] * gamma_gr_N * (p['h1'] ** 2) * c['Ka'] / 2.0 + c['p_gr_84'] * p['h1'] * c['Ka']) if p[
                                                                                                                     'c_gr'] == 0 else 0.0
    c['E2'] = c['q_tr'] * math.tan(math.radians(p['phi_deg']))
    c['q_gor'] = c['E1'] - c['E_akt'] + c['E2']
    c['tau_pr_84'] = c['p_gr_84'] * math.tan(math.radians(p['phi_deg'])) + p['c_gr'] * 1000.0
    c['p0_84'] = math.pi * D_ins_m * c['tau_pr_84']
    c['N_kr_84'] = 3.97 * (
                (c['p0_84'] ** 2 * c['q_gor'] ** 4 * c['F'] ** 2 * E_Pa ** 5 * c['I'] ** 3) ** (1.0 / 11.0)) / 1e6
    c['allow_84'] = (p['m'] / 1.1) * c['N_kr_84']
    c['min_2b'] = max(1.5 * D_H_m, 1.5)
    c['ok_84_ust'] = c['S'] <= c['allow_84']
    c['ok_84_2b'] = (2.0 * p['b']) >= c['min_2b']
    c['ok_84_h0'] = p['h0'] >= 0.8
    c['ok_84_aH'] = p['alpha_H'] <= 39.0
    c['ok_84'] = all([c['ok_84_ust'], c['ok_84_2b'], c['ok_84_h0'], c['ok_84_aH']])

    # 8.5
    c['a_low'] = p['b'] + p['H'] / math.tan(math.radians(p['alpha_H']))
    c['q_sdv'] = (p['n_gr'] * gamma_gr_N * math.tan(math.radians(p['phi_deg'])) * p['H'] * (
                (2.0 * c['a_low'] - D_ins_m) + (2.0 * p['b'] - D_ins_m)) / 4.0 +
                  p['f_gr'] * (c['q_tr'] + p['n_gr'] * gamma_gr_N * D_ins_m * (p['H'] - D_ins_m)) +
                  p['n_gr'] * (p['c_gr'] * 1000.0) * (2.0 * p['b'] - D_ins_m) / 2.0)
    c['q_sdv_treb'] = p['k_sdv'] * (c['S'] * 1e6) / p['rho_gor']
    c['ok_85'] = c['q_sdv'] >= c['q_sdv_treb']

    # 8.6
    c['l_kr'] = 2.0 * p['rho_v'] * math.sin(math.radians(p['alpha_v'] / 2.0))
    c['f_izg'] = 2.0 * p['rho_v'] * (math.sin(math.radians(p['alpha_v'] / 4.0)) ** 2)
    c['k_alpha'] = 1.0 if p['alpha_v'] <= 45.0 else math.sqrt(
        math.sin(math.radians(p['alpha_v'] / 2.0)) ** 2 + math.cos(math.radians(p['alpha_v'] / 2.0)) ** 4)
    c['q_v_treb1'] = 2.0 * p['k_np'] * (c['S'] * 1e6) / (
                c['l_kr'] * math.sqrt(1.0 + ((c['l_kr'] / c['f_izg']) ** 2) / 16.0)) if c['f_izg'] > 0 else 0.0
    c['q_v_treb2'] = p['k_np'] * (c['S'] * 1e6) / (c['k_alpha'] * p['rho_v'])
    c['rho_v_min'] = p['rho_v'] * max(c['q_v_treb1'], c['q_v_treb2']) / c['q_v_83']
    c['ok_86_1'] = c['q_v_83'] >= c['q_v_treb1']
    c['ok_86_2'] = c['q_v_83'] >= c['q_v_treb2']
    c['ok_86'] = c['ok_86_1'] and c['ok_86_2']

    # 8.7 (Раздел 5 — эпюры и продольные перемещения по стр. 81 методички)
    q_tr_87 = 1.1 * (c['q_m_n'] + c['q_iz_n']) + 1.0 * c['q_pr_n']
    c['p_gr_87'] = (2.0 * 1.2 * gamma_gr_N * D_ins_m * (
                (p['h0'] + D_ins_m / 8.0) + (p['h0'] + D_ins_m / 2.0) * c['tan2_45_phi']) + q_tr_87) / (
                               math.pi * D_ins_m)
    c['tau_pr_87'] = c['p_gr_87'] * math.tan(math.radians(p['phi_deg'])) + p['c_gr'] * 1000.0
    c['beta_87'] = math.sqrt(math.pi * D_H_m * (p['k_i'] * 1e6) / (E_Pa * c['F']))
    c['p0_87'] = math.pi * D_H_m * c['tau_pr_87']
    c['l1_87'] = 3.5 / c['beta_87']
    c['P_pr_87'] = (c['tau_pr_87'] * c['beta_87'] * E_Pa * c['F'] / ((p['k_i'] * 1e6) * math.tanh(3.5))) / 1e6

    S_abs = abs(c['S'])
    if S_abs > c['P_pr_87']:
        c['l2_87'] = (S_abs - c['P_pr_87']) * 1e6 / c['p0_87']
        c['u_end'] = ((c['tau_pr_87'] / (p['k_i'] * 1e6)) + (
                    ((S_abs * 1e6) ** 2 - (c['P_pr_87'] * 1e6) ** 2) / (2.0 * c['p0_87'] * E_Pa * c['F']))) * 1000.0
    else:
        c['l2_87'] = 0.0
        c['u_end'] = (S_abs * 1e6 * c['beta_87'] / (math.pi * D_H_m * (p['k_i'] * 1e6))) * 1000.0

    return c


def auto_select_thickness(p):
    """Автоподбор минимальной толщины из сортамента, выполняющей условия 8.1 и 8.2"""
    temp_p = p.copy()
    for t in SORTAMENT:
        temp_p['delta_n'] = t
        res = calculate_all(temp_p)
        if res['ok_81'] and res['ok_82']:
            return t
    return SORTAMENT[-1]


# --- ВСТРОЕННЫЙ ГЕНЕРАТОР ВЕКТОРНЫХ ГРАФИКОВ SVG (НЕ ТРЕБУЕТ MATPLOTLIB) ---
def svg_line_epure(x_vals, y_vals, x_bound, title, x_label, y_label):
    W, H = 760, 300
    ml, mr, mt, mb = 65, 25, 35, 45
    pw, ph = W - ml - mr, H - mt - mb
    xmax = max(max(x_vals), 1e-6)
    ymax = max(max(y_vals) * 1.08, 1e-6)

    def sx(x):
        return ml + (x / xmax) * pw

    def sy(y):
        return mt + ph - (y / ymax) * ph

    svg = [
        f"<div class='svg-chart'><svg viewBox='0 0 {W} {H}' width='100%' height='100%' xmlns='http://www.w3.org/2000/svg' style='font-family: sans-serif;'>"]
    svg.append(
        f"<text x='{W / 2}' y='22' text-anchor='middle' font-size='15' font-weight='bold' fill='#222'>{title}</text>")

    # Сетка и подписи по Y
    for i in range(6):
        yv = ymax * i / 5.0
        py = sy(yv)
        svg.append(f"<line x1='{ml}' y1='{py:.1f}' x2='{W - mr}' y2='{py:.1f}' stroke='#eee' stroke-width='1'/>")
        svg.append(f"<text x='{ml - 8}' y='{py + 4:.1f}' text-anchor='end' font-size='11' fill='#555'>{fmt(yv)}</text>")

    # Сетка и подписи по X
    for i in range(7):
        xv = xmax * i / 6.0
        px = sx(xv)
        svg.append(f"<line x1='{px:.1f}' y1='{mt}' x2='{px:.1f}' y2='{mt + ph}' stroke='#eee' stroke-width='1'/>")
        svg.append(
            f"<text x='{px:.1f}' y='{mt + ph + 18}' text-anchor='middle' font-size='11' fill='#555'>{fmt(xv)}</text>")

    # Оси
    svg.append(f"<line x1='{ml}' y1='{mt}' x2='{ml}' y2='{mt + ph}' stroke='#333' stroke-width='1.2'/>")
    svg.append(f"<line x1='{ml}' y1='{mt + ph}' x2='{W - mr}' y2='{mt + ph}' stroke='#333' stroke-width='1.2'/>")
    svg.append(f"<text x='{ml + pw / 2}' y='{H - 6}' text-anchor='middle' font-size='12' fill='#222'>{x_label}</text>")
    svg.append(
        f"<text x='16' y='{mt + ph / 2}' text-anchor='middle' font-size='12' fill='#222' transform='rotate(-90 16,{mt + ph / 2})'>{y_label}</text>")

    # Граница упругой зоны
    if 0 < x_bound <= xmax:
        bx = sx(x_bound)
        svg.append(
            f"<line x1='{bx:.1f}' y1='{mt}' x2='{bx:.1f}' y2='{mt + ph}' stroke='#d9822b' stroke-width='1.8' stroke-dasharray='5,5'/>")

    # Линия графика
    pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(x_vals, y_vals))
    svg.append(f"<polyline fill='none' stroke='#166587' stroke-width='2.5' points='{pts}'/>")

    # Легенда
    lx, ly = ml + 12, mt + 10
    svg.append(
        f"<rect x='{lx}' y='{ly}' width='195' height='42' fill='white' fill-opacity='0.9' stroke='#ccc' rx='4'/>")
    svg.append(
        f"<line x1='{lx + 8}' y1='{ly + 13}' x2='{lx + 28}' y2='{ly + 13}' stroke='#166587' stroke-width='2.5'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 17}' font-size='11' fill='#333'>Текущий проект</text>")
    svg.append(
        f"<line x1='{lx + 8}' y1='{ly + 30}' x2='{lx + 28}' y2='{ly + 30}' stroke='#d9822b' stroke-width='1.8' stroke-dasharray='4,4'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 34}' font-size='11' fill='#333'>Граница упругой зоны</text>")

    svg.append("</svg></div>")
    st.markdown("".join(svg), unsafe_allow_html=True)


def svg_bar_forces(c):
    W, H = 760, 320
    ml, mr, mt, mb = 65, 25, 35, 55
    pw, ph = W - ml - mr, H - mt - mb
    categories = [
        ("Прямой", "пластичная связь", c['N_kr_pl'], c['allow_83_pl']),
        ("Прямой", "упругая связь", c['N_kr_up'], c['allow_83_up']),
        ("Изогнутый", "меньшая оценка", c['N_kr_min'], c['allow_83_min']),
        ("Насыпь", "", c['N_kr_84'], c['allow_84'])
    ]
    ymax = max([max(x[2], x[3]) for x in categories] + [abs(c['S'])]) * 1.12
    ymax = max(ymax, 1.0)

    def sy(y):
        return mt + ph - (y / ymax) * ph

    svg = [
        f"<div class='svg-chart'><svg viewBox='0 0 {W} {H}' width='100%' height='100%' xmlns='http://www.w3.org/2000/svg' style='font-family: sans-serif;'>"]
    svg.append(
        f"<text x='{W / 2}' y='22' text-anchor='middle' font-size='15' font-weight='bold' fill='#222'>Расчётное и критические продольные усилия</text>")

    for i in range(6):
        yv = ymax * i / 5.0
        py = sy(yv)
        svg.append(f"<line x1='{ml}' y1='{py:.1f}' x2='{W - mr}' y2='{py:.1f}' stroke='#eee' stroke-width='1'/>")
        svg.append(f"<text x='{ml - 8}' y='{py + 4:.1f}' text-anchor='end' font-size='11' fill='#555'>{fmt(yv)}</text>")

    svg.append(f"<line x1='{ml}' y1='{mt}' x2='{ml}' y2='{mt + ph}' stroke='#333' stroke-width='1.2'/>")
    svg.append(f"<line x1='{ml}' y1='{mt + ph}' x2='{W - mr}' y2='{mt + ph}' stroke='#333' stroke-width='1.2'/>")
    svg.append(
        f"<text x='16' y='{mt + ph / 2}' text-anchor='middle' font-size='12' fill='#222' transform='rotate(-90 16,{mt + ph / 2})'>Усилие, МН</text>")

    step = pw / len(categories)
    bw = 38
    for idx, (l1, l2, nkr, allow) in enumerate(categories):
        cx = ml + step * (idx + 0.5)
        y1 = sy(nkr)
        y2 = sy(allow)
        svg.append(
            f"<rect x='{cx - bw - 2:.1f}' y='{y1:.1f}' width='{bw}' height='{mt + ph - y1:.1f}' fill='#9cb4c9'/>")
        svg.append(f"<rect x='{cx + 2:.1f}' y='{y2:.1f}' width='{bw}' height='{mt + ph - y2:.1f}' fill='#1b698c'/>")
        svg.append(f"<text x='{cx:.1f}' y='{mt + ph + 18}' text-anchor='middle' font-size='11' fill='#222'>{l1}</text>")
        if l2:
            svg.append(
                f"<text x='{cx:.1f}' y='{mt + ph + 32}' text-anchor='middle' font-size='11' fill='#222'>{l2}</text>")

    # Линия Sсж
    ys = sy(abs(c['S']))
    svg.append(f"<line x1='{ml}' y1='{ys:.1f}' x2='{W - mr}' y2='{ys:.1f}' stroke='#c0392b' stroke-width='2'/>")

    # Легенда
    lx, ly = W - mr - 210, mt + 8
    svg.append(
        f"<rect x='{lx}' y='{ly}' width='200' height='58' fill='white' fill-opacity='0.9' stroke='#ccc' rx='4'/>")
    svg.append(f"<line x1='{lx + 8}' y1='{ly + 13}' x2='{lx + 28}' y2='{ly + 13}' stroke='#c0392b' stroke-width='2'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 17}' font-size='11' fill='#333'>Расчётное Sсж ({fmt(c['S'])} МН)</text>")
    svg.append(f"<rect x='{lx + 8}' y='{ly + 24}' width='20' height='9' fill='#9cb4c9'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 32}' font-size='11' fill='#333'>Nкр</text>")
    svg.append(f"<rect x='{lx + 8}' y='{ly + 40}' width='20' height='9' fill='#1b698c'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 48}' font-size='11' fill='#333'>Допустимое (m/1,1) Nкр</text>")

    svg.append("</svg></div>")
    st.markdown("".join(svg), unsafe_allow_html=True)


def svg_vert_radii(p, c):
    W, H = 760, 320
    ml, mr, mt, mb = 65, 25, 35, 45
    pw, ph = W - ml - mr, H - mt - mb

    alphas = np.linspace(5, 175, 90)
    r1_list, r2_list, rmax_list = [], [], []
    S_N = abs(c['S']) * 1e6
    qv = max(c['q_v_83'], 1.0)
    for a in alphas:
        rad_a2 = math.radians(a / 2.0)
        rad_a4 = math.radians(a / 4.0)
        # По 4.25: при заданном угле отношение lкр/f = 2 sin(a/2) / (2 sin^2(a/4))
        sin_a2 = max(math.sin(rad_a2), 1e-6)
        sin2_a4 = max(math.sin(rad_a4) ** 2, 1e-6)
        ratio_lf = sin_a2 / sin2_a4
        r_425 = (2.0 * p['k_np'] * S_N) / (qv * 2.0 * sin_a2 * math.sqrt(1.0 + (ratio_lf ** 2) / 16.0))
        k_a = 1.0 if a <= 45.0 else math.sqrt(math.sin(rad_a2) ** 2 + math.cos(rad_a2) ** 4)
        r_426 = (p['k_np'] * S_N) / (qv * k_a)
        r1_list.append(r_425)
        r2_list.append(r_426)
        rmax_list.append(max(r_425, r_426))

    xmax = 180.0
    ymax = max(max(rmax_list), p['rho_v']) * 1.15
    ymax = max(ymax, 100.0)

    def sx(x):
        return ml + (x / xmax) * pw

    def sy(y):
        return mt + ph - min(max(y / ymax, 0.0), 1.0) * ph

    svg = [
        f"<div class='svg-chart'><svg viewBox='0 0 {W} {H}' width='100%' height='100%' xmlns='http://www.w3.org/2000/svg' style='font-family: sans-serif;'>"]
    svg.append(
        f"<text x='{W / 2}' y='22' text-anchor='middle' font-size='15' font-weight='bold' fill='#222'>Допустимые радиусы вертикального поворота</text>")

    for i in range(6):
        yv = ymax * i / 5.0
        py = sy(yv)
        svg.append(f"<line x1='{ml}' y1='{py:.1f}' x2='{W - mr}' y2='{py:.1f}' stroke='#eee' stroke-width='1'/>")
        svg.append(f"<text x='{ml - 8}' y='{py + 4:.1f}' text-anchor='end' font-size='11' fill='#555'>{fmt(yv)}</text>")

    for a_tick in [0, 25, 50, 75, 100, 125, 150, 175]:
        px = sx(a_tick)
        svg.append(f"<line x1='{px:.1f}' y1='{mt}' x2='{px:.1f}' y2='{mt + ph}' stroke='#eee' stroke-width='1'/>")
        svg.append(
            f"<text x='{px:.1f}' y='{mt + ph + 18}' text-anchor='middle' font-size='11' fill='#555'>{a_tick}</text>")

    # Зона допустимых радиусов (заливка выше кривой максимума)
    poly_pts = [f"{sx(alphas[0]):.1f},{mt}"] + [f"{sx(a):.1f},{sy(r):.1f}" for a, r in zip(alphas, rmax_list)] + [
        f"{sx(alphas[-1]):.1f},{mt}"]
    svg.append(f"<polygon points='{' '.join(poly_pts)}' fill='#d4efdf' fill-opacity='0.45'/>")

    pts1 = " ".join(f"{sx(a):.1f},{sy(r):.1f}" for a, r in zip(alphas, r1_list))
    pts2 = " ".join(f"{sx(a):.1f},{sy(r):.1f}" for a, r in zip(alphas, r2_list))
    pts_m = " ".join(f"{sx(a):.1f},{sy(r):.1f}" for a, r in zip(alphas, rmax_list))

    svg.append(f"<polyline fill='none' stroke='#85929e' stroke-width='1.8' stroke-dasharray='5,4' points='{pts1}'/>")
    svg.append(f"<polyline fill='none' stroke='#d9822b' stroke-width='1.8' stroke-dasharray='3,3' points='{pts2}'/>")
    svg.append(f"<polyline fill='none' stroke='#166587' stroke-width='2.5' points='{pts_m}'/>")

    # Точка текущего поворота
    cx, cy = sx(p['alpha_v']), sy(p['rho_v'])
    svg.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='5.5' fill='#1b5e20' stroke='#fff' stroke-width='1.5'/>")

    svg.append(f"<line x1='{ml}' y1='{mt}' x2='{ml}' y2='{mt + ph}' stroke='#333' stroke-width='1.2'/>")
    svg.append(f"<line x1='{ml}' y1='{mt + ph}' x2='{W - mr}' y2='{mt + ph}' stroke='#333' stroke-width='1.2'/>")
    svg.append(
        f"<text x='{ml + pw / 2}' y='{H - 6}' text-anchor='middle' font-size='12' fill='#222'>Угол αв, град</text>")
    svg.append(
        f"<text x='16' y='{mt + ph / 2}' text-anchor='middle' font-size='12' fill='#222' transform='rotate(-90 16,{mt + ph / 2})'>Минимальный радиус, м</text>")

    # Легенда
    lx, ly = W - mr - 195, mt + ph - 82
    svg.append(
        f"<rect x='{lx}' y='{ly}' width='185' height='74' fill='white' fill-opacity='0.92' stroke='#ccc' rx='4'/>")
    svg.append(
        f"<line x1='{lx + 8}' y1='{ly + 13}' x2='{lx + 28}' y2='{ly + 13}' stroke='#85929e' stroke-width='1.8' stroke-dasharray='4,3'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 17}' font-size='11' fill='#333'>По условию 4.25</text>")
    svg.append(
        f"<line x1='{lx + 8}' y1='{ly + 29}' x2='{lx + 28}' y2='{ly + 29}' stroke='#d9822b' stroke-width='1.8' stroke-dasharray='3,3'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 33}' font-size='11' fill='#333'>По условию 4.26</text>")
    svg.append(
        f"<line x1='{lx + 8}' y1='{ly + 45}' x2='{lx + 28}' y2='{ly + 45}' stroke='#166587' stroke-width='2.5'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 49}' font-size='11' fill='#333'>Оба условия</text>")
    svg.append(f"<circle cx='{lx + 18}' cy='{ly + 61}' r='4.5' fill='#1b5e20'/>")
    svg.append(f"<text x='{lx + 34}' y='{ly + 65}' font-size='11' fill='#333'>Текущий поворот</text>")

    svg.append("</svg></div>")
    st.markdown("".join(svg), unsafe_allow_html=True)


def render_all_charts(p, c):
    st.subheader("Графики и сравнение вариантов")
    st.markdown(
        "<div class='info-text'>Эпюры — дополнительная расчётная схема раздела 5 (формулы 5.4–5.19). "
        "x отсчитывается от условно неподвижного сечения к свободному концу. Показаны модули усилий и перемещений. "
        f"Длина упругой зоны l₁ = 3,5/β = {fmt(c['l1_87'])} м; длина зоны скольжения l₂ = {fmt(c['l2_87'])} м.</div>",
        unsafe_allow_html=True
    )

    l1 = c['l1_87']
    l2 = c['l2_87']
    L_tot = max(l1 + l2, 10.0)
    xs = np.linspace(0.0, L_tot, 200)
    P_list, u_list, tau_list = [], [], []
    E_Pa = p['E'] * 1e6
    ki_Pa = p['k_i'] * 1e6
    S_abs = abs(c['S'])
    sh_35 = math.sinh(3.5)

    for x in xs:
        if S_abs > c['P_pr_87']:
            if x <= l1:
                ratio_sh = math.sinh(c['beta_87'] * x) / sh_35
                tx = c['tau_pr_87'] * ratio_sh
                Px = c['P_pr_87'] * ratio_sh
                ux = (tx / ki_Pa) * 1000.0
            else:
                dx = x - l1
                tx = c['tau_pr_87']
                Px = c['P_pr_87'] + (c['p0_87'] * dx) / 1e6
                ux = ((c['tau_pr_87'] / ki_Pa) + (c['P_pr_87'] * 1e6 * dx + 0.5 * c['p0_87'] * (dx ** 2)) / (
                            E_Pa * c['F'])) * 1000.0
        else:
            ratio_sh = math.sinh(c['beta_87'] * x) / sh_35 if l1 > 0 else 0.0
            Px = S_abs * ratio_sh
            tx = (S_abs * c['P_pr_87'] > 0 and (S_abs / c['P_pr_87']) * c['tau_pr_87'] * ratio_sh) or 0.0
            ux = (tx / ki_Pa) * 1000.0

        P_list.append(Px)
        u_list.append(ux)
        tau_list.append(tx / 1000.0)

    svg_line_epure(xs, P_list, l1, "Продольное усилие по длине", "x, м", "P(x), МН")
    svg_line_epure(xs, u_list, l1, "Продольные перемещения по длине", "x, м", "u(x), мм")
    svg_line_epure(xs, tau_list, l1, "Касательные напряжения по длине", "x, м", "τ(x), кПа")
    svg_bar_forces(c)
    svg_vert_radii(p, c)


# --- ФУНКЦИИ ОТРИСОВКИ ПОШАГОВЫХ РАСЧЕТОВ ПО МЕТОДИЧКЕ ---
def draw_step(num_title, latex_formula, sub_str, ans_str):
    st.markdown(f"<div class='step-box'><div class='step-title'>{num_title}</div>", unsafe_allow_html=True)
    st.latex(latex_formula)
    st.markdown(f"<div class='sub-line'>Подстановка: {sub_str}</div><div class='ans-line'>{ans_str}</div></div>",
                unsafe_allow_html=True)


def render_8_1(p, c):
    st.subheader("Расчёт 8.1. Требуемая толщина стенки")
    st.markdown(f"**Итог:** {'выполняется' if c['ok_81'] else 'не выполняется'}.")
    draw_step("1. Расчётное сопротивление [(3.3)]",
              r"R_1 = \frac{R_{1\text{н}} m}{k_1 k_{\text{н}}}; \quad R_2 = \frac{R_{2\text{н}} m}{k_2 k_{\text{н}}}",
              f"R₁ = {fmt(p['R1_n'])} × {fmt(p['m'])} / ({fmt(p['k1'])} × {fmt(p['k_H'])}); R₂ = {fmt(p['R2_n'])} × {fmt(p['m'])} / ({fmt(p['k2'])} × {fmt(p['k_H'])})",
              f"R₁ = {fmt(c['R1'])} МПа; R₂ = {fmt(c['R2'])} МПа")
    draw_step("2. Толщина по давлению [(3.5)]",
              r"\delta = \frac{n p D_{\text{н}}}{2(R_1 + n p)}",
              f"{fmt(p['n_p'])} × {fmt(p['P'])} × {fmt(p['D_H'])} / [2 × ({fmt(c['R1'])} + {fmt(p['n_p'])} × {fmt(p['P'])})]",
              f"δ = {fmt(c['delta_p'])} мм")
    draw_step("3. Минимум по конструктивным условиям [стр. 38–39, 96–97]",
              r"\delta_{\min} = \max(D_{\text{н}}/100;\; 4\text{ мм};\; 12\text{ мм при } D_{\text{н}} \ge 1000\text{ мм})",
              f"max({fmt(p['D_H'] / 100.0)}; 4; {fmt(c['d_min_1000'])})",
              f"δmin = {fmt(c['delta_min'])} мм")
    draw_step("4. Требуемая толщина [8.1]",
              r"\delta_{\text{треб}} = \max(\delta;\; \delta_{\min})",
              f"max({fmt(c['delta_p'])}; {fmt(c['delta_min'])})",
              f"δтреб = {fmt(c['delta_treb'])} мм")
    draw_step("5. Рекомендация из сортамента [8.1]",
              r"\delta_{\text{сорт}} = \min\{\delta_i \text{ из сортамента} : \delta_i \ge \delta_{\text{треб}}\}",
              f"требование {fmt(c['delta_treb'])} мм",
              f"δсорт = {fmt(c['delta_sort'])} мм")
    draw_step("6. Холодный температурный перепад [8.1]",
              r"\Delta t^x = t_{\text{э}} - t^x",
              f"{fmt(p['t_product'])} − ({fmt(p['t_x'])})",
              f"Δtˣ = {fmt(c['dt_x'])} °C")
    draw_step("7. Тёплый температурный перепад [8.1]",
              r"\Delta t^m = t_{\text{э}} - t^m",
              f"{fmt(p['t_product'])} − ({fmt(p['t_m'])})",
              f"Δtᵐ = {fmt(c['dt_m'])} °C")
    draw_step("8. Внутренний диаметр принятой трубы [8.2]",
              r"D_{\text{вн}} = D_{\text{н}} - 2\delta_{\text{н}}",
              f"{fmt(p['D_H'])} − 2 × {fmt(p['delta_n'])}",
              f"Dвн = {fmt(c['D_vn'])} мм")

    st.markdown("**Проверяемые условия (8.1)**")
    st.table(pd.DataFrame({
        "Условие": ["Принятая толщина δн ≥ δтреб"],
        "Подстановка и итог": [
            f"{fmt(p['delta_n'])} ≥ {fmt(c['delta_treb'])} мм — {'выполняется' if c['ok_81'] else 'не выполняется'}"]
    }))
    st.markdown("**Таблица результатов (8.1)**")
    st.table(pd.DataFrame({
        "Величина": ["Расчётное сопротивление R₁", "Расчётное сопротивление R₂", "Толщина по давлению",
                     "Минимум по конструктивным условиям", "Требуемая толщина", "Рекомендация из сортамента",
                     "Холодный темп. перепад", "Тёплый темп. перепад", "Внутренний диаметр"],
        "Обозначение": ["R₁", "R₂", "δ", "δmin", "δтреб", "δсорт", "Δtˣ", "Δtᵐ", "Dвн"],
        "Результат": [fmt(c['R1']), fmt(c['R2']), fmt(c['delta_p']), fmt(c['delta_min']), fmt(c['delta_treb']),
                      fmt(c['delta_sort']), fmt(c['dt_x']), fmt(c['dt_m']), fmt(c['D_vn'])],
        "Единица": ["МПа", "МПа", "мм", "мм", "мм", "мм", "°C", "°C", "мм"]
    }))


def render_8_2(p, c):
    st.subheader("Расчёт 8.2. Прочность по деформациям")
    st.markdown(f"**Итог:** {'выполняется' if c['ok_82'] else 'не выполняется'}.")
    draw_step("1. Нормативные кольцевые напряжения [(3.23)]",
              r"\sigma_{\text{кц}}^n = \frac{p D_{\text{вн}}}{2\delta_{\text{н}}}",
              f"{fmt(p['P'])} × {fmt(c['D_vn_m'])} / (2 × {fmt(c['delta_m'])})",
              f"σкцⁿ = {fmt(c['sig_kc_n'])} МПа")
    draw_step("2. Расчётные кольцевые напряжения [(2.12)]",
              r"\sigma_{\text{кц}} = n \sigma_{\text{кц}}^n",
              f"{fmt(p['n_p'])} × {fmt(c['sig_kc_n'])}",
              f"σкц = {fmt(c['sig_kc'])} МПа")
    draw_step("3. Осевые напряжения [(3.8)]",
              r"\sigma_{\text{пр}N} = -\alpha E \Delta t^x + \mu \sigma_{\text{кц}}",
              f"−{fmt(p['alpha'])} × {fmt(p['E'])} × {fmt(c['dt_x'])} + {fmt(p['mu'])} × {fmt(c['sig_kc'])}",
              f"σпрN = {fmt(c['sig_pr_N'])} МПа")
    draw_step("4. Нормированное сопротивление [(3.20), (3.21)]",
              r"R_{2\text{д}} = \frac{m R_{2\text{н}}}{0.9 k_{\text{н}}}",
              f"{fmt(p['m'])} × {fmt(p['R2_n'])} / (0,9 × {fmt(p['k_H'])})",
              f"R₂д = {fmt(c['R2_d'])} МПа")
    draw_step("5. Коэффициент при сжатии [(3.22); при растяжении ψ₁ = 1]",
              r"\psi_1 = \sqrt{1 - 0.75(\sigma_{\text{кц}}^n / R_{2\text{д}})^2} - 0.5 \frac{\sigma_{\text{кц}}^n}{R_{2\text{д}}}",
              f"√[1 − 0,75 × ({fmt(c['sig_kc_n'])} / {fmt(c['R2_d'])})²] − 0,5 × {fmt(c['sig_kc_n'])} / {fmt(c['R2_d'])}",
              f"ψ₁ = {fmt(c['psi_1'])} —")
    draw_step("6. Продольные напряжения, холодное замыкание [(3.24)]",
              r"\sigma_{\text{пр}}^n = \mu \sigma_{\text{кц}}^n - \alpha E \Delta t^x \pm \frac{E D_{\text{н}}}{2\rho}; \quad \text{оба края сечения}",
              f"{fmt(p['mu'])} × {fmt(c['sig_kc_n'])} − {fmt(p['alpha'])} × {fmt(p['E'])} × ({fmt(c['dt_x'])}) ± {fmt(c['bend_stress'])}; диапазон [{fmt(c['sig_pr_x_minus'])}; {fmt(c['sig_pr_x_plus'])}]",
              f"σпрˣ = {fmt(c['sig_pr_x'])} МПа")
    draw_step("7. Продольные напряжения, тёплое замыкание [(3.24)]",
              r"\sigma_{\text{пр}}^n = \mu \sigma_{\text{кц}}^n - \alpha E \Delta t^m \pm \frac{E D_{\text{н}}}{2\rho}; \quad \text{оба края сечения}",
              f"{fmt(p['mu'])} × {fmt(c['sig_kc_n'])} − {fmt(p['alpha'])} × {fmt(p['E'])} × ({fmt(c['dt_m'])}) ± {fmt(c['bend_stress'])}; диапазон [{fmt(c['sig_pr_m_minus'])}; {fmt(c['sig_pr_m_plus'])}]",
              f"σпрᵐ = {fmt(c['sig_pr_m'])} МПа")

    st.markdown("**Проверяемые условия (8.2)**")
    st.table(pd.DataFrame({
        "Условие": [
            "Кольцевое направление σкцⁿ ≤ R₂д",
            "Холодное замыкание, край − |σпрⁿ| ≤ ψ₁ R₂д (ψ₁ = 1 при σпрⁿ ≥ 0)",
            "Холодное замыкание, край + |σпрⁿ| ≤ ψ₁ R₂д (ψ₁ = 1 при σпрⁿ ≥ 0)",
            "Тёплое замыкание, край − |σпрⁿ| ≤ ψ₁ R₂д (ψ₁ = 1 при σпрⁿ ≥ 0)",
            "Тёплое замыкание, край + |σпрⁿ| ≤ ψ₁ R₂д (ψ₁ = 1 при σпрⁿ ≥ 0)"
        ],
        "Подстановка и итог": [
            f"{fmt(c['sig_kc_n'])} ≤ {fmt(c['R2_d'])} МПа — {'выполняется' if c['ok_82_kc'] else 'не выполняется'}",
            f"{fmt(abs(c['sig_pr_x_minus']))} ≤ {fmt(c['allow_x_minus'])} МПа — {'выполняется' if c['ok_82_xm'] else 'не выполняется'}",
            f"{fmt(abs(c['sig_pr_x_plus']))} ≤ {fmt(c['allow_x_plus'])} МПа — {'выполняется' if c['ok_82_xp'] else 'не выполняется'}",
            f"{fmt(abs(c['sig_pr_m_minus']))} ≤ {fmt(c['allow_m_minus'])} МПа — {'выполняется' if c['ok_82_mm'] else 'не выполняется'}",
            f"{fmt(abs(c['sig_pr_m_plus']))} ≤ {fmt(c['allow_m_plus'])} МПа — {'выполняется' if c['ok_82_mp'] else 'не выполняется'}"
        ]
    }))
    st.markdown("**Таблица результатов (8.2)**")
    st.table(pd.DataFrame({
        "Величина": ["Нормативные кольцевые напряжения", "Расчётные кольцевые напряжения", "Осевые напряжения",
                     "Нормированное сопротивление", "Коэффициент при сжатии",
                     "Продольные напряжения, холодное замыкание", "Продольные напряжения, тёплое замыкание"],
        "Обозначение": ["σкцⁿ", "σкц", "σпрN", "R₂д", "ψ₁", "σпрˣ", "σпрᵐ"],
        "Результат": [fmt(c['sig_kc_n']), fmt(c['sig_kc']), fmt(c['sig_pr_N']), fmt(c['R2_d']), fmt(c['psi_1']),
                      fmt(c['sig_pr_x']), fmt(c['sig_pr_m'])],
        "Единица": ["МПа", "МПа", "МПа", "МПа", "—", "МПа", "МПа"]
    }))


def render_8_3(p, c):
    st.subheader("Расчёт 8.3. Общая продольная устойчивость")
    st.markdown(f"**Итог:** {'выполняется' if c['ok_83'] else 'не выполняется'}.")
    draw_step("1. Площадь металла [8.3 п. 1]", r"F = \frac{\pi(D_{\text{н}}^2 - D_{\text{вн}}^2)}{4}",
              f"π({fmt(c['D_H_m'])}² − {fmt(c['D_vn_m'])}²) / 4", f"F = {fmt(c['F'])} м²")
    draw_step("2. Момент инерции [8.3 п. 3]", r"I = \frac{\pi(D_{\text{н}}^4 - D_{\text{вн}}^4)}{64}",
              f"π({fmt(c['D_H_m'])}⁴ − {fmt(c['D_vn_m'])}⁴) / 64", f"I = {fmt(c['I'])} м⁴")
    draw_step("3. Нормативный вес металла [8.3 п. 4]", r"q_{\text{м}}^n = \gamma_{\text{м}} F",
              f"{fmt(p['gamma_m'] * 1000)} × {fmt(c['F'])}", f"qмⁿ = {fmt(c['q_m_n'])} Н/м")
    draw_step("4. Нормативный вес изоляции [8.3 п. 5]",
              r"q_{\text{из}}^n = \rho_{\text{из}} g \frac{\pi(D_{\text{н.и}}^2 - D_{\text{н}}^2)}{4}",
              f"{fmt(p['rho_ins'])} × 9,81 × π({fmt(c['D_ins_m'])}² − {fmt(c['D_H_m'])}²) / 4",
              f"qизⁿ = {fmt(c['q_iz_n'])} Н/м")
    draw_step("5. Нормативный вес продукта [(2.16), (2.17)]",
              r"q_{\text{пр}}^n = \rho_{\text{пр}} g \frac{\pi D_{\text{вн}}^2}{4}",
              f"{fmt(p['rho_prod'] if p['product_type'] == 'Нефть' else 0.8)} × 9,81 × π × {fmt(c['D_vn_m'])}² / 4",
              f"qпрⁿ = {fmt(c['q_pr_n'])} Н/м")
    draw_step("6. Расчётный погонный вес [(4.7)]",
              r"q_{\text{тр}} = n_{\text{с.в}}(q_{\text{м}}^n + q_{\text{из}}^n) + n_{\text{пр}} q_{\text{пр}}^n",
              f"{fmt(p['n_sv'])} × ({fmt(c['q_m_n'])} + {fmt(c['q_iz_n'])}) + {fmt(p['n_pr'])} × {fmt(c['q_pr_n'])}",
              f"qтр = {fmt(c['q_tr'])} Н/м")
    draw_step("7. Кольцевое расчётное напряжение [(2.12)]",
              r"\sigma_{\text{кц}} = \frac{n p D_{\text{вн}}}{2\delta_{\text{н}}}",
              f"{fmt(p['n_p'])} × {fmt(p['P'])} × {fmt(c['D_vn_m'])} / (2 × {fmt(c['delta_m'])})",
              f"σкц = {fmt(c['sig_kc'])} МПа")
    draw_step("8. Эквивалентное продольное усилие [(4.2)]",
              r"S = [(0.5 - \mu)\sigma_{\text{кц}} + \alpha E \Delta t^x] F",
              f"[(0,5 − {fmt(p['mu'])}) × {fmt(c['sig_kc'])} + {fmt(p['alpha'])} × {fmt(p['E'])} × {fmt(c['dt_x'])}] × {fmt(c['F'])}",
              f"S = {fmt(c['S'])} МН")
    draw_step("9. Среднее давление грунта [(4.6), с диаметром контакта Dн.и]",
              r"p_{\text{гр}} = \frac{2 n_{\text{гр}} \gamma_{\text{гр}} D_{\text{н.и}}((h_0 + D_{\text{н.и}}/8) + (h_0 + D_{\text{н.и}}/2)\tan^2(45^\circ - \varphi_{\text{гр}}/2)) + q_{\text{тр}}}{\pi D_{\text{н.и}}}",
              f"[2 × {fmt(p['n_gr'])} × {fmt(c['gamma_gr_N'])} × {fmt(c['D_ins_m'])} × (({fmt(p['h0'])} + {fmt(c['D_ins_m'])}/8) + ({fmt(p['h0'])} + {fmt(c['D_ins_m'])}/2) × {fmt(c['tan2_45_phi'])}) + {fmt(c['q_tr'])}] / (π × {fmt(c['D_ins_m'])})",
              f"pгр = {fmt(c['p_gr_83'])} Па")
    draw_step("10. Предельное касательное напряжение [(4.5)]",
              r"\tau_{\text{пр}} = p_{\text{гр}}\tan\varphi_{\text{гр}} + c_{\text{гр}}",
              f"{fmt(c['p_gr_83'])} × tg {fmt(p['phi_deg'])}° + {fmt(p['c_gr'])}",
              f"τпр = {fmt(c['tau_pr_83'] / 1000.0)} кПа ({fmt(c['tau_pr_83'])} Па)")
    draw_step("11. Продольное сопротивление грунта [(4.4)]", r"p_0 = \pi D_{\text{н.и}}\tau_{\text{пр}}",
              f"π × {fmt(c['D_ins_m'])} × {fmt(c['tau_pr_83'])}", f"p₀ = {fmt(c['p0_83'])} Н/м")
    draw_step("12. Сопротивление подъёму [(4.8)]",
              r"q_{\text{в}} = n_{\text{гр}}\gamma_{\text{гр}}D_{\text{н.и}}(h_0 + D_{\text{н.и}}/2 - \pi D_{\text{н.и}}/8) + q_{\text{тр}}",
              f"{fmt(p['n_gr'])} × {fmt(c['gamma_gr_N'])} × {fmt(c['D_ins_m'])} × ({fmt(p['h0'])} + {fmt(c['D_ins_m'])}/2 − π × {fmt(c['D_ins_m'])}/8) + {fmt(c['q_tr'])}",
              f"qв = {fmt(c['q_v_83'])} Н/м")
    draw_step("13. Прямой участок, пластичная связь [(4.3)]",
              r"N_{\text{кр.пл}} = 4.09 (p_0^2 q_{\text{в}}^4 F^2 E^5 I^3)^{1/11}",
              f"4,09 × ({fmt(c['p0_83'])}² × {fmt(c['q_v_83'])}⁴ × {fmt(c['F'])}² × {fmt(p['E'] * 1e6)}⁵ × {fmt(c['I'])}³)^(1/11) / 10⁶",
              f"Nкр.пл = {fmt(c['N_kr_pl'])} МН")
    draw_step("14. Прямой участок, упругая связь [(4.32)]", r"N_{\text{кр.уп}} = 2\sqrt{k_0 D_{\text{н}} E I}",
              f"2 × √({fmt(p['k_0'] * 1e6)} × {fmt(c['D_H_m'])} × {fmt(p['E'] * 1e6)} × {fmt(c['I'])}) / 10⁶",
              f"Nкр.уп = {fmt(c['N_kr_up'])} МН")
    draw_step("15. Длина волны выпучивания [(4.33)]", r"\lambda = 2\pi \left(\frac{E I}{k_0 D_{\text{н}}}\right)^{1/4}",
              f"2π × ({fmt(p['E'] * 1e6)} × {fmt(c['I'])} / ({fmt(p['k_0'] * 1e6)} × {fmt(c['D_H_m'])}))^(1/4)",
              f"λ = {fmt(c['lam'])} м")
    draw_step("16. Параметр номограммы [(4.11)]", r"\theta = \frac{1}{\rho (q_{\text{в}} / (E I))^{1/3}}",
              f"1 / [{fmt(p['rho_izg'])} × ({fmt(c['q_v_83'])} / ({fmt(p['E'] * 1e6)} × {fmt(c['I'])}))^(1/3)]",
              f"θ = {fmt(c['theta'])} —")
    draw_step("17. Параметр номограммы [(4.12)]",
              r"Z = \frac{\sqrt{p_0 F / (q_{\text{в}} I)}}{(q_{\text{в}} / (E I))^{1/3}}",
              f"√[{fmt(c['p0_83'])} × {fmt(c['F'])} / ({fmt(c['q_v_83'])} × {fmt(c['I'])})] / ({fmt(c['q_v_83'])} / ({fmt(p['E'] * 1e6)} × {fmt(c['I'])}))^(1/3)",
              f"Z = {fmt(c['Z'])} —")
    draw_step("18. Изогнутый участок, номограмма [(4.9)]", r"N_{\text{кр.ном}} = \beta (q_{\text{в}}^2 E I)^{1/3}",
              f"{fmt(p['beta_nom'])} × ({fmt(c['q_v_83'])}² × {fmt(p['E'] * 1e6)} × {fmt(c['I'])})^(1/3) / 10⁶",
              f"Nкр.ном = {fmt(c['N_kr_nom'])} МН")
    draw_step("19. Изогнутый участок, вторая оценка [(4.10)]", r"N_{\text{кр.изг}} = 0.375 q_{\text{в}} \rho",
              f"0,375 × {fmt(c['q_v_83'])} × {fmt(p['rho_izg'])} / 10⁶", f"Nкр.изг = {fmt(c['N_kr_izg'])} МН")
    draw_step("20. Принятое усилие для изгиба [стр. 67]",
              r"N_{\text{кр.min}} = \min(N_{\text{кр.ном}};\; N_{\text{кр.изг}})",
              f"min({fmt(c['N_kr_nom'])}; {fmt(c['N_kr_izg'])})", f"Nкр.min = {fmt(c['N_kr_min'])} МН")
    draw_step("21. Минимальный радиус по второй оценке [(4.1), (4.10)]",
              r"\rho_{\text{треб}} = \frac{1.1 S_{\text{сж}}}{m \times 0.375 q_{\text{в}}}",
              f"1,1 × {fmt(c['S'] * 1e6)} / ({fmt(p['m'])} × 0,375 × {fmt(c['q_v_83'])})",
              f"ρтреб = {fmt(c['rho_treb'])} м")
    draw_step("22. Дополнительный сценарий ρ = 1400 м [8.3 п. 20]",
              r"N_{\text{кр.1400}} = 0.375 q_{\text{в}} \times 1400",
              f"0,375 × {fmt(c['q_v_83'])} × 1400 / 10⁶", f"Nкр.1400 = {fmt(c['N_kr_1400'])} МН")

    st.markdown("**Проверяемые условия (8.3)**")
    st.table(pd.DataFrame({
        "Условие": [
            "Прямой, пластичная связь Sсж ≤ (m/1,1) Nкр.пл",
            "Прямой, упругая связь Sсж ≤ (m/1,1) Nкр.уп",
            "Изогнутый, меньшая оценка Sсж ≤ (m/1,1) Nкр.min"
        ],
        "Подстановка и итог": [
            f"{fmt(c['S'])} ≤ {fmt(c['allow_83_pl'])} МН — {'выполняется' if c['ok_83_pl'] else 'не выполняется'}",
            f"{fmt(c['S'])} ≤ {fmt(c['allow_83_up'])} МН — {'выполняется' if c['ok_83_up'] else 'не выполняется'}",
            f"{fmt(c['S'])} ≤ {fmt(c['allow_83_min'])} МН — {'выполняется' if c['ok_83_izg'] else 'не выполняется'}"
        ]
    }))
    st.markdown("**Таблица результатов (8.3)**")
    st.table(pd.DataFrame({
        "Величина": ["Площадь металла", "Момент инерции", "Нормативный вес металла", "Нормативный вес изоляции",
                     "Нормативный вес продукта", "Расчётный погонный вес", "Кольцевое расчётное напряжение",
                     "Эквивалентное продольное усилие", "Среднее давление грунта", "Предельное касательное напряжение",
                     "Продольное сопротивление грунта", "Сопротивление подъёму", "Прямой участок, пластичная связь",
                     "Прямой участок, упругая связь", "Длина волны выпучивания", "Параметр номограммы θ",
                     "Параметр номограммы Z", "Изогнутый участок, номограмма", "Изогнутый участок, вторая оценка",
                     "Принятое усилие для изгиба", "Минимальный радиус", "Доп. сценарий ρ = 1400 м"],
        "Обозначение": ["F", "I", "qмⁿ", "qизⁿ", "qпрⁿ", "qтр", "σкц", "S", "pгр", "τпр", "p₀", "qв", "Nкр.пл",
                        "Nкр.уп", "λ", "θ", "Z", "Nкр.ном", "Nкр.изг", "Nкр.min", "ρтреб", "Nкр.1400"],
        "Результат": [fmt(c['F']), fmt(c['I']), fmt(c['q_m_n']), fmt(c['q_iz_n']), fmt(c['q_pr_n']), fmt(c['q_tr']),
                      fmt(c['sig_kc']), fmt(c['S']), fmt(c['p_gr_83']), fmt(c['tau_pr_83'] / 1000.0), fmt(c['p0_83']),
                      fmt(c['q_v_83']), fmt(c['N_kr_pl']), fmt(c['N_kr_up']), fmt(c['lam']), fmt(c['theta']),
                      fmt(c['Z']), fmt(c['N_kr_nom']), fmt(c['N_kr_izg']), fmt(c['N_kr_min']), fmt(c['rho_treb']),
                      fmt(c['N_kr_1400'])],
        "Единица": ["м²", "м⁴", "Н/м", "Н/м", "Н/м", "Н/м", "МПа", "МН", "Па", "кПа", "Н/м", "Н/м", "МН", "МН", "м",
                    "—", "—", "МН", "МН", "МН", "м", "МН"]
    }))


def render_8_4(p, c):
    st.subheader("Расчёт 8.4. Устойчивость в грунтовой насыпи")
    st.markdown(f"**Итог:** {'выполняется' if c['ok_84'] else 'не выполняется'}.")
    draw_step("1–8. Базовые характеристики сечения и усилия [из 8.3]",
              r"F = \frac{\pi(D_{\text{н}}^2 - D_{\text{вн}}^2)}{4}; \quad I = \frac{\pi(D_{\text{н}}^4 - D_{\text{вн}}^4)}{64}; \quad q_{\text{тр}}; \quad S",
              f"F = {fmt(c['F'])} м²; I = {fmt(c['I'])} м⁴; qтр = {fmt(c['q_tr'])} Н/м; σкц = {fmt(c['sig_kc'])} МПа",
              f"S = {fmt(c['S'])} МН")
    draw_step("9. Высота активной зоны [(4.17)]",
              r"h_2 = h_1 - (b + h_0 \cot \alpha_{\text{н}} - 0.5 h_1)\tan(45^\circ - \varphi_{\text{гр}}/2)",
              f"{fmt(p['h1'])} − ({fmt(p['b'])} + {fmt(p['h0'])} × {fmt(c['cot_aH'])} − 0,5 × {fmt(p['h1'])}) × {fmt(c['tan_45_phi2'])}",
              f"h₂ = {fmt(c['h2'])} м")
    draw_step("10. Давление на верхнюю образующую [(4.18)]",
              r"p_{\text{гр}} = \frac{n_{\text{гр}} \gamma_{\text{гр}} h_0 (b + 0.5 h_0 \cot \alpha_{\text{н}})}{b + h_0 \cot \alpha_{\text{н}}}",
              f"{fmt(p['n_gr'])} × {fmt(c['gamma_gr_N'])} × {fmt(p['h0'])} × ({fmt(p['b'])} + 0,5 × {fmt(p['h0'])} × {fmt(c['cot_aH'])}) / ({fmt(p['b'])} + {fmt(p['h0'])} × {fmt(c['cot_aH'])})",
              f"pгр = {fmt(c['p_gr_84'])} Па")
    draw_step("11. Пассивный отпор [(4.15)]",
              r"E_1 = n_{\text{гр}}\gamma_{\text{гр}}(h_1^2 - h_2^2)\frac{K_{\text{п}}}{2} + p_{\text{гр}}h_1 K_{\text{п}} + 2 n_{\text{гр}} c_{\text{гр}}(h_1 - h_2)\sqrt{K_{\text{п}}}; \quad K_{\text{п}} = \tan^2(45^\circ + \varphi_{\text{гр}}/2)",
              f"{fmt(p['n_gr'] * c['gamma_gr_N'] / 2.0)} × ({fmt(p['h1'])}² − {fmt(c['h2'])}²) × {fmt(c['Kp'])} + {fmt(c['p_gr_84'])} × {fmt(p['h1'])} × {fmt(c['Kp'])}",
              f"E₁ = {fmt(c['E1'])} Н/м")
    draw_step("12. Активный отпор, только при cгр = 0 [(4.20), стр. 68]",
              r"E_{\text{акт}} = n_{\text{гр}}\gamma_{\text{гр}}h_1^2 \frac{K_{\text{а}}}{2} + p_{\text{гр}}h_1 K_{\text{а}}; \quad K_{\text{а}} = \tan^2(45^\circ - \varphi_{\text{гр}}/2)",
              f"{fmt(p['n_gr'] * c['gamma_gr_N'] / 2.0)} × {fmt(p['h1'])}² × {fmt(c['Ka'])} + {fmt(c['p_gr_84'])} × {fmt(p['h1'])} × {fmt(c['Ka'])}",
              f"Eакт = {fmt(c['E_akt'])} Н/м")
    draw_step("13. Поперечное трение [(4.16)]",
              r"E_2 = q_{\text{тр}} \tan \varphi_{\text{гр}}",
              f"{fmt(c['q_tr'])} × tg {fmt(p['phi_deg'])}°",
              f"E₂ = {fmt(c['E2'])} Н/м")
    draw_step("14. Горизонтальное сопротивление [(4.14) с поправкой (4.20)]",
              r"q_{\text{гор}} = E_1 - E_{\text{акт}} + E_2",
              f"{fmt(c['E1'])} − {fmt(c['E_akt'])} + {fmt(c['E2'])}",
              f"qгор = {fmt(c['q_gor'])} Н/м")
    draw_step("15. Касательное напряжение [(4.5)]",
              r"\tau_{\text{пр}} = p_{\text{гр}} \tan \varphi_{\text{гр}} + c_{\text{гр}}",
              f"{fmt(c['p_gr_84'])} × tg {fmt(p['phi_deg'])}° + {fmt(p['c_gr'])}",
              f"τпр = {fmt(c['tau_pr_84'] / 1000.0)} кПа")
    draw_step("16. Продольное сопротивление [(4.4)]",
              r"p_0 = \pi D_{\text{н.и}} \tau_{\text{пр}}",
              f"π × {fmt(c['D_ins_m'])} × {fmt(c['tau_pr_84'])}",
              f"p₀ = {fmt(c['p0_84'])} Н/м")
    draw_step("17. Критическое усилие [(4.13)]",
              r"N_{\text{кр}} = 3.97 (p_0^2 q_{\text{гор}}^4 F^2 E^5 I^3)^{1/11}",
              f"3,97 × ({fmt(c['p0_84'])}² × {fmt(c['q_gor'])}⁴ × {fmt(c['F'])}² × {fmt(p['E'] * 1e6)}⁵ × {fmt(c['I'])}³)^(1/11) / 10⁶",
              f"Nкр = {fmt(c['N_kr_84'])} МН")

    st.markdown("**Проверяемые условия (8.4)**")
    st.table(pd.DataFrame({
        "Условие": [
            "Продольная устойчивость Sсж ≤ (m/1,1) Nкр",
            "Ширина насыпи 2b ≥ max(1,5 Dн; 1,5 м)",
            "Засыпка насыпи h₀ ≥ 0,8 м",
            "Откос насыпи αн ≤ 39°"
        ],
        "Подстановка и итог": [
            f"{fmt(c['S'])} ≤ {fmt(c['allow_84'])} МН — {'выполняется' if c['ok_84_ust'] else 'не выполняется'}",
            f"{fmt(2.0 * p['b'])} ≥ {fmt(c['min_2b'])} м — {'выполняется' if c['ok_84_2b'] else 'не выполняется'}",
            f"{fmt(p['h0'])} ≥ 0,8 м — {'выполняется' if c['ok_84_h0'] else 'не выполняется'}",
            f"{fmt(p['alpha_H'])} ≤ 39 град — {'выполняется' if c['ok_84_aH'] else 'не выполняется'}"
        ]
    }))
    st.markdown("**Таблица результатов (8.4)**")
    st.table(pd.DataFrame({
        "Величина": ["Площадь металла", "Момент инерции", "Расчётный погонный вес", "Эквивалентное продольное усилие",
                     "Высота активной зоны", "Давление на верхнюю образующую", "Пассивный отпор", "Активный отпор",
                     "Поперечное трение", "Горизонтальное сопротивление", "Касательное напряжение",
                     "Продольное сопротивление", "Критическое усилие"],
        "Обозначение": ["F", "I", "qтр", "S", "h₂", "pгр", "E₁", "Eакт", "E₂", "qгор", "τпр", "p₀", "Nкр"],
        "Результат": [fmt(c['F']), fmt(c['I']), fmt(c['q_tr']), fmt(c['S']), fmt(c['h2']), fmt(c['p_gr_84']),
                      fmt(c['E1']), fmt(c['E_akt']), fmt(c['E2']), fmt(c['q_gor']), fmt(c['tau_pr_84'] / 1000.0),
                      fmt(c['p0_84']), fmt(c['N_kr_84'])],
        "Единица": ["м²", "м⁴", "Н/м", "МН", "м", "Па", "Н/м", "Н/м", "Н/м", "Н/м", "кПа", "Н/м", "МН"]
    }))


def render_8_5(p, c):
    st.subheader("Расчёт 8.5. Устойчивость на горизонтальном повороте")
    st.markdown(f"**Итог:** {'выполняется' if c['ok_85'] else 'не выполняется'}.")
    draw_step("1–8. Базовые характеристики сечения и усилия [из 8.3]",
              r"F; \quad I; \quad q_{\text{тр}}; \quad \sigma_{\text{кц}}; \quad S",
              f"qтр = {fmt(c['q_tr'])} Н/м; σкц = {fmt(c['sig_kc'])} МПа",
              f"S = {fmt(c['S'])} МН")
    draw_step("9. Половина ширины насыпи понизу [(4.23)]",
              r"a = b + \frac{H}{\tan \alpha_{\text{н}}}",
              f"{fmt(p['b'])} + {fmt(p['H'])} / tg {fmt(p['alpha_H'])}°",
              f"a = {fmt(c['a_low'])} м")
    draw_step("10. Сопротивление сдвигу [(4.22)]",
              r"q_{\text{сдв}} = n_{\text{гр}}\gamma_{\text{гр}}\tan\varphi_{\text{гр}} H \frac{(2a - D_{\text{н.и}}) + (2b - D_{\text{н.и}})}{4} + f_{\text{тр}}[q_{\text{тр}} + n_{\text{гр}}\gamma_{\text{гр}}D_{\text{н.и}}(H - D_{\text{н.и}})] + n_{\text{гр}}c_{\text{гр}}\frac{2b - D_{\text{н.и}}}{2}",
              f"{fmt(p['n_gr'])} × {fmt(c['gamma_gr_N'])} × tg {fmt(p['phi_deg'])}° × {fmt(p['H'])} × [(2×{fmt(c['a_low'])} − {fmt(c['D_ins_m'])}) + (2×{fmt(p['b'])} − {fmt(c['D_ins_m'])})]/4 + {fmt(p['f_gr'])} × [{fmt(c['q_tr'])} + {fmt(p['n_gr'] * c['gamma_gr_N'])} × {fmt(c['D_ins_m'])} × ({fmt(p['H'])} − {fmt(c['D_ins_m'])})]",
              f"qсдв = {fmt(c['q_sdv'])} Н/м")
    draw_step("11. Требуемое сопротивление сдвигу [(4.21)]",
              r"q_{\text{сдв.треб}} = \frac{k_{\text{сдв}} S_{\text{сж}}}{\rho_{\text{гор}}}",
              f"{fmt(p['k_sdv'])} × {fmt(c['S'] * 1e6)} / {fmt(p['rho_gor'])}",
              f"qсдв.треб = {fmt(c['q_sdv_treb'])} Н/м")

    st.markdown("**Проверяемые условия (8.5)**")
    st.table(pd.DataFrame({
        "Условие": ["Устойчивость на сдвиг qсдв ≥ kсдв Sсж / ρгор"],
        "Подстановка и итог": [
            f"{fmt(c['q_sdv'])} ≥ {fmt(c['q_sdv_treb'])} Н/м — {'выполняется' if c['ok_85'] else 'не выполняется'}"]
    }))
    st.markdown("**Таблица результатов (8.5)**")
    st.table(pd.DataFrame({
        "Величина": ["Расчётный погонный вес", "Эквивалентное продольное усилие", "Половина ширины насыпи понизу",
                     "Сопротивление сдвигу", "Требуемое сопротивление сдвигу"],
        "Обозначение": ["qтр", "S", "a", "qсдв", "qсдв.треб"],
        "Результат": [fmt(c['q_tr']), fmt(c['S']), fmt(c['a_low']), fmt(c['q_sdv']), fmt(c['q_sdv_treb'])],
        "Единица": ["Н/м", "МН", "м", "Н/м", "Н/м"]
    }))


def render_8_6(p, c):
    st.subheader("Расчёт 8.6. Устойчивость на вертикальном повороте")
    st.markdown(f"**Итог:** {'выполняется' if c['ok_86'] else 'не выполняется'}.")
    draw_step("1–12. Базовые характеристики и сопротивление подъёму [из 8.3]",
              r"q_{\text{тр}}; \quad S; \quad q_{\text{в}} = n_{\text{гр}}\gamma_{\text{гр}}D_{\text{н.и}}(h_0 + D_{\text{н.и}}/2 - \pi D_{\text{н.и}}/8) + q_{\text{тр}}",
              f"S = {fmt(c['S'])} МН; p₀ = {fmt(c['p0_83'])} Н/м",
              f"qв = {fmt(c['q_v_83'])} Н/м")
    draw_step("13. Хорда вертикальной кривой [(4.28)]",
              r"l_{\text{кр}} = 2 \rho_{\text{в}} \sin(\alpha_{\text{в}}/2)",
              f"2 × {fmt(p['rho_v'])} × sin({fmt(p['alpha_v'])}° / 2)",
              f"lкр = {fmt(c['l_kr'])} м")
    draw_step("14. Стрела изгиба [(4.29)]",
              r"f = \rho_{\text{в}} - \sqrt{\rho_{\text{в}}^2 - l_{\text{кр}}^2/4} = 2 \rho_{\text{в}} \sin^2(\alpha_{\text{в}}/4)",
              f"2 × {fmt(p['rho_v'])} × sin²({fmt(p['alpha_v'])}° / 4)",
              f"f = {fmt(c['f_izg'])} м")
    draw_step("15. Коэффициент угла [(4.27)]",
              r"k_\alpha = 1 \text{ при } \alpha_{\text{в}} \le 45^\circ; \text{ иначе } \sqrt{\sin^2(\alpha_{\text{в}}/2) + \cos^4(\alpha_{\text{в}}/2)}",
              f"√[sin²({fmt(p['alpha_v'])}°/2) + cos⁴({fmt(p['alpha_v'])}°/2)]",
              f"kα = {fmt(c['k_alpha'])} —")
    draw_step("16. Сопротивление по первой проверке [(4.25)]",
              r"q_{\text{в.треб1}} = \frac{2 k_{\text{н.п}} S_{\text{сж}}}{l_{\text{кр}}\sqrt{1 + (l_{\text{кр}}/f)^2 / 16}}",
              f"2 × {fmt(p['k_np'])} × {fmt(c['S'] * 1e6)} / [{fmt(c['l_kr'])} × √(1 + ({fmt(c['l_kr'])}/{fmt(c['f_izg'])})² / 16)]",
              f"qв.треб1 = {fmt(c['q_v_treb1'])} Н/м")
    draw_step("17. Сопротивление по второй проверке [(4.26)]",
              r"q_{\text{в.треб2}} = \frac{k_{\text{н.п}} S_{\text{сж}}}{k_\alpha \rho_{\text{в}}}",
              f"{fmt(p['k_np'])} × {fmt(c['S'] * 1e6)} / ({fmt(c['k_alpha'])} × {fmt(p['rho_v'])})",
              f"qв.треб2 = {fmt(c['q_v_treb2'])} Н/м")
    draw_step("18. Минимальный радиус по обеим проверкам [(4.25), (4.26)]",
              r"\rho_{\text{в.min}} = \frac{\rho_{\text{в}}\max(q_{\text{в.треб1}};\; q_{\text{в.треб2}})}{q_{\text{в}}}",
              f"{fmt(p['rho_v'])} × max({fmt(c['q_v_treb1'])}; {fmt(c['q_v_treb2'])}) / {fmt(c['q_v_83'])}",
              f"ρв.min = {fmt(c['rho_v_min'])} м")

    st.markdown("**Проверяемые условия (8.6)**")
    st.table(pd.DataFrame({
        "Условие": [
            "Подъём, первая проверка qв ≥ qв.треб1",
            "Подъём, вторая проверка qв ≥ qв.треб2"
        ],
        "Подстановка и итог": [
            f"{fmt(c['q_v_83'])} ≥ {fmt(c['q_v_treb1'])} Н/м — {'выполняется' if c['ok_86_1'] else 'не выполняется'}",
            f"{fmt(c['q_v_83'])} ≥ {fmt(c['q_v_treb2'])} Н/м — {'выполняется' if c['ok_86_2'] else 'не выполняется'}"
        ]
    }))
    st.markdown("**Таблица результатов (8.6)**")
    st.table(pd.DataFrame({
        "Величина": ["Сопротивление подъёму", "Хорда вертикальной кривой", "Стрела изгиба", "Коэффициент угла",
                     "Сопротивление по первой проверке", "Сопротивление по второй проверке",
                     "Минимальный радиус по обеим проверкам"],
        "Обозначение": ["qв", "lкр", "f", "kα", "qв.треб1", "qв.треб2", "ρв.min"],
        "Результат": [fmt(c['q_v_83']), fmt(c['l_kr']), fmt(c['f_izg']), fmt(c['k_alpha']), fmt(c['q_v_treb1']),
                      fmt(c['q_v_treb2']), fmt(c['rho_v_min'])],
        "Единица": ["Н/м", "м", "м", "—", "Н/м", "Н/м", "м"]
    }))


def render_8_7(p, c):
    st.subheader("Расчёт 8.7. Продольные перемещения (Раздел 5)")
    draw_step("1. Предельное касательное напряжение [(5.5)]",
              r"\tau_{\text{пр}} = p_{\text{гр}} \tan \varphi_{\text{гр}}",
              f"{fmt(c['p_gr_87'])} × tg {fmt(p['phi_deg'])}°",
              f"τпр = {fmt(c['tau_pr_87'] / 1000.0)} кПа ({fmt(c['tau_pr_87'])} Па)")
    draw_step("2. Коэффициент затухания [(5.8)]",
              r"\beta = \sqrt{\frac{\pi D_{\text{н}} k_{\text{и}}}{E F}}",
              f"√[π × {fmt(c['D_H_m'])} × {fmt(p['k_i'] * 1e6)} / ({fmt(p['E'] * 1e6)} × {fmt(c['F'])})]",
              f"β = {fmt(c['beta_87'])} 1/м")
    draw_step("3. Предельное удерживающее усилие [(5.12), (5.14)]",
              r"P_{\text{пр}} = \frac{\tau_{\text{пр}} \beta E F}{k_{\text{и}} \tanh(3.5)}",
              f"при l₁ = 3,5/β = {fmt(c['l1_87'])} м",
              f"Pпр = {fmt(c['P_pr_87'])} МН")
    draw_step("4. Длины зон деформации и перемещение свободного конца [(5.16), (5.19)]",
              r"l_1 = \frac{3.5}{\beta}; \quad l_2 = \frac{S - P_{\text{пр}}}{p_0}; \quad u_{\text{end}}",
              f"l₁ = {fmt(c['l1_87'])} м; l₂ = {fmt(c['l2_87'])} м",
              f"u = {fmt(c['u_end'])} мм")


# --- БОКОВАЯ ПАНЕЛЬ НАВИГАЦИИ ---
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
st.sidebar.caption("Быстрая загрузка исходных данных:")
col_pr1, col_pr2 = st.sidebar.columns(2)
if col_pr1.button("Вариант 1020"):
    st.session_state.params = PRESET_TETRAD.copy()
    st.rerun()
if col_pr2.button("Пример 630"):
    st.session_state.params = PRESET_DOCX.copy()
    st.rerun()

p = st.session_state.params
c = calculate_all(p)

st.sidebar.info(
    f"**В памяти:**\nDн = {fmt(p['D_H'])} мм | δн = {fmt(p['delta_n'])} мм\np = {fmt(p['P'])} МПа | Δtˣ = {fmt(c['dt_x'])} °C")


def find_image(base_name):
    for ext in ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']:
        if os.path.exists(base_name + ext): return base_name + ext
    return None


# ==============================================================================
# СТРАНИЦА 1: КЛИМАТОЛОГИЯ
# ==============================================================================
if page == "1. Климатология":
    st.title("1. Климатология и температурный перепад (Δt)")
    col_map1, col_map2 = st.columns([1, 1])
    with col_map1:
        region = st.selectbox("Город из базы:", ["Задать вручную"] + list(CLIMATE_DATA.keys()))
        if region != "Задать вручную":
            if st.button("Применить температуры выбранного города"):
                st.session_state.params['t_x'] = CLIMATE_DATA[region]["t_min"]
                st.session_state.params['t_m'] = CLIMATE_DATA[region]["t_max"]
                st.rerun()
        p_input("Температура замыкания зимой (tˣ), °C", "t_x", step=1.0)
        p_input("Температура замыкания летом (tᵐ), °C", "t_m", step=1.0)

        idx_prod = 0 if p['product_type'] == "Нефть" else 1
        new_prod = st.radio("Тип продукта:", ["Нефть", "Газ"], index=idx_prod, horizontal=True)
        if new_prod != p['product_type']:
            st.session_state.params['product_type'] = new_prod
            st.session_state.params['t_product'] = 5.0 if new_prod == "Нефть" else 6.0
            st.session_state.params['rho_prod'] = 870.0 if new_prod == "Нефть" else 0.8
            st.rerun()
        p_input("Температура эксплуатации (tэ), °C", "t_product", step=1.0)

    with col_map2:
        map_mode = st.radio("Слой карты:",
                            ["Зимние температуры (t_min)", "Летние температуры (t_max)", "Снеговые районы",
                             "Ветровые районы"], horizontal=True)
        df_anchors = pd.DataFrame.from_dict(CLIMATE_DATA, orient='index').reset_index().rename(
            columns={'index': 'Город'})
        df_grid = generate_zone_grid(df_anchors, map_mode)
        layer_zones = pdk.Layer("PolygonLayer", df_grid, get_polygon="polygon", get_fill_color="color", opacity=0.6,
                                stroked=False)
        layer_cities = pdk.Layer("ScatterplotLayer", df_anchors, get_position=["lon", "lat"], get_radius=25000,
                                 get_fill_color=[40, 40, 40, 220])
        st.pydeck_chart(pdk.Deck(map_provider="carto", map_style="light", layers=[layer_zones, layer_cities],
                                 initial_view_state=pdk.ViewState(latitude=62.0, longitude=90.0, zoom=2.0)))

    c = calculate_all(st.session_state.params)
    st.success(
        f"**Холодный перепад:** Δtˣ = {fmt(p['t_product'])} − ({fmt(p['t_x'])}) = **{fmt(c['dt_x'])} °C** | **Тёплый перепад:** Δtᵐ = {fmt(p['t_product'])} − ({fmt(p['t_m'])}) = **{fmt(c['dt_m'])} °C**")

    with st.expander("Посмотреть оригинальные карты из СНиП"):
        tab_img1, tab_img2, tab_img3, tab_img4, tab_img5 = st.tabs(["t_max", "t_min", "Снег", "Ветер", "Гололед"])
        with tab_img1:
            img = find_image("Снимок экрана 2026-10-09 в 00.49.04") or find_image("map_max")
            if img: st.image(img, use_container_width=True)
        with tab_img2:
            img2 = find_image("Снимок экрана 2026-10-09 в 00.49.13") or find_image("map_min")
            if img2: st.image(img2, use_container_width=True)
        with tab_img3:
            img3 = find_image("Снимок экрана 2026-10-09 в 00.49.19") or find_image("map_snow")
            if img3: st.image(img3, use_container_width=True)
        with tab_img4:
            img4 = find_image("Снимок экрана 2026-10-09 в 00.49.27") or find_image("map_wind")
            if img4: st.image(img4, use_container_width=True)
        with tab_img5:
            img5 = find_image("Снимок экрана 2026-10-09 в 00.49.35") or find_image("map_ice")
            if img5: st.image(img5, use_container_width=True)

# ==============================================================================
# СТРАНИЦА 2: 8.1
# ==============================================================================
elif page == "2. 8.1: Толщина стенки":
    st.title("Модуль 8.1. Требуемая толщина стенки")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_input("Наружный диаметр Dн, мм", "D_H", step=10.0)
        p_input("Принятая толщина стенки δн, мм (Ручной выбор)", "delta_n", step=0.5)
        p_input("Рабочее давление p, МПа", "P", step=0.5)
    with col2:
        p_input("Предел прочности R₁н, МПа", "R1_n", step=10.0)
        p_input("Предел текучести R₂н, МПа", "R2_n", step=10.0)
        p_input("Надёжность по давлению n", "n_p", step=0.05)
    with col3:
        p_input("Коэффициент условий работы m", "m", step=0.01)
        p_input("Надёжность по материалу k₁", "k1", step=0.01)
        p_input("Надёжность по назначению kн", "k_H", step=0.01)

    c = calculate_all(st.session_state.params)
    col_b1, col_b2 = st.columns(2)
    if col_b1.button(f"Принять минимальную по 8.1 из сортамента ({fmt(c['delta_sort'])} мм)"):
        st.session_state.params['delta_n'] = c['delta_sort']
        st.rerun()
    opt_82 = auto_select_thickness(st.session_state.params)
    if col_b2.button(f"🚀 Автоподбор с учётом прочности 8.2 ({fmt(opt_82)} мм)"):
        st.session_state.params['delta_n'] = opt_82
        st.rerun()
    st.markdown("---")
    render_8_1(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 3: 8.2
# ==============================================================================
elif page == "3. 8.2: Прочность по деформациям":
    st.title("Модуль 8.2. Прочность по деформациям")

    opt_delta = auto_select_thickness(st.session_state.params)
    col_auto1, col_auto2 = st.columns([2, 1])
    with col_auto1:
        st.markdown(
            f"<div class='info-text'>Минимальная толщина из сортамента ГОСТ, при которой выполняются все условия 8.1 и 8.2: <b>{fmt(opt_delta)} мм</b>. Вы можете применить её кнопкой справа или ввести любое значение вручную ниже.</div>",
            unsafe_allow_html=True)
    with col_auto2:
        st.write("")
        if st.button(f"🚀 Автоподбор для 8.2 (Установить {fmt(opt_delta)} мм)", use_container_width=True):
            st.session_state.params['delta_n'] = opt_delta
            st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        p_input("Принятая толщина стенки δн, мм (Ручной ввод)", "delta_n", step=0.5)
        p_input("Радиус упругого изгиба ρ, м", "rho_izg", step=50.0)
    with col2:
        p_input("Модуль Юнга E, МПа", "E", step=1000.0)
        p_input("Коэффициент Пуассона μ", "mu", step=0.01)
    with col3:
        p_input("Линейное расширение α, 1/°C", "alpha", step=0.000001)
        p_input("Замыкание зимой tˣ, °C", "t_x", step=1.0)

    c = calculate_all(st.session_state.params)
    st.markdown("---")
    render_8_2(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 4: 8.3
# ==============================================================================
elif page == "4. 8.3: Продольная устойчивость":
    st.title("Модуль 8.3. Общая продольная устойчивость")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_input("Удельный вес грунта γгр, кН/м³", "gamma_gr", step=0.5)
        p_input("Внутреннее трение грунта φгр, град", "phi_deg", step=1.0)
        p_input("Сцепление грунта cгр, кПа", "c_gr", step=1.0)
    with col2:
        p_input("Засыпка над трубой h₀, м", "h0", step=0.1)
        p_input("Постель грунта при сжатии k₀, МН/м³", "k_0", step=0.5)
        p_input("Коэффициент номограммы β", "beta_nom", step=0.5)
    with col3:
        p_input("Толщина изоляции δиз, мм", "delta_ins", step=0.5)
        p_input("Плотность изоляции ρиз, кг/м³", "rho_ins", step=50.0)
        p_input("Плотность жидкого продукта ρпр, кг/м³", "rho_prod", step=10.0)

    c = calculate_all(st.session_state.params)
    st.markdown("---")
    render_8_3(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 5: 8.4
# ==============================================================================
elif page == "5. 8.4: Устойчивость в насыпи (Прямой)":
    st.title("Модуль 8.4. Устойчивость в грунтовой насыпи")
    col1, col2 = st.columns(2)
    with col1:
        p_input("Высота до верхней образующей h₁, м", "h1", step=0.05)
        p_input("Полная высота насыпи H, м", "H", step=0.1)
    with col2:
        p_input("Половина ширины поверху b, м", "b", step=0.05)
        p_input("Угол откоса насыпи αн, град", "alpha_H", step=1.0)

    c = calculate_all(st.session_state.params)
    st.markdown("---")
    render_8_4(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 6: 8.5
# ==============================================================================
elif page == "6. 8.5: Горизонтальный поворот":
    st.title("Модуль 8.5. Устойчивость на горизонтальном повороте")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_input("Радиус горизонтального поворота ρгор, м", "rho_gor", step=50.0)
    with col2:
        p_input("Трение трубы о грунт fтр", "f_gr", step=0.05)
    with col3:
        p_input("Запас против сдвига kсдв", "k_sdv", step=0.05)

    c = calculate_all(st.session_state.params)
    st.markdown("---")
    render_8_5(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 7: 8.6
# ==============================================================================
elif page == "7. 8.6: Вертикальный поворот":
    st.title("Модуль 8.6. Устойчивость на вертикальном повороте")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_input("Радиус вертикального поворота ρв, м", "rho_v", step=50.0)
    with col2:
        p_input("Угол вертикального поворота αв, град", "alpha_v", step=1.0)
    with col3:
        p_input("Запас против подъёма kн.п", "k_np", step=0.05)

    c = calculate_all(st.session_state.params)
    st.markdown("---")
    render_8_6(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 8: 8.7
# ==============================================================================
elif page == "8. 8.7: Продольные перемещения":
    st.title("Модуль 8.7. Продольные перемещения и графики (Раздел 5)")
    p_input("Постель грунта при сдвиге kи, МН/м³", "k_i", step=0.5)
    c = calculate_all(st.session_state.params)
    st.markdown("---")
    render_8_7(st.session_state.params, c)
    st.markdown("---")
    render_all_charts(st.session_state.params, c)

# ==============================================================================
# СТРАНИЦА 9: ПОЛНЫЙ ИТОГОВЫЙ ОТЧЕТ ПО ОБРАЗЦУ DOCX + ГРАФИКИ
# ==============================================================================
elif page == "9. Итоговый отчет":
    st.sidebar.markdown("---")
    student_name = st.sidebar.text_input("ФИО / Исполнитель", value="Ясавиев Артур")
    variant_num = st.sidebar.text_input("Вариант", value="15")
    project_name = st.sidebar.text_input("Название проекта", value="Калькулятор трубопровода 8.1–8.6")

    p = st.session_state.params
    c = calculate_all(p)
    all_ok = all([c['ok_81'], c['ok_82'], c['ok_83'], c['ok_84'], c['ok_85'], c['ok_86']])

    st.markdown(f"## Расчёт прочности и устойчивости трубопровода")
    st.markdown(
        f"**{student_name} — вариант {variant_num}**  \n**{project_name}**  \nДата и время формирования: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

    if all_ok:
        st.success("Все вычисленные условия модулей 8.1–8.6 выполняются.")
    else:
        st.warning("Внимание: некоторые условия не выполняются (см. сводку ниже).")

    st.table(pd.DataFrame({
        "Модуль": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6"],
        "Проверка": [
            "Требуемая толщина стенки",
            "Прочность по деформациям",
            "Общая продольная устойчивость",
            "Устойчивость в грунтовой насыпи",
            "Устойчивость на горизонтальном повороте",
            "Устойчивость на вертикальном повороте"
        ],
        "Итог": [
            "выполняется" if c['ok_81'] else "не выполняется",
            "выполняется" if c['ok_82'] else "не выполняется",
            "выполняется" if c['ok_83'] else "не выполняется",
            "выполняется" if c['ok_84'] else "не выполняется",
            "выполняется" if c['ok_85'] else "не выполняется",
            "выполняется" if c['ok_86'] else "не выполняется"
        ]
    }))

    st.header("Исходные данные")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown("**Геометрия трубы**")
        st.table(pd.DataFrame({
            "Параметр": ["Наружный диаметр", "Принятая толщина стенки", "Радиус упругого изгиба"],
            "Обозначение": ["Dн", "δн", "ρ"],
            "Значение": [fmt(p['D_H']), fmt(p['delta_n']), fmt(p['rho_izg'])],
            "Единица": ["мм", "мм", "м"]
        }))
        st.markdown("**Давление и температура**")
        st.table(pd.DataFrame({
            "Параметр": ["Рабочее давление", "Температура эксплуатации", "Замыкание в холодное время",
                         "Замыкание в тёплое время", "Надёжность по давлению"],
            "Обозначение": ["p", "tэ", "tˣ", "tᵐ", "n"],
            "Значение": [fmt(p['P']), fmt(p['t_product']), fmt(p['t_x']), fmt(p['t_m']), fmt(p['n_p'])],
            "Единица": ["МПа", "°C", "°C", "°C", "—"]
        }))
        st.markdown("**Изоляция и транспортируемый продукт**")
        st.table(pd.DataFrame({
            "Параметр": ["Толщина изоляции", "Плотность изоляции", "Надёжность по собств. весу",
                         "Надёжность по весу продукта", "Плотность продукта"],
            "Обозначение": ["δиз", "ρиз", "nс.в", "nпр", "ρпр"],
            "Значение": [fmt(p['delta_ins']), fmt(p['rho_ins']), fmt(p['n_sv']), fmt(p['n_pr']), fmt(p['rho_prod'])],
            "Единица": ["мм", "кг/м³", "—", "—", "кг/м³"]
        }))

    with col_i2:
        st.markdown("**Характеристики материала**")
        st.table(pd.DataFrame({
            "Параметр": ["Предел прочности", "Предел текучести", "Модуль Юнга", "Коэффициент Пуассона",
                         "Линейное расширение", "Коэффициент условий работы", "Надёжность по материалу",
                         "Надёжность по назначению", "Удельный вес металла"],
            "Обозначение": ["R₁н = σв", "R₂н = σт", "E = E₀", "μ = μ₀", "α", "m", "k₁", "kн", "γм"],
            "Значение": [fmt(p['R1_n']), fmt(p['R2_n']), fmt(p['E']), fmt(p['mu']), fmt(p['alpha']), fmt(p['m']),
                         fmt(p['k1']), fmt(p['k_H']), fmt(p['gamma_m'])],
            "Единица": ["МПа", "МПа", "МПа", "—", "1/°C", "—", "—", "—", "кН/м³"]
        }))
        st.markdown("**Характеристики грунта и насыпи**")
        st.table(pd.DataFrame({
            "Параметр": ["Удельный вес грунта", "Внутреннее трение грунта", "Сцепление грунта",
                         "Постель грунта при сжатии", "Постель грунта при сдвиге", "Засыпка над трубой",
                         "Надёжность по весу грунта", "Высота до верхней образующей", "Полная высота насыпи",
                         "Половина ширины поверху", "Угол откоса насыпи", "Коэффициент номограммы"],
            "Обозначение": ["γгр", "φгр", "cгр", "k₀", "kи", "h₀", "nгр", "h₁", "H", "b", "αн", "β"],
            "Значение": [fmt(p['gamma_gr']), fmt(p['phi_deg']), fmt(p['c_gr']), fmt(p['k_0']), fmt(p['k_i']),
                         fmt(p['h0']), fmt(p['n_gr']), fmt(p['h1']), fmt(p['H']), fmt(p['b']), fmt(p['alpha_H']),
                         fmt(p['beta_nom'])],
            "Единица": ["кН/м³", "град", "кПа", "МН/м³", "МН/м³", "м", "—", "м", "м", "м", "град", "—"]
        }))
        st.markdown("**Параметры горизонтального и вертикального поворота**")
        st.table(pd.DataFrame({
            "Параметр": ["Радиус горизонтального поворота", "Трение трубы о грунт", "Запас против сдвига",
                         "Радиус вертикального поворота", "Угол вертикального поворота", "Запас против подъёма"],
            "Обозначение": ["ρгор", "fтр", "kсдв", "ρв", "αв", "kн.п"],
            "Значение": [fmt(p['rho_gor']), fmt(p['f_gr']), fmt(p['k_sdv']), fmt(p['rho_v']), fmt(p['alpha_v']),
                         fmt(p['k_np'])],
            "Единица": ["м", "—", "—", "м", "град", "—"]
        }))

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_1(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_2(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_3(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_4(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_5(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_6(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_8_7(p, c)

    st.markdown("<div class='page-break'></div>", unsafe_allow_html=True)
    render_all_charts(p, c)

    st.markdown("---")
    st.subheader("Итоговые выводы")
    st.markdown(f"""
    * **8.1.** Условия {'выполняются' if c['ok_81'] else 'не выполняются'}.
    * **8.2.** Условия {'выполняются' if c['ok_82'] else 'не выполняются'}.
    * **8.3.** Условия {'выполняются' if c['ok_83'] else 'не выполняются'}.
    * **8.4.** Условия {'выполняются' if c['ok_84'] else 'не выполняются'}.
    * **8.5.** Условия {'выполняются' if c['ok_85'] else 'не выполняются'}.
    * **8.6.** Условия {'выполняются' if c['ok_86'] else 'не выполняются'}.
    """)

    if st.button("🖨️ Открыть диалог печати (Сохранить как PDF)"):
        st.components.v1.html("<script>window.parent.print();</script>", height=0)