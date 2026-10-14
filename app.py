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
    .warn-box { background-color: #fff8e1; padding: 12px 16px; border-radius: 6px; border-left: 4px solid #ff8f00; margin-bottom: 15px; color: #4e342e; font-size: 0.96em; }
    .result-block { background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #2e7d32; font-weight: bold; margin-bottom: 20px;}
    .error-block { background-color: #ffebee; padding: 15px; border-radius: 8px; border-left: 4px solid #d32f2f; color: #c62828; font-weight: bold; margin-bottom: 20px;}
    .info-text { font-size: 1.02em; color: #34495E; margin-bottom: 15px; line-height: 1.5; background-color: #e3f2fd; padding: 12px; border-radius: 5px; border-left: 4px solid #1976d2;}
    .svg-container { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; margin-bottom: 20px; text-align: center; }

    @media print {
        .page-break { page-break-before: always; }
        .no-break { page-break-inside: avoid; }
        header, footer, .stButton, section[data-testid="stSidebar"] { display: none !important; }
        .step-box { border: 1px solid #ddd; border-left: 3px solid #000; background-color: #fff !important; }
        .warn-box { border: 1px solid #ff8f00; background-color: #fff !important; }
        .svg-container { border: none; page-break-inside: avoid; }
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


def pct_diff(app_val, pdf_val):
    if pdf_val == 0:
        return "0"
    d = ((app_val - pdf_val) / abs(pdf_val)) * 100.0
    return fmt(d)


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
    c['psi_1'] = math.sqrt(under) - 0.5 * ratio_kc
    c['bend_stress'] = p['E'] * D_H_m / (2.0 * p['rho_izg'])

    base_x = p['mu'] * c['sig_kc_n'] - p['alpha'] * p['E'] * c['dt_x']
    c['sig_pr_x_minus'] = base_x - c['bend_stress']
    c['sig_pr_x_plus'] = base_x + c['bend_stress']
    c['sig_pr_x'] = c['sig_pr_x_minus'] if abs(c['sig_pr_x_minus']) >= abs(c['sig_pr_x_plus']) else c['sig_pr_x_plus']

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
    c['E_Pa'] = E_Pa
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

    # 8.7 и Эпюры Раздела 5 (стр. 81: nгр = 1,2; nс.в = 1,1; nпр = 1,0)
    c['q_tr_ep'] = 1.1 * (c['q_m_n'] + c['q_iz_n']) + 1.0 * c['q_pr_n']
    c['p_gr_87'] = (2.0 * 1.2 * gamma_gr_N * D_ins_m * (
                (p['h0'] + D_ins_m / 8.0) + (p['h0'] + D_ins_m / 2.0) * c['tan2_45_phi']) + c['q_tr_ep']) / (
                               math.pi * D_ins_m)
    c['tau_pr_87'] = c['p_gr_87'] * math.tan(math.radians(p['phi_deg'])) + p['c_gr'] * 1000.0
    c['beta_87'] = math.sqrt(math.pi * D_H_m * (p['k_i'] * 1e6) / (E_Pa * c['F']))
    c['l1_87'] = 3.5 / c['beta_87']
    c['p0_87'] = math.pi * D_ins_m * c['tau_pr_87']
    # Непрерывный переход по формуле 5.12/5.14 из методички:
    c['P_pr_87'] = (c['tau_pr_87'] * c['beta_87'] * E_Pa * c['F'] / ((p['k_i'] * 1e6) * math.tanh(3.5))) / 1e6

    S_abs = abs(c['S'])
    c['l2_87'] = max(0.0, (S_abs * 1e6 - c['P_pr_87'] * 1e6) / c['p0_87'])
    if S_abs > c['P_pr_87']:
        c['u_end'] = ((c['tau_pr_87'] / (p['k_i'] * 1e6)) + (
                    ((S_abs * 1e6) ** 2 - (c['P_pr_87'] * 1e6) ** 2) / (2.0 * c['p0_87'] * E_Pa * c['F']))) * 1000.0
    else:
        c['u_end'] = (S_abs * 1e6 * c['beta_87'] / (math.pi * D_H_m * (p['k_i'] * 1e6))) * 1000.0

    return c


# --- ГЕНЕРАТОР ВЕКТОРНЫХ ГРАФИКОВ SVG (100% КАК В РЕФЕРЕНСЕ PDF) ---
def svg_line_epure(x_vals, y_vals, l1_x, title, y_label, y_max_nice):
    W, H = 760, 340
    pad_l, pad_r, pad_t, pad_b = 65, 30, 45, 50
    pw, ph = W - pad_l - pad_r, H - pad_t - pad_b
    x_max = max(x_vals) if len(x_vals) > 0 and max(x_vals) > 0 else 1.0
    y_max = y_max_nice if y_max_nice > 0 else 1.0

    def tx(x):
        return pad_l + (x / x_max) * pw

    def ty(y):
        return pad_t + ph - (y / y_max) * ph

    svg = [
        f'<div class="svg-container"><svg viewBox="0 0 {W} {H}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">']
    svg.append(
        f'<text x="{W / 2}" y="25" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">{title}</text>')

    # Сетка Y
    for i in range(6):
        yv = y_max * i / 5.0
        py = ty(yv)
        svg.append(
            f'<line x1="{pad_l}" y1="{py:.1f}" x2="{W - pad_r}" y2="{py:.1f}" stroke="#ebebeb" stroke-width="1"/>')
        svg.append(f'<line x1="{pad_l - 4}" y1="{py:.1f}" x2="{pad_l}" y2="{py:.1f}" stroke="#333" stroke-width="1"/>')
        svg.append(
            f'<text x="{pad_l - 8}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#444">{fmt(yv)}</text>')

    # Сетка X
    step_x = 25.0 if x_max > 80 else 10.0
    xv = 0.0
    while xv <= x_max:
        px = tx(xv)
        svg.append(
            f'<line x1="{px:.1f}" y1="{pad_t}" x2="{px:.1f}" y2="{pad_t + ph}" stroke="#ebebeb" stroke-width="1"/>')
        svg.append(
            f'<line x1="{px:.1f}" y1="{pad_t + ph}" x2="{px:.1f}" y2="{pad_t + ph + 4}" stroke="#333" stroke-width="1"/>')
        svg.append(
            f'<text x="{px:.1f}" y="{pad_t + ph + 18}" text-anchor="middle" font-size="11" fill="#444">{int(xv)}</text>')
        xv += step_x

    # Оси
    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<line x1="{pad_l}" y1="{pad_t + ph}" x2="{W - pad_r}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')

    # Подписи осей
    svg.append(f'<text x="{pad_l + pw / 2}" y="{H - 10}" text-anchor="middle" font-size="12" fill="#222">x, м</text>')
    svg.append(
        f'<text x="18" y="{pad_t + ph / 2}" text-anchor="middle" font-size="12" fill="#222" transform="rotate(-90 18 {pad_t + ph / 2})">{y_label}</text>')

    # Граница упругой зоны
    if l1_x <= x_max:
        lx = tx(l1_x)
        svg.append(
            f'<line x1="{lx:.1f}" y1="{pad_t}" x2="{lx:.1f}" y2="{pad_t + ph}" stroke="#d4a359" stroke-width="1.8" stroke-dasharray="6,4"/>')

    # Линия графика
    pts = " ".join([f"{tx(x):.1f},{ty(y):.1f}" for x, y in zip(x_vals, y_vals)])
    svg.append(f'<polyline fill="none" stroke="#11698e" stroke-width="2.5" points="{pts}"/>')

    # Легенда
    lx_box, ly_box = pad_l + 12, pad_t + 10
    svg.append(
        f'<rect x="{lx_box}" y="{ly_box}" width="185" height="44" fill="#ffffff" fill-opacity="0.9" stroke="#ccc" rx="3"/>')
    svg.append(
        f'<line x1="{lx_box + 8}" y1="{ly_box + 14}" x2="{lx_box + 30}" y2="{ly_box + 14}" stroke="#11698e" stroke-width="2.5"/>')
    svg.append(f'<text x="{lx_box + 36}" y="{ly_box + 18}" font-size="11" fill="#333">Текущий проект</text>')
    svg.append(
        f'<line x1="{lx_box + 8}" y1="{ly_box + 32}" x2="{lx_box + 30}" y2="{ly_box + 32}" stroke="#d4a359" stroke-width="1.8" stroke-dasharray="5,3"/>')
    svg.append(f'<text x="{lx_box + 36}" y="{ly_box + 36}" font-size="11" fill="#333">Граница упругой зоны</text>')

    svg.append('</svg></div>')
    return "".join(svg)


def svg_bar_forces(c):
    W, H = 760, 350
    pad_l, pad_r, pad_t, pad_b = 65, 30, 45, 55
    pw, ph = W - pad_l - pad_r, H - pad_t - pad_b

    cats = [
        ("Прямой", "пластичная связь", c['N_kr_pl'], c['allow_83_pl']),
        ("Прямой", "упругая связь", c['N_kr_up'], c['allow_83_up']),
        ("Изогнутый", "меньшая оценка", c['N_kr_min'], c['allow_83_min']),
        ("Насыпь", "прямой участок", c['N_kr_84'], c['allow_84'])
    ]
    max_val = max([max(x[2], x[3]) for x in cats] + [abs(c['S'])]) * 1.12
    if max_val <= 0: max_val = 10.0

    def ty(y):
        return pad_t + ph - (y / max_val) * ph

    svg = [
        f'<div class="svg-container"><svg viewBox="0 0 {W} {H}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">']
    svg.append(
        f'<text x="{W / 2}" y="25" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">Расчётное и критические продольные усилия</text>')

    for i in range(6):
        yv = max_val * i / 5.0
        py = ty(yv)
        svg.append(
            f'<line x1="{pad_l}" y1="{py:.1f}" x2="{W - pad_r}" y2="{py:.1f}" stroke="#ebebeb" stroke-width="1"/>')
        svg.append(
            f'<text x="{pad_l - 8}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#444">{fmt(yv)}</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<line x1="{pad_l}" y1="{pad_t + ph}" x2="{W - pad_r}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<text x="18" y="{pad_t + ph / 2}" text-anchor="middle" font-size="12" fill="#222" transform="rotate(-90 18 {pad_t + ph / 2})">Усилие, МН</text>')

    col_w = pw / len(cats)
    bar_w = 42
    for idx, (l1, l2, nkr, allow) in enumerate(cats):
        cx = pad_l + (idx + 0.5) * col_w
        y1 = ty(nkr)
        y2 = ty(allow)
        svg.append(
            f'<rect x="{cx - bar_w:.1f}" y="{y1:.1f}" width="{bar_w}" height="{pad_t + ph - y1:.1f}" fill="#9cb4c9"/>')
        svg.append(f'<rect x="{cx:.1f}" y="{y2:.1f}" width="{bar_w}" height="{pad_t + ph - y2:.1f}" fill="#1f6f8b"/>')
        svg.append(
            f'<text x="{cx:.1f}" y="{pad_t + ph + 18}" text-anchor="middle" font-size="11" fill="#333">{l1}</text>')
        svg.append(
            f'<text x="{cx:.1f}" y="{pad_t + ph + 32}" text-anchor="middle" font-size="11" fill="#555">{l2}</text>')

    # Линия Sсж
    sy = ty(abs(c['S']))
    svg.append(f'<line x1="{pad_l}" y1="{sy:.1f}" x2="{W - pad_r}" y2="{sy:.1f}" stroke="#c82333" stroke-width="2.2"/>')

    # Легенда
    lx_box, ly_box = W - pad_r - 190, pad_t + 8
    svg.append(
        f'<rect x="{lx_box}" y="{ly_box}" width="182" height="60" fill="#ffffff" fill-opacity="0.92" stroke="#ccc" rx="3"/>')
    svg.append(
        f'<line x1="{lx_box + 8}" y1="{ly_box + 14}" x2="{lx_box + 28}" y2="{ly_box + 14}" stroke="#c82333" stroke-width="2.2"/>')
    svg.append(
        f'<text x="{lx_box + 34}" y="{ly_box + 18}" font-size="11" fill="#333">Расчётное Sсж ({fmt(c["S"])} МН)</text>')
    svg.append(f'<rect x="{lx_box + 8}" y="{ly_box + 25}" width="18" height="10" fill="#9cb4c9"/>')
    svg.append(f'<text x="{lx_box + 34}" y="{ly_box + 34}" font-size="11" fill="#333">Nкр</text>')
    svg.append(f'<rect x="{lx_box + 8}" y="{ly_box + 42}" width="18" height="10" fill="#1f6f8b"/>')
    svg.append(f'<text x="{lx_box + 34}" y="{ly_box + 51}" font-size="11" fill="#333">Допустимое (m/1,1) Nкр</text>')

    svg.append('</svg></div>')
    return "".join(svg)


def svg_radii_chart(p, c):
    W, H = 760, 350
    pad_l, pad_r, pad_t, pad_b = 65, 30, 45, 50
    pw, ph = W - pad_l - pad_r, H - pad_t - pad_b

    angles = np.linspace(5.0, 175.0, 80)
    r_425, r_426, r_both = [], [], []
    S_N = abs(c['S']) * 1e6
    qv = c['q_v_83'] if c['q_v_83'] > 0 else 1.0

    for a in angles:
        sin_a2 = math.sin(math.radians(a / 2.0))
        sin_a4 = math.sin(math.radians(a / 4.0))
        ratio_lf = (2.0 * sin_a2) / (2.0 * (sin_a4 ** 2)) if sin_a4 > 0 else 1.0
        r1 = (2.0 * p['k_np'] * S_N) / (qv * 2.0 * sin_a2 * math.sqrt(1.0 + (ratio_lf ** 2) / 16.0))
        ka = 1.0 if a <= 45.0 else math.sqrt(sin_a2 ** 2 + math.cos(math.radians(a / 2.0)) ** 4)
        r2 = (p['k_np'] * S_N) / (qv * ka)
        r_425.append(r1)
        r_426.append(r2)
        r_both.append(max(r1, r2))

    y_max = max(max(r_both), p['rho_v']) * 1.15
    if y_max <= 0: y_max = 1600.0

    def tx(a):
        return pad_l + (a / 180.0) * pw

    def ty(r):
        return pad_t + ph - min(1.0, max(0.0, r / y_max)) * ph

    svg = [
        f'<div class="svg-container"><svg viewBox="0 0 {W} {H}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">']
    svg.append(
        f'<text x="{W / 2}" y="25" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">Допустимые радиусы вертикального поворота</text>')

    for i in range(6):
        yv = y_max * i / 5.0
        py = ty(yv)
        svg.append(
            f'<line x1="{pad_l}" y1="{py:.1f}" x2="{W - pad_r}" y2="{py:.1f}" stroke="#ebebeb" stroke-width="1"/>')
        svg.append(
            f'<text x="{pad_l - 8}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#444">{int(yv)}</text>')

    for a_tick in [0, 25, 50, 75, 100, 125, 150, 175]:
        px = tx(a_tick)
        svg.append(
            f'<line x1="{px:.1f}" y1="{pad_t}" x2="{px:.1f}" y2="{pad_t + ph}" stroke="#ebebeb" stroke-width="1"/>')
        svg.append(
            f'<text x="{px:.1f}" y="{pad_t + ph + 18}" text-anchor="middle" font-size="11" fill="#444">{a_tick}</text>')

    # Закрашенная зона допустимых радиусов (выше кривой r_both)
    poly_pts = [f"{tx(angles[0]):.1f},{pad_t}"] + [f"{tx(a):.1f},{ty(r):.1f}" for a, r in zip(angles, r_both)] + [
        f"{tx(angles[-1]):.1f},{pad_t}"]
    svg.append(f'<polygon points="{" ".join(poly_pts)}" fill="#d4edda" fill-opacity="0.55"/>')

    pts_425 = " ".join([f"{tx(a):.1f},{ty(r):.1f}" for a, r in zip(angles, r_425)])
    pts_426 = " ".join([f"{tx(a):.1f},{ty(r):.1f}" for a, r in zip(angles, r_426)])
    pts_both = " ".join([f"{tx(a):.1f},{ty(r):.1f}" for a, r in zip(angles, r_both)])

    svg.append(f'<polyline fill="none" stroke="#6c757d" stroke-width="1.6" stroke-dasharray="5,4" points="{pts_425}"/>')
    svg.append(f'<polyline fill="none" stroke="#fd7e14" stroke-width="1.6" stroke-dasharray="3,3" points="{pts_426}"/>')
    svg.append(f'<polyline fill="none" stroke="#11698e" stroke-width="2.5" points="{pts_both}"/>')

    # Маркер текущего поворота
    cx_cur, cy_cur = tx(p['alpha_v']), ty(p['rho_v'])
    svg.append(f'<circle cx="{cx_cur:.1f}" cy="{cy_cur:.1f}" r="5.5" fill="#c82333" stroke="#fff" stroke-width="1.5"/>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<line x1="{pad_l}" y1="{pad_t + ph}" x2="{W - pad_r}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<text x="{pad_l + pw / 2}" y="{H - 10}" text-anchor="middle" font-size="12" fill="#222">Угол αв, град</text>')
    svg.append(
        f'<text x="18" y="{pad_t + ph / 2}" text-anchor="middle" font-size="12" fill="#222" transform="rotate(-90 18 {pad_t + ph / 2})">Минимальный радиус, м</text>')

    # Легенда
    lx_box, ly_box = pad_l + 12, pad_t + 10
    svg.append(
        f'<rect x="{lx_box}" y="{ly_box}" width="190" height="82" fill="#ffffff" fill-opacity="0.92" stroke="#ccc" rx="3"/>')
    svg.append(
        f'<line x1="{lx_box + 8}" y1="{ly_box + 13}" x2="{lx_box + 28}" y2="{ly_box + 13}" stroke="#6c757d" stroke-width="1.6" stroke-dasharray="4,3"/>')
    svg.append(f'<text x="{lx_box + 34}" y="{ly_box + 17}" font-size="11" fill="#333">По условию 4.25</text>')
    svg.append(
        f'<line x1="{lx_box + 8}" y1="{ly_box + 29}" x2="{lx_box + 28}" y2="{ly_box + 29}" stroke="#fd7e14" stroke-width="1.6" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{lx_box + 34}" y="{ly_box + 33}" font-size="11" fill="#333">По условию 4.26</text>')
    svg.append(
        f'<line x1="{lx_box + 8}" y1="{ly_box + 45}" x2="{lx_box + 28}" y2="{ly_box + 45}" stroke="#11698e" stroke-width="2.5"/>')
    svg.append(f'<text x="{lx_box + 34}" y="{ly_box + 49}" font-size="11" fill="#333">Оба условия (макс.)</text>')
    svg.append(f'<rect x="{lx_box + 8}" y="{ly_box + 56}" width="18" height="9" fill="#d4edda" stroke="#a3cfbb"/>')
    svg.append(f'<text x="{lx_box + 34}" y="{ly_box + 64}" font-size="11" fill="#333">Зона допустимых радиусов</text>')
    svg.append(f'<circle cx="{lx_box + 17}" cy="{ly_box + 75}" r="4" fill="#c82333"/>')
    svg.append(
        f'<text x="{lx_box + 34}" y="{ly_box + 78}" font-size="11" fill="#333">Текущий поворот ({fmt(p["rho_v"])} м)</text>')

    svg.append('</svg></div>')
    return "".join(svg)


def svg_compare_variants(c):
    W, H = 760, 280
    pad_l, pad_r, pad_t, pad_b = 65, 30, 45, 45
    pw, ph = W - pad_l - pad_r, H - pad_t - pad_b

    # Сравнение текущего расчета с эталоном из PDF
    s_cur, allow_cur = abs(c['S']), c['allow_83_min']
    s_pdf, allow_pdf = 8.45, 6.19

    max_v = max(s_cur, allow_cur, s_pdf, allow_pdf) * 1.18
    if max_v <= 0: max_v = 10.0

    def ty(y):
        return pad_t + ph - (y / max_v) * ph

    svg = [
        f'<div class="svg-container"><svg viewBox="0 0 {W} {H}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">']
    svg.append(
        f'<text x="{W / 2}" y="25" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">Сравнение вариантов исходных данных</text>')

    for i in range(5):
        yv = max_v * i / 4.0
        py = ty(yv)
        svg.append(
            f'<line x1="{pad_l}" y1="{py:.1f}" x2="{W - pad_r}" y2="{py:.1f}" stroke="#ebebeb" stroke-width="1"/>')
        svg.append(
            f'<text x="{pad_l - 8}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="#444">{fmt(yv)}</text>')

    svg.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<line x1="{pad_l}" y1="{pad_t + ph}" x2="{W - pad_r}" y2="{pad_t + ph}" stroke="#333" stroke-width="1.2"/>')
    svg.append(
        f'<text x="18" y="{pad_t + ph / 2}" text-anchor="middle" font-size="12" fill="#222" transform="rotate(-90 18 {pad_t + ph / 2})">Продольное усилие, МН</text>')

    groups = [("Текущий проект", s_cur, allow_cur), ("Пример методички (PDF)", s_pdf, allow_pdf)]
    gw = pw / 2.0
    bw = 55
    for idx, (gname, sv, av) in enumerate(groups):
        cx = pad_l + (idx + 0.5) * gw
        ys, ya = ty(sv), ty(av)
        svg.append(
            f'<rect x="{cx - bw - 4:.1f}" y="{ys:.1f}" width="{bw}" height="{pad_t + ph - ys:.1f}" fill="#e07a5f"/>')
        svg.append(f'<rect x="{cx + 4:.1f}" y="{ya:.1f}" width="{bw}" height="{pad_t + ph - ya:.1f}" fill="#3d405b"/>')
        svg.append(
            f'<text x="{cx:.1f}" y="{pad_t + ph + 22}" text-anchor="middle" font-size="12" font-weight="bold" fill="#333">{gname}</text>')

    lx_box, ly_box = W - pad_r - 185, pad_t + 8
    svg.append(
        f'<rect x="{lx_box}" y="{ly_box}" width="175" height="44" fill="#ffffff" fill-opacity="0.92" stroke="#ccc" rx="3"/>')
    svg.append(f'<rect x="{lx_box + 8}" y="{ly_box + 10}" width="16" height="10" fill="#e07a5f"/>')
    svg.append(f'<text x="{lx_box + 30}" y="{ly_box + 19}" font-size="11" fill="#333">Sсж (расчётное)</text>')
    svg.append(f'<rect x="{lx_box + 8}" y="{ly_box + 26}" width="16" height="10" fill="#3d405b"/>')
    svg.append(f'<text x="{lx_box + 30}" y="{ly_box + 35}" font-size="11" fill="#333">Допустимое при изгибе</text>')

    svg.append('</svg></div>')
    return "".join(svg)


def render_all_charts(p, c):
    st.subheader("📈 Графики и сравнение вариантов")
    st.markdown("""<div class='info-text'>
    Эпюры — дополнительная расчётная схема раздела 5 (формулы 5.4–5.19), не самостоятельный пример 8.1–8.6. 
    <i>x</i> отсчитывается от условно неподвижного сечения к свободному концу. Показаны модули усилий и перемещений; при S &lt; 0 направление обратное. 
    Для эпюр nгр = 1,2; nс.в = 1,1; nпр = 1,0 по стр. 81. Длина упругой зоны l₁ = 3,5/β. 
    Для непрерывного перехода Pпр = τпр βEF / [kи tanh(3,5)] (уточнение приближения 5.14 из 5.12). 
    График радиусов относится к устойчивости против подъёма по 4.25 и 4.26; проверки прочности упругого изгиба раздела 7 выполняются отдельно.
    </div>""", unsafe_allow_html=True)

    l1 = c['l1_87']
    l2 = c['l2_87']
    L_tot = l1 + l2
    x_el = np.linspace(0.0, l1, 50)
    x_pl = np.linspace(l1, L_tot, 40)[1:] if l2 > 0 else np.array([])
    x_all = np.concatenate([x_el, x_pl])

    beta = c['beta_87']
    tau_max = c['tau_pr_87'] if abs(c['S']) >= c['P_pr_87'] else (
                abs(c['S']) * 1e6 * (p['k_i'] * 1e6) * math.tanh(3.5) / (beta * c['E_Pa'] * c['F']))
    P_el_top = c['P_pr_87'] if abs(c['S']) >= c['P_pr_87'] else abs(c['S'])

    P_vals, u_vals, tau_vals = [], [], []
    sinh_35 = math.sinh(3.5)
    cosh_35_m1 = math.cosh(3.5) - 1.0

    for x in x_all:
        if x <= l1:
            tau_x = tau_max * (math.sinh(beta * x) / sinh_35)
            u_x = (tau_x / (p['k_i'] * 1e6)) * 1000.0
            P_x = P_el_top * ((math.cosh(beta * x) - 1.0) / cosh_35_m1)
        else:
            dx = x - l1
            tau_x = tau_max
            P_x = P_el_top + (c['p0_87'] * dx) / 1e6
            u_l1 = (tau_max / (p['k_i'] * 1e6)) * 1000.0
            u_x = u_l1 + ((P_el_top * 1e6 * dx + 0.5 * c['p0_87'] * (dx ** 2)) / (c['E_Pa'] * c['F'])) * 1000.0
        P_vals.append(P_x)
        u_vals.append(u_x)
        tau_vals.append(tau_x / 1000.0)  # кПа

    st.markdown("#### Продольное усилие по длине")
    st.markdown(svg_line_epure(x_all, P_vals, l1, "Продольное усилие по длине", "P(x), МН",
                               max(P_vals) * 1.08 if len(P_vals) else 4.0), unsafe_allow_html=True)

    st.markdown("#### Продольные перемещения по длине")
    st.markdown(svg_line_epure(x_all, u_vals, l1, "Продольные перемещения по длине", "u(x), мм",
                               max(u_vals) * 1.08 if len(u_vals) else 60.0), unsafe_allow_html=True)

    st.markdown("#### Касательные напряжения по длине")
    st.markdown(svg_line_epure(x_all, tau_vals, l1, "Касательные напряжения по длине", "τ(x), кПа",
                               max(tau_vals) * 1.08 if len(tau_vals) else 20.0), unsafe_allow_html=True)

    st.markdown("#### Расчётное и критические усилия")
    st.markdown(svg_bar_forces(c), unsafe_allow_html=True)

    st.markdown("#### Радиусы вертикального поворота")
    st.markdown(svg_radii_chart(p, c), unsafe_allow_html=True)

    st.markdown("#### Сравнение вариантов")
    st.markdown(svg_compare_variants(c), unsafe_allow_html=True)


# --- ФУНКЦИИ ОТРИСОВКИ ПОШАГОВЫХ РАСЧЕТОВ ПО МЕТОДИЧКЕ ---
def draw_step(num_title, latex_formula, sub_str, ans_str):
    st.markdown(f"<div class='step-box'><div class='step-title'>{num_title}</div>", unsafe_allow_html=True)
    st.latex(latex_formula)
    st.markdown(f"<div class='sub-line'>Подстановка: {sub_str}</div><div class='ans-line'>{ans_str}</div></div>",
                unsafe_allow_html=True)


def status_str(ok):
    return "✅ выполняется" if ok else "❌ не выполняется"


def render_8_1(p, c):
    st.subheader("📐 Расчёт 8.1. Требуемая толщина стенки")
    st.markdown(f"**Итог:** {status_str(c['ok_81'])}.")
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
    draw_step("5. Рекомендация из введённого сортамента [8.1]",
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

    st.markdown("**🔍 Проверяемые условия (8.1)**")
    st.table(pd.DataFrame({
        "Условие": ["Принятая толщина δн ≥ δтреб"],
        "Подстановка и итог": [f"{fmt(p['delta_n'])} ≥ {fmt(c['delta_treb'])} мм — {status_str(c['ok_81'])}"]
    }))
    st.markdown("**📋 Таблица результатов (8.1)**")
    st.table(pd.DataFrame({
        "Величина": ["Расчётное сопротивление R₁", "Расчётное сопротивление R₂", "Толщина по давлению",
                     "Минимум по конструктивным условиям", "Требуемая толщина", "Рекомендация из сортамента",
                     "Холодный темп. перепад", "Тёплый темп. перепад", "Внутренний диаметр"],
        "Обозначение": ["R₁", "R₂", "δ", "δmin", "δтреб", "δсорт", "Δtˣ", "Δtᵐ", "Dвн"],
        "Результат": [fmt(c['R1']), fmt(c['R2']), fmt(c['delta_p']), fmt(c['delta_min']), fmt(c['delta_treb']),
                      fmt(c['delta_sort']), fmt(c['dt_x']), fmt(c['dt_m']), fmt(c['D_vn'])],
        "Единица": ["МПа", "МПа", "мм", "мм", "мм", "мм", "°C", "°C", "мм"]
    }))
    st.markdown("**📊 Сопоставление с примером PDF (8.1)**")
    st.caption(
        "Исходные данные изменены пользователем. PDF содержит другой вариант; отклонение не является оценкой точности приложения.")
    st.table(pd.DataFrame({
        "Величина": ["Сопротивление R₁", "Толщина по давлению", "Толщина по сортаменту"],
        "Приложение": [fmt(c['R1']), fmt(c['delta_p']), fmt(c['delta_sort'])],
        "PDF": ["395,6", "10,28", "12,3"],
        "Единица": ["МПа", "мм", "мм"],
        "Δ %": [pct_diff(c['R1'], 395.6), pct_diff(c['delta_p'], 10.28), pct_diff(c['delta_sort'], 12.3)]
    }))


def render_8_2(p, c):
    st.subheader("🔬 Расчёт 8.2. Прочность по деформациям")
    st.markdown(f"**Итог:** {status_str(c['ok_82'])}.")
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
              r"\sigma_{\text{пр}}^n = \mu \sigma_{\text{кц}}^n - \alpha E \Delta t^x \pm \frac{E D_{\text{