import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import requests
import re
import locale
warnings.filterwarnings('ignore')

# Configurar locale para formato de números (Argentina: punto para miles, coma para decimales)
try:
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        pass  # Usar formato por defecto si no se puede configurar

def validar_formato_decimal(texto):
    """
    Valida que el formato de decimal sea correcto.
    Acepta: números enteros, números con punto decimal (45.20) o coma decimal (45,20)
    No acepta: formatos mixtos incorrectos (45.20,50 o 45,20.50)
    """
    if not texto or texto.strip() == '':
        return True, None  # Campo vacío es válido
    
    texto = texto.strip()
    
    # Permitir solo números, punto, coma y signo negativo
    if not re.match(r'^-?\d+([.,]\d+)?$', texto):
        return False, None
    
    # Verificar que no tenga ambos separadores
    tiene_punto = '.' in texto
    tiene_coma = ',' in texto
    
    if tiene_punto and tiene_coma:
        return False, None
    
    # Convertir a float
    try:
        # Reemplazar coma por punto para conversión
        texto_convertido = texto.replace(',', '.')
        valor = float(texto_convertido)
        return True, valor
    except:
        return False, None

def formatear_numero(numero, decimales=2, usar_separador_miles=True):
    """
    Formatea un número con separadores de miles y decimales según formato argentino.
    Usa punto para miles y coma para decimales (ej: 1.234,56)
    """
    if numero is None or pd.isna(numero):
        return "-"
    
    try:
        numero = float(numero)
        
        if usar_separador_miles:
            # Formatear con separador de miles y decimales
            # Usar formato: 1.234,56
            parte_entera = int(abs(numero))
            parte_decimal = abs(numero) - parte_entera
            
            # Formatear parte entera con separador de miles
            parte_entera_str = f"{parte_entera:,}".replace(",", ".")
            
            # Formatear parte decimal
            if decimales > 0:
                parte_decimal_str = f"{parte_decimal:.{decimales}f}".split('.')[1]
                signo = "-" if numero < 0 else ""
                return f"{signo}{parte_entera_str},{parte_decimal_str}"
            else:
                signo = "-" if numero < 0 else ""
                return f"{signo}{parte_entera_str}"
        else:
            # Sin separador de miles, solo decimales
            if decimales > 0:
                return f"{numero:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                return f"{numero:,.0f}".replace(",", ".")
    except:
        return str(numero)


# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Bonos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para el dashboard
st.markdown("""
<style>
    /* Forzar tema claro */
    .stApp {
        background-color: white !important;
        color: black !important;
    }
    
    .stApp > div {
        background-color: white !important;
    }
    
    /* Estilos generales */
    .main > div {
        padding-top: 0rem;
    }
    
    /* Eliminar espaciado superior adicional */
    .main .block-container {
        padding-top: 0rem !important;
    }
    
    .main .element-container {
        margin-top: 0rem !important;
    }
    
    /* Eliminar espaciado del primer elemento */
    .main .element-container:first-child {
        margin-top: 0rem !important;
        padding-top: 0rem !important;
    }
    
    /* Selectores más específicos para eliminar espaciado */
    .main .block-container > div {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    .main .block-container > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    /* Eliminar espaciado de columnas */
    .main .stColumn {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    .main .stColumn:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    /* Eliminar espaciado de contenedores de Streamlit */
    div[data-testid="stMarkdownContainer"] {
        margin-top: 0rem !important;
        padding-top: 0rem !important;
    }
    
    div[data-testid="stMarkdownContainer"]:first-child {
        margin-top: 0rem !important;
        padding-top: 0rem !important;
    }
    
    /* Alinear sección de resultados con el título del sidebar */
    .main .stColumn:first-child {
        margin-top: -2rem !important;
    }
    
    /* Reducir espaciado entre elementos en la columna principal */
    .main .stColumn:first-child .element-container {
        margin-top: -1rem !important;
    }
    
    /* Ajustar espaciado de las tarjetas */
    .main .stColumn:first-child .metrics-grid {
        margin-top: -1.5rem !important;
    }
    
    /* Reducir espaciado en el sidebar */
    .sidebar .element-container {
        margin-bottom: 0.2rem !important;
    }
    
    .sidebar .stMarkdown {
        margin-bottom: 0.1rem !important;
    }
    
    .sidebar .stMarkdown p {
        margin: 0.1rem 0 !important;
        line-height: 1.2 !important;
    }
    
    /* Reducir espaciado del separador en sidebar */
    .sidebar hr {
        margin: 0.2rem 0 !important;
    }
    
    /* Eliminar espaciado extra después del botón calcular */
    .sidebar .stButton {
        margin-bottom: 0.1rem !important;
    }
    
    /* Reducir espaciado del título "Información del Bono" */
    .sidebar h3 {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    /* Reducir espaciado después del título h3 en sidebar */
    .sidebar h3 + .stMarkdown {
        margin-top: 0.1rem !important;
    }
    
    /* Reducir espaciado del contenedor de información del bono */
    .sidebar .stMarkdown div {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    /* Eliminar bordes de widgets de TradingView */
    .tradingview-widget-container {
        border: none !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    .tradingview-widget-container__widget {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Eliminar bordes de iframes de TradingView */
    iframe[src*="tradingview"] {
        border: none !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Eliminar bordes de contenedores de Streamlit para TradingView */
    div[data-testid="stIFrame"] {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Eliminar bordes de componentes HTML */
    .stComponents iframe {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Intentar ocultar bordes internos de TradingView */
    .tradingview-widget-container * {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Ocultar bordes de elementos específicos de TradingView */
    .tradingview-widget-container table,
    .tradingview-widget-container tr,
    .tradingview-widget-container td,
    .tradingview-widget-container th {
        border: none !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    
    /* Aplicar estilos a todos los elementos dentro de TradingView */
    .tradingview-widget-container iframe {
        border: none !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Reducir espaciado del título "Datos de Mercado" */
    .main h2 {
        margin-bottom: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        line-height: 1.2 !important;
    }
    
    /* Eliminar espaciado extra después de títulos h2 */
    .main h2 + .stMarkdown {
        margin-top: -0.5rem !important;
    }
    
    /* Reducir espaciado de elementos después de títulos */
    .main h2 + div {
        margin-top: -0.5rem !important;
    }
    
    
    
    /* Reducir tamaño de títulos y alinear arriba */
    .main h1, .main h2, .main h3, 
    .main .element-container h1, .main .element-container h2, .main .element-container h3,
    .main .block-container h1, .main .block-container h2, .main .block-container h3 {
        margin-top: 0rem !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0rem !important;
        font-size: 1.2rem !important;
        line-height: 1.2 !important;
    }
    
    .main h1, .main .element-container h1, .main .block-container h1 {
        font-size: 1.4rem !important;
    }
    
    .main h2, .main .element-container h2, .main .block-container h2 {
        font-size: 1.2rem !important;
    }
    
    .main h3, .main .element-container h3, .main .block-container h3 {
        font-size: 1.1rem !important;
    }
    
    /* Selectores más específicos para Streamlit */
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3 {
        margin-top: 0rem !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0rem !important;
        font-size: 1.2rem !important;
        line-height: 1.2 !important;
    }
    
    /* Reducir espaciado en sidebar */
    .css-1d391kg {
        padding-top: 0.5rem !important;
    }
    
    .css-1d391kg .element-container {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    .css-1d391kg .stMarkdown {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Reducir espaciado en sección principal */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    .main .element-container {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Reducir espaciado entre elementos */
    .stSelectbox, .stDateInput, .stNumberInput, .stButton {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    div[data-testid="stMarkdownContainer"] h1 {
        font-size: 1.4rem !important;
    }
    
    div[data-testid="stMarkdownContainer"] h2 {
        font-size: 1.2rem !important;
    }
    
    div[data-testid="stMarkdownContainer"] h3 {
        font-size: 1.1rem !important;
    }
    
    /* Sidebar */
    .stSidebar {
        background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
        color: white;
    }
    
    /* Bajar el título del sidebar */
    .stSidebar h1 {
        margin-top: 0.8rem !important;
        padding-top: 0.8rem !important;
    }
    
    .stSidebar .element-container:first-child h1 {
        margin-top: 0.8rem !important;
        padding-top: 0.8rem !important;
    }
    
    .stSidebar .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    .stSidebar .stSelectbox label {
        color: white !important;
        font-weight: 600;
    }
    
    .stSidebar .stDateInput > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    .stSidebar .stDateInput label {
        color: white !important;
        font-weight: 600;
    }
    
    .stSidebar .stDateInput > div > div > input {
        color: white !important;
    }
    
    .stSidebar .stDateInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    .stSidebar .stNumberInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    .stSidebar .stNumberInput label {
        color: white !important;
        font-weight: 600;
    }
    
    .stSidebar .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
    }
    
    .stSidebar .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Botones secondary (azul) */
    .stButton > button[kind="secondary"] {
        background-color: #6b7280 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #4b5563 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3) !important;
    }
    
    /* Ocultar botones +/- del number input */
    .stNumberInput button {
        display: none !important;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        height: 120px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    
    .metric-label {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.2;
        text-align: center;
    }
    
    /* Grid de métricas */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 0.75rem;
    }
    
    /* Info bullets */
    .info-bullets {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-bullets h4 {
        color: #475569;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    .info-bullets p {
        color: #64748b;
        margin: 0.25rem 0;
        font-size: 0.85rem;
    }
    
    /* Future content */
    .future-content {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .future-content h3 {
        color: #1e293b;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
    
    .future-content ul {
        color: #64748b;
        margin: 0;
        padding-left: 1.5rem;
    }
    
    .future-content li {
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    /* Cash flow table */
    .cashflow-table {
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Ocultar bordes del dataframe */
    .stDataFrame {
        border: none !important;
    }
    
    .stDataFrame > div {
        border: none !important;
    }
    
    .stDataFrame table {
        border: none !important;
    }
    
    .stDataFrame th, .stDataFrame td {
        border: none !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    
    .stDataFrame th {
        background-color: #f8fafc !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    
    /* Ocultar menú del dataframe */
    .stDataFrame > div > div:first-child {
        display: none !important;
    }
    
    /* Ocultar barra de GitHub */
    .stDeployButton {
        display: none !important;
    }
    
    /* Ocultar elementos de GitHub/Streamlit Cloud */
    [data-testid="stDeployButton"] {
        display: none !important;
    }
    
    /* Ocultar cualquier elemento de deploy */
    .stDeployButton,
    .deploy-button,
    .github-button {
        display: none !important;
    }
    
    /* Ocultar barra superior de Streamlit Cloud */
    .stApp > header {
        display: none !important;
    }
    
    /* Ocultar elementos de la barra superior */
    .stApp > div > div > div:first-child {
        display: none !important;
    }
    
    /* Ocultar elementos específicos de GitHub */
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    .stApp > div > div > div:first-child > div {
        display: none !important;
    }
    
    /* Ocultar cualquier elemento con texto "Deploy" o "GitHub" */
    a[href*="github"],
    a[href*="deploy"],
    button[title*="Deploy"],
    button[title*="GitHub"] {
        display: none !important;
    }
    
    /* Reducir tamaño de fuentes en widgets de TradingView */
    iframe[src*="tradingview"] {
        font-size: 10px !important;
    }
    
    /* Reducir tamaño de fuentes en contenedores de TradingView */
    div[data-testid="stIFrame"] iframe {
        font-size: 10px !important;
    }
    
    /* Reducir tamaño de fuentes en elementos de TradingView */
    .tradingview-widget-container {
        font-size: 10px !important;
    }
    
    .tradingview-widget-container * {
        font-size: 10px !important;
    }
    
    /* Reducir tamaño de fuentes en iframes de TradingView */
    iframe[title*="TradingView"] {
        font-size: 10px !important;
    }
    
    /* Reducir tamaño de fuentes en todos los iframes */
    iframe {
        font-size: 10px !important;
    }
    
    /* Reducir tamaño de fuentes específicamente en el widget Market Data */
    .tradingview-widget-container[style*="height: 800px"] {
        font-size: 8px !important;
    }
    
    .tradingview-widget-container[style*="height: 800px"] * {
        font-size: 8px !important;
    }
    
    /* Reducir tamaño de fuentes en el widget Market Data */
    div[data-testid="stIFrame"] iframe[src*="market-overview"] {
        font-size: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# CSS condicional para ocultar sidebar cuando mercados está activo
if st.session_state.get('mercados_activo', False):
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    .main {
        margin-left: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Función para calcular el próximo día hábil
def get_next_business_day():
    today = datetime.now()
    next_day = today + timedelta(days=1)
    
    # Si es sábado (5) o domingo (6), ir al lunes
    if next_day.weekday() == 5:  # Sábado
        next_day += timedelta(days=2)
    elif next_day.weekday() == 6:  # Domingo
        next_day += timedelta(days=1)
    
    return next_day

# Función para calcular días entre fechas según base de cálculo
def calcular_dias(fecha1, fecha2, base_calculo):
    # Convertir ambas fechas a datetime para asegurar compatibilidad
    if hasattr(fecha1, 'date'):
        fecha1 = fecha1.date()
    if hasattr(fecha2, 'date'):
        fecha2 = fecha2.date()
    
    if base_calculo == "30/360":
        d1, m1, y1 = fecha1.day, fecha1.month, fecha1.year
        d2, m2, y2 = fecha2.day, fecha2.month, fecha2.year
        
        # Ajuste para 30/360
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            d2 = 30
        
        dias = (y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)
        return dias
    elif base_calculo == "ACT/360":
        return (fecha2 - fecha1).days
    elif base_calculo == "ACT/365":
        return (fecha2 - fecha1).days
    elif base_calculo == "ACT/ACT":
        return (fecha2 - fecha1).days
    else:
        return (fecha2 - fecha1).days

# Función para calcular YTM usando Newton-Raphson
def calcular_ytm(precio_dirty, flujos, fechas, fecha_liquidacion, base_calculo="ACT/365", periodicidad=2):
    # Convertir fecha_liquidacion a date si es datetime
    fecha_liq = fecha_liquidacion
    if hasattr(fecha_liq, 'date'):
        fecha_liq = fecha_liq.date()
    
    def npv(rate):
        total = 0
        for i, (flujo, fecha) in enumerate(zip(flujos, fechas)):
            dias = calcular_dias(fecha_liq, fecha, base_calculo)
            if base_calculo == "30/360":
                factor_descuento = (1 + rate) ** (dias / 360)
            elif base_calculo == "ACT/360":
                factor_descuento = (1 + rate) ** (dias / 360)
            elif base_calculo == "ACT/365":
                factor_descuento = (1 + rate) ** (dias / 365)
            elif base_calculo == "ACT/ACT":
                factor_descuento = (1 + rate) ** (dias / 365)
            else:
                factor_descuento = (1 + rate) ** (dias / 365)
            total += flujo / factor_descuento
        return total - precio_dirty
    
    def npv_derivative(rate):
        total = 0
        for i, (flujo, fecha) in enumerate(zip(flujos, fechas)):
            dias = calcular_dias(fecha_liq, fecha, base_calculo)
            if base_calculo == "30/360":
                factor_descuento = (1 + rate) ** (dias / 360)
                derivada = -flujo * (dias / 360) * (1 + rate) ** (dias / 360 - 1)
            elif base_calculo == "ACT/360":
                factor_descuento = (1 + rate) ** (dias / 360)
                derivada = -flujo * (dias / 360) * (1 + rate) ** (dias / 360 - 1)
            elif base_calculo == "ACT/365":
                factor_descuento = (1 + rate) ** (dias / 365)
                derivada = -flujo * (dias / 365) * (1 + rate) ** (dias / 365 - 1)
            elif base_calculo == "ACT/ACT":
                factor_descuento = (1 + rate) ** (dias / 365)
                derivada = -flujo * (dias / 365) * (1 + rate) ** (dias / 365 - 1)
            else:
                factor_descuento = (1 + rate) ** (dias / 365)
                derivada = -flujo * (dias / 365) * (1 + rate) ** (dias / 365 - 1)
            total += derivada
        return total
    
    # Método de Newton-Raphson
    rate = 0.05  # Tasa inicial
    tolerance = 1e-8
    max_iterations = 100
    
    for i in range(max_iterations):
        npv_val = npv(rate)
        if abs(npv_val) < tolerance:
            break
    
        derivative = npv_derivative(rate)
        if abs(derivative) < 1e-12:
            break
    
        rate = rate - npv_val / derivative
    
    # Si no converge, usar búsqueda binaria
    if abs(npv(rate)) > tolerance:
        low, high = 0.0, 1.0
        for _ in range(100):
            mid = (low + high) / 2
            if npv(mid) > 0:
                low = mid
            else:
                high = mid
            if high - low < tolerance:
                break
        rate = (low + high) / 2
    
    return rate

# Función para calcular duración Macaulay
def calcular_duracion_macaulay(flujos, fechas, fecha_liquidacion, ytm, base_calculo="ACT/365"):
    # Convertir fecha_liquidacion a date si es datetime
    fecha_liq = fecha_liquidacion
    if hasattr(fecha_liq, 'date'):
        fecha_liq = fecha_liq.date()
    
    pv_total = 0
    pv_weighted = 0
    
    for flujo, fecha in zip(flujos, fechas):
        dias = calcular_dias(fecha_liq, fecha, base_calculo)
        if base_calculo == "30/360":
            factor_descuento = (1 + ytm) ** (dias / 360)
        elif base_calculo == "ACT/360":
            factor_descuento = (1 + ytm) ** (dias / 360)
        elif base_calculo == "ACT/365":
            factor_descuento = (1 + ytm) ** (dias / 365)
        elif base_calculo == "ACT/ACT":
            factor_descuento = (1 + ytm) ** (dias / 365)
        else:
            factor_descuento = (1 + ytm) ** (dias / 365)
        
        pv = flujo / factor_descuento
        pv_total += pv
        pv_weighted += pv * (dias / 365)
    
    if pv_total == 0:
        return 0
    
    return pv_weighted / pv_total

# Función para calcular duración modificada
def calcular_duracion_modificada(duracion_macaulay, ytm, periodicidad):
    return duracion_macaulay / (1 + ytm / periodicidad)

# Función para calcular intereses corridos
def calcular_intereses_corridos(fecha_liquidacion, fecha_ultimo_cupon, tasa_cupon, capital_residual, base_calculo="ACT/365"):
    # Convertir fecha_liquidacion a date si es datetime
    fecha_liq = fecha_liquidacion
    if hasattr(fecha_liq, 'date'):
        fecha_liq = fecha_liq.date()
    
    dias = calcular_dias(fecha_ultimo_cupon, fecha_liq, base_calculo)
    if base_calculo == "30/360":
        return (tasa_cupon * capital_residual) / 360 * dias
    elif base_calculo == "ACT/360":
        return (tasa_cupon * capital_residual) / 360 * dias
    elif base_calculo == "ACT/365":
        return (tasa_cupon * capital_residual) / 365 * dias
    elif base_calculo == "ACT/ACT":
        return (tasa_cupon * capital_residual) / 365 * dias
    else:
        return (tasa_cupon * capital_residual) / 365 * dias

# Función para encontrar el último cupón
def encontrar_ultimo_cupon(fecha_liquidacion, fechas_cupones):
    fechas_anteriores = [fecha for fecha in fechas_cupones if fecha <= fecha_liquidacion]
    if not fechas_anteriores:
        return None
    return max(fechas_anteriores)

# Función para calcular vida media
def calcular_vida_media(flujos_capital, fechas, fecha_liquidacion, base_calculo="ACT/365"):
    # Convertir fecha_liquidacion a date si es datetime
    fecha_liq = fecha_liquidacion
    if hasattr(fecha_liq, 'date'):
        fecha_liq = fecha_liq.date()
    
    if not flujos_capital or sum(flujos_capital) == 0:
        return 0
    
    total_capital = sum(flujos_capital)
    vida_media = 0
    
    for flujo, fecha in zip(flujos_capital, fechas):
        if flujo > 0:
            dias = calcular_dias(fecha_liq, fecha, base_calculo)
            peso = flujo / total_capital
            vida_media += peso * (dias / 365)
    
    return vida_media

# Función para encontrar el próximo cupón
def encontrar_proximo_cupon(fecha_liquidacion, fechas_cupones):
    fechas_futuras = [fecha for fecha in fechas_cupones if fecha > fecha_liquidacion]
    if not fechas_futuras:
        return None
    return min(fechas_futuras)

# Función para encontrar el cupón vigente
def encontrar_cupon_vigente(fecha_liquidacion, flujos):
    """
    Encuentra el cupón vigente basado en la fecha de liquidación.
    Busca la fila cuya fecha es la inmediatamente anterior a la fecha de liquidación.
    """
    # Convertir fecha_liquidacion a date si es datetime
    fecha_liq = fecha_liquidacion
    if hasattr(fecha_liq, 'date'):
        fecha_liq = fecha_liq.date()
    
    # Filtrar fechas anteriores o iguales a la fecha de liquidación
    fechas_anteriores = []
    for flujo in flujos:
        fecha_flujo = flujo['fecha']
        if hasattr(fecha_flujo, 'date'):
            fecha_flujo = fecha_flujo.date()
        
        if fecha_flujo <= fecha_liq:
            fechas_anteriores.append((fecha_flujo, flujo['cupon_vigente']))
    
    if not fechas_anteriores:
        return 0.0  # Valor por defecto si no se encuentra
    
    # Encontrar la fecha más cercana (inmediatamente anterior)
    fecha_mas_cercana = max(fechas_anteriores, key=lambda x: x[0])
    return fecha_mas_cercana[1]

# Función para encontrar la fecha de vencimiento
def encontrar_fecha_vencimiento(flujos):
    """
    Encuentra la fecha de vencimiento del bono (última fecha de los flujos).
    """
    if not flujos:
        return None
    
    # Encontrar la fecha máxima entre todos los flujos
    fechas = [flujo['fecha'] for flujo in flujos]
    fecha_vencimiento = max(fechas)
    
    return fecha_vencimiento

@st.cache_data(ttl=300)  # Cache por 5 minutos
def obtener_precio_byma(ticker):
    """
    Obtiene el precio actual de un símbolo desde PyOBD (Open BYMA Data)
    Retorna el precio o None si no se puede obtener
    """
    if not ticker or ticker.strip() == '' or ticker == 'SPX500':
        return None
    
    try:
        from PyOBD import openBYMAdata
        
        # Inicializar PyOBD
        PyOBD = openBYMAdata()
        
        # Limpiar el ticker
        ticker_clean = ticker.strip().upper()
        
        # Intentar diferentes métodos para obtener el precio
        # Método 1: Buscar directamente por ticker
        methods = [
            lambda: PyOBD.get_ticker(ticker_clean),
            lambda: PyOBD.get_instrument(ticker_clean),
            lambda: PyOBD.get_symbol(ticker_clean),
            lambda: PyOBD.buscar(ticker_clean),
            lambda: PyOBD.search(ticker_clean),
        ]
        
        for method in methods:
            try:
                datos = method()
                if datos:
                    # Buscar precio en diferentes formatos
                    precio = None
                    if isinstance(datos, dict):
                        precio = (datos.get('precio') or datos.get('price') or 
                                 datos.get('last_price') or datos.get('ultimo_precio') or
                                 datos.get('precio_cierre') or datos.get('close') or
                                 datos.get('precio_ultimo') or datos.get('p') or
                                 datos.get('valor'))
                    elif isinstance(datos, list) and len(datos) > 0:
                        item = datos[0]
                        if isinstance(item, dict):
                            precio = (item.get('precio') or item.get('price') or 
                                     item.get('last_price') or item.get('ultimo_precio') or
                                     item.get('precio_cierre') or item.get('close'))
                    
                    if precio and precio > 0:
                        return round(float(precio), 2)
            except (AttributeError, TypeError, KeyError, IndexError):
                continue
        
        # Método 2: Obtener todos los datos y buscar nuestro ticker
        try:
            todos_methods = [
                lambda: PyOBD.get_all(),
                lambda: PyOBD.get_instruments(),
                lambda: PyOBD.get_symbols(),
                lambda: PyOBD.list(),
            ]
            
            for method in todos_methods:
                try:
                    todos_datos = method()
                    if todos_datos:
                        for item in todos_datos:
                            if isinstance(item, dict):
                                item_ticker = (item.get('ticker') or item.get('symbol') or 
                                             item.get('nombre') or item.get('name') or
                                             item.get('codigo') or item.get('code'))
                                if item_ticker:
                                    item_ticker_clean = str(item_ticker).strip().upper()
                                    # Buscar coincidencia exacta o parcial
                                    if ticker_clean == item_ticker_clean or ticker_clean in item_ticker_clean:
                                        precio = (item.get('precio') or item.get('price') or 
                                                 item.get('last_price') or item.get('ultimo_precio') or
                                                 item.get('precio_cierre') or item.get('close') or
                                                 item.get('p'))
                                        if precio and precio > 0:
                                            return round(float(precio), 2)
                except (AttributeError, TypeError):
                    continue
        except:
            pass
        
        return None
        
    except ImportError:
        # PyOBD no está instalado
        return None
    except Exception as e:
        # Cualquier otro error
        return None

# Cargar datos del Excel
try:
    df = pd.read_excel('bonos_flujos.xlsx', engine='openpyxl')
    
    # Los tipos de bonos se generarán automáticamente después de procesar los bonos
    
    # Procesar bonos
    bonos = []
    current_bono = None
    
    # No procesar ningún bono antes del bucle principal
    
    for index, row in df.iterrows():
        # Verificar si es el inicio de un nuevo bono (cualquier carácter que no sea fecha en columna A)
        if pd.notna(row.iloc[0]) and not isinstance(row.iloc[0], datetime):
            if current_bono:
                bonos.append(current_bono)
            
            # Función auxiliar para convertir a float de forma segura
            def safe_float(value, default=0):
                if pd.isna(value):
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            current_bono = {
                'nombre': str(row.iloc[0]),
                'base_calculo': str(row.iloc[1]) if pd.notna(row.iloc[1]) else "ACT/365",
                'periodicidad': int(row.iloc[2]) if pd.notna(row.iloc[2]) else 2,
                'tipo_bono': str(row.iloc[3]) if pd.notna(row.iloc[3]) else "General",
                'tasa_cupon': 0.0,  # Se calculará con el primer flujo
                'ticker': str(row.iloc[4]) if pd.notna(row.iloc[4]) else "SPX500",  # Columna E - ticker
                'flujos': []
            }
        elif current_bono and pd.notna(row.iloc[0]) and isinstance(row.iloc[0], datetime):
            # Es una fecha, agregar flujo
            fecha = row.iloc[0]
            
            # Función auxiliar para convertir a float de forma segura
            def safe_float(value, default=0):
                if pd.isna(value):
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # Si es el primer flujo, capturar la tasa de cupón
            if len(current_bono['flujos']) == 0:
                current_bono['tasa_cupon'] = safe_float(row.iloc[1], 0.0)  # Columna 2: cupón
            
            cupon = safe_float(row.iloc[2])  # Columna C
            capital = safe_float(row.iloc[3])  # Columna D
            total = safe_float(row.iloc[4])  # Columna E
            cupon_vigente = safe_float(row.iloc[1])  # Columna B - cupón vigente
            
            current_bono['flujos'].append({
                'fecha': fecha,
                'cupon': cupon,
                'capital': capital,
                'total': total,
                'cupon_vigente': cupon_vigente
            })
    
    if current_bono:
        bonos.append(current_bono)
    
    if not bonos:
        st.error("❌ No se encontraron bonos en el archivo")
        st.stop()
    
    # Generar tipos de bonos automáticamente a partir de los bonos procesados
    tipos_bono = list(set([bono['tipo_bono'] for bono in bonos]))
    tipos_bono.sort()  # Ordenar alfabéticamente
    tipos_bono = ["Todos"] + tipos_bono
    
    # Sidebar
    with st.sidebar:
        st.markdown("# CALCULADORA DE RENDIMIENTOS")
        
        # Filtro por tipo de bono
        if 'tipo_seleccionado' not in st.session_state:
            st.session_state.tipo_seleccionado = "Seleccione un Tipo"  # Valor inicial
        
        tipos_bono_con_seleccion = ["Seleccione un Tipo"] + tipos_bono
        
        # Usar una clave única que cambie cuando se presiona Volver
        if 'tipo_selectbox_key' not in st.session_state:
            st.session_state.tipo_selectbox_key = 0
        tipo_seleccionado = st.selectbox("Tipo de Bono", tipos_bono_con_seleccion, key=f"tipo_selectbox_{st.session_state.tipo_selectbox_key}")
        
        # Filtrar bonos por tipo
        if tipo_seleccionado == "Seleccione un Tipo":
            bonos_filtrados = bonos  # Mostrar todos los bonos cuando está en "Seleccione un Tipo"
        elif tipo_seleccionado == "Todos":
            bonos_filtrados = bonos
        else:
            bonos_filtrados = [bono for bono in bonos if bono['tipo_bono'] == tipo_seleccionado]
        
        if not bonos_filtrados:
            st.error("No hay bonos del tipo seleccionado")
            st.stop()
        
        # Selección de bono
        nombres_bonos = [bono['nombre'] for bono in bonos_filtrados]
        nombres_bonos.sort()  # Ordenar alfabéticamente
        
        # Inicializar session_state si no existe
        if 'bono_seleccionado' not in st.session_state:
            st.session_state.bono_seleccionado = None
        if 'calcular' not in st.session_state:
            st.session_state.calcular = False
        if 'mercados_activo' not in st.session_state:
            st.session_state.mercados_activo = False
            
        bono_seleccionado = st.selectbox(
            "Elija un Bono", 
            nombres_bonos,
            index=None,  # Ningún bono seleccionado por defecto
            placeholder="Seleccione un bono...",
            key="bono_selectbox"
        )
        
        # Actualizar session_state cuando cambia la selección
        if bono_seleccionado != st.session_state.bono_seleccionado:
            st.session_state.bono_seleccionado = bono_seleccionado
            st.session_state.calcular = False
        
        # Variables para uso en la sección principal
        if bono_seleccionado and not st.session_state.get('flujos_bono_seleccionado'):
            bono_actual = next(bono for bono in bonos_filtrados if bono['nombre'] == bono_seleccionado)
        else:
            st.session_state.calcular = False
            bono_actual = None
    
        # Calculadora de Flujos
        st.markdown("---")
        st.markdown("## CALCULADORA DE FLUJOS")
        
        # Inicializar session_state para flujos
        if 'flujos_tipo_seleccionado' not in st.session_state:
            st.session_state.flujos_tipo_seleccionado = "Seleccione un Tipo"  # Valor inicial
        if 'flujos_bono_seleccionado' not in st.session_state:
            st.session_state.flujos_bono_seleccionado = None
        if 'flujos_calcular' not in st.session_state:
            st.session_state.flujos_calcular = False
        
        # Filtro por tipo de bono para flujos
        flujos_tipos_bono_con_seleccion = ["Seleccione un Tipo"] + tipos_bono
        
        # Usar una clave única que cambie cuando se presiona Volver
        if 'flujos_tipo_selectbox_key' not in st.session_state:
            st.session_state.flujos_tipo_selectbox_key = 0
        flujos_tipo_seleccionado = st.selectbox("Tipo de Bono", flujos_tipos_bono_con_seleccion, key=f"flujos_tipo_selectbox_{st.session_state.flujos_tipo_selectbox_key}")
        
        # Filtrar bonos por tipo para flujos
        if flujos_tipo_seleccionado == "Seleccione un Tipo":
            flujos_bonos_filtrados = bonos  # Mostrar todos los bonos cuando está en "Seleccione un Tipo"
        elif flujos_tipo_seleccionado == "Todos":
            flujos_bonos_filtrados = bonos
        else:
            flujos_bonos_filtrados = [bono for bono in bonos if bono['tipo_bono'] == flujos_tipo_seleccionado]
        
        if not flujos_bonos_filtrados:
            st.error("No hay bonos del tipo seleccionado")
        else:
            # Selección de bono para flujos
            flujos_nombres_bonos = [bono['nombre'] for bono in flujos_bonos_filtrados]
            flujos_nombres_bonos.sort()  # Ordenar alfabéticamente
            
            flujos_bono_seleccionado = st.selectbox(
                "Elija un Bono", 
                flujos_nombres_bonos,
                index=None,  # Ningún bono seleccionado por defecto
                placeholder="Seleccione un bono...",
                key="flujos_bono_selectbox"
            )
            
            # Actualizar session_state solo cuando se selecciona un bono específico
            if flujos_bono_seleccionado and flujos_bono_seleccionado != st.session_state.flujos_bono_seleccionado:
                st.session_state.flujos_bono_seleccionado = flujos_bono_seleccionado
                st.session_state.flujos_calcular = False
            
            # Mensaje para agregar más bonos (solo si ya hay bonos seleccionados)
            if st.session_state.get('flujos_bonos_seleccionados') and len(st.session_state.flujos_bonos_seleccionados) > 0:
                st.markdown("**Para agregar más bonos:** Selecciona otro bono en el sidebar")
            
            # Si se selecciona un bono en flujos, limpiar la pantalla principal y selecciones de rendimientos
            if flujos_bono_seleccionado:
                st.session_state.calcular = False
                st.session_state.bono_seleccionado = None
                st.session_state.tipo_seleccionado = "Seleccione un Tipo"  # Valor inicial
                # Limpiar las selecciones de los selectbox de rendimientos
                if 'tipo_selectbox' in st.session_state:
                    del st.session_state['tipo_selectbox']
                if 'bono_selectbox' in st.session_state:
                    del st.session_state['bono_selectbox']
        
        # Botón Volver para flujos (siempre visible cuando hay bono seleccionado)
        if st.session_state.get('flujos_bono_seleccionado', None):
            if st.button("Volver", type="secondary", use_container_width=True, key="flujos_volver"):
                # Resetear TODAS las selecciones - estado inicial completo
                st.session_state.calcular = False
                st.session_state.bono_seleccionado = None
                st.session_state.tipo_seleccionado = "Seleccione un Tipo"
                
                # Limpiar TODAS las selecciones de flujos
                st.session_state.flujos_bono_seleccionado = None
                st.session_state.flujos_tipo_seleccionado = "Seleccione un Tipo"
                st.session_state.flujos_calcular = False
                if 'flujos_bonos_seleccionados' in st.session_state:
                    del st.session_state['flujos_bonos_seleccionados']
                
                # Incrementar claves únicas para forzar reset de selectbox
                st.session_state.tipo_selectbox_key += 1
                st.session_state.flujos_tipo_selectbox_key += 1
                
                # Limpiar TODOS los selectbox para forzar reset
                if 'bono_selectbox' in st.session_state:
                    del st.session_state['bono_selectbox']
                if 'flujos_bono_selectbox' in st.session_state:
                    del st.session_state['flujos_bono_selectbox']
                
                st.rerun()
    
        # Botón Mercados
        st.markdown("---")
        if st.button("Mercados", type="secondary", use_container_width=True, key="mercados_button"):
            st.session_state.mercados_activo = True
            # Limpiar otras selecciones
            st.session_state.calcular = False
            st.session_state.bono_seleccionado = None
            st.session_state.tipo_seleccionado = "Seleccione un Tipo"
            st.session_state.flujos_bono_seleccionado = None
            st.session_state.flujos_tipo_seleccionado = "Seleccione un Tipo"
            st.session_state.flujos_calcular = False
            st.session_state.indices_activo = False
            if 'flujos_bonos_seleccionados' in st.session_state:
                del st.session_state['flujos_bonos_seleccionados']
            st.rerun()
        
        # Botón Indices
        if st.button("Indices", type="secondary", use_container_width=True, key="indices_button"):
            st.session_state.indices_activo = True
            # Limpiar otras selecciones
            st.session_state.calcular = False
            st.session_state.bono_seleccionado = None
            st.session_state.tipo_seleccionado = "Seleccione un Tipo"
            st.session_state.flujos_bono_seleccionado = None
            st.session_state.flujos_tipo_seleccionado = "Seleccione un Tipo"
            st.session_state.flujos_calcular = False
            st.session_state.mercados_activo = False
            if 'flujos_bonos_seleccionados' in st.session_state:
                del st.session_state['flujos_bonos_seleccionados']
            st.rerun()
    
    # LÓGICA SIMPLIFICADA: S1, S2 y S3 son independientes
    
    # S3 (Mercados) - Prioridad más alta
    if st.session_state.get('mercados_activo', False):
        # CSS para reducir espacio superior
        st.markdown("""
        <style>
            .stColumn:first-child {
                padding-top: 0 !important;
                margin-top: 0 !important;
            }
            div[data-testid="column"]:first-child {
                padding-top: 0 !important;
                margin-top: 0 !important;
            }
            .element-container:first-child {
                padding-top: 0 !important;
                margin-top: 0 !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Layout con dos columnas: izquierda vacía, derecha para gráficos
        col_mercados_left, col_mercados_right = st.columns([1, 1])
        
        with col_mercados_left:
            # Mostrar los gráficos de TradingView (misma información que página inicial)
            # Crear 2 filas de 2 columnas cada una
            col1, col2 = st.columns(2)
            
            with col1:
                # S&P 500
                sp500_html = """
                    <div class="tradingview-widget-container" style="height: 300px; width: 100%; margin-top: -20px;">
                        <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
                        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                        {
                        "symbol": "SPX500",
                        "width": "100%",
                        "height": "300",
                        "locale": "es",
                        "dateRange": "1D",
                        "colorTheme": "light",
                        "isTransparent": true,
                        "autosize": false,
                        "largeChartUrl": "",
                        "hideTopToolbar": true,
                        "hideLegend": false,
                        "saveImage": false
                        }
                        </script>
                    </div>
                """
                st.components.v1.html(sp500_html, height=300)
                
            with col2:
                # IMV Merval
                imv_html = """
                <div class="tradingview-widget-container" style="height: 300px; width: 100%;">
                    <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
                    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                    {
                    "symbol": "IMV",
                    "width": "100%",
                    "height": "300",
                    "locale": "es",
                    "dateRange": "1D",
                    "colorTheme": "light",
                    "isTransparent": true,
                    "autosize": false,
                    "largeChartUrl": "",
                    "hideTopToolbar": true,
                    "hideLegend": false,
                    "saveImage": false
                    }
                    </script>
                </div>
                """
                st.components.v1.html(imv_html, height=300)
            
            # Espaciado reducido antes de la tabla de datos de mercado
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Construir JSON de símbolos (sin bonos soberanos)
            symbols_groups = [
                    {
                        "name": "Indices",
                        "symbols": [
                        {"name": "SPX500", "displayName": "S&P 500"},
                        {"name": "NASDAQ:IXIC", "displayName": "NASDAQ"},
                        {"name": "BMFBOVESPA:IBOV", "displayName": "Bovespa"},
                        {"name": "IMV", "displayName": "Merval"}
                    ]
                }
            ]
            
            # Agregar Monedas y Commodities
            symbols_groups.append({
                        "name": "Monedas",
                        "symbols": [
                    {"name": "FX_IDC:USDARS", "displayName": "USD/ARS"},
                    {"name": "FX_IDC:USDEUR", "displayName": "USD/EUR"},
                    {"name": "FX_IDC:USDGBP", "displayName": "USD/GBP"},
                    {"name": "FX_IDC:USDJPY", "displayName": "USD/JPY"}
                ]
            })
            
            symbols_groups.append({
                        "name": "Commodities",
                        "symbols": [
                    {"name": "TVC:USOIL", "displayName": "Petróleo WTI"},
                    {"name": "TVC:UKOIL", "displayName": "Petróleo Brent"},
                    {"name": "TVC:GOLD", "displayName": "Oro"},
                    {"name": "TVC:SILVER", "displayName": "Plata"}
                ]
            })
            
            # Widget Market Data - Ancho completo
            market_data_html = f"""
            <style>
                .tradingview-widget-container-left {{
                    font-size: 13.248px !important;
                }}
            </style>
            <div class="tradingview-widget-container tradingview-widget-container-left" style="height: 800px; width: 100%; font-size: 13.248px; margin-top: 0;">
                <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%; font-size: 13.248px;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js" async>
                {{
                "colorTheme": "light",
                "locale": "es",
                "largeChartUrl": "",
                "isTransparent": true,
                "showSymbolLogo": false,
                "backgroundColor": "transparent",
                "support_host": "https://www.tradingview.com",
                "width": "100%",
                "height": "800",
                "symbolsGroups": {json.dumps(symbols_groups, ensure_ascii=False)}
                }}
                </script>
                <script>
                    // NOTA IMPORTANTE: TradingView renderiza el contenido en un iframe de otro dominio (tradingview.com).
                    // Por políticas de seguridad del navegador (CORS - Cross-Origin Resource Sharing), 
                    // NO ES POSIBLE acceder al contenido del iframe desde JavaScript.
                    // Por lo tanto, ocultar la columna "Apertura" NO ES TÉCNICAMENTE POSIBLE.
                    // TradingView no proporciona una opción de configuración para ocultar columnas específicas.
                    // El código a continuación intentará ocultarla, pero fallará silenciosamente debido a CORS.
                    
                    function modificarColumnasLeft() {{
                        var container = document.querySelector('.tradingview-widget-container-left');
                        if (!container) return;
                        
                        var iframe = container.querySelector('iframe');
                        if (!iframe) {{
                            setTimeout(modificarColumnasLeft, 500);
                            return;
                        }}
                        
                        try {{
                            var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                            if (!iframeDoc) {{
                                setTimeout(modificarColumnasLeft, 500);
                                return;
                            }}
                            
                            var tables = iframeDoc.querySelectorAll('table');
                            tables.forEach(function(table) {{
                                var headers = table.querySelectorAll('th');
                                headers.forEach(function(th, index) {{
                                    var text = th.textContent || th.innerText || '';
                                    var colIndex = index + 1;
                                    
                                    // Reducir ancho de columna Nombre (primera columna)
                                    if (text.includes('Nombre') || text.includes('Name') || index === 0) {{
                                        table.querySelectorAll('th:nth-child(' + colIndex + '), td:nth-child(' + colIndex + ')').forEach(function(el) {{
                                            el.style.maxWidth = '80px';
                                            el.style.width = '80px';
                                            el.style.minWidth = '80px';
                                            el.style.overflow = 'hidden';
                                            el.style.textOverflow = 'ellipsis';
                                            el.style.whiteSpace = 'nowrap';
                                        }});
                                    }}
                                    
                                    // Intentar ocultar columna Apertura
                                    if (text.includes('Apertura') || text.includes('Open') || text.includes('Abrir')) {{
                                        table.querySelectorAll('th:nth-child(' + colIndex + '), td:nth-child(' + colIndex + ')').forEach(function(el) {{
                                            el.style.display = 'none';
                                        }});
                                    }}
                                }});
                            }});
                        }} catch(e) {{
                            // Esto fallará debido a CORS - es el comportamiento esperado
                            // No se puede acceder al contenido del iframe de TradingView por políticas de seguridad
                        }}
                    }}
                    
                    // Intentar múltiples veces (aunque no funcionará debido a CORS)
                    setTimeout(modificarColumnasLeft, 1000);
                    setTimeout(modificarColumnasLeft, 2000);
                    setTimeout(modificarColumnasLeft, 3000);
                </script>
            </div>
            """
            st.components.v1.html(market_data_html, height=800)
            
            # Botón para volver (debajo de las tablas)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Volver", type="secondary", use_container_width=True, key="mercados_volver_left"):
                st.session_state.mercados_activo = False
                st.rerun()
        
        with col_mercados_right:
            # Buscar el ticker de AL30 en la lista de bonos original (el que aparece en la tabla)
            # Buscar en bonos soberanos para encontrar el ticker en USD
            ticker_al30 = "AL30"  # Default
            for bono in bonos:
                ticker = bono.get('ticker', '').strip()
                nombre = bono.get('nombre', '').upper()
                tipo_bono = bono.get('tipo_bono', '').strip().lower()
                
                # Buscar AL30 que sea soberano y en USD
                if ticker and 'soberano' in tipo_bono and ('AL30' in ticker.upper() or 'AL30' in nombre):
                    # Preferir tickers que contengan USD o D (formato común para USD)
                    if 'USD' in tipo_bono or 'D' in ticker.upper()[-1:] or 'USD' in nombre:
                        ticker_al30 = ticker
                        break
                    elif ticker_al30 == "AL30":  # Si no encontramos uno en USD, usar el primero que encontremos
                        ticker_al30 = ticker
            
            # Buscar el ticker de T30J6 en la lista de bonos (el que aparece en la tabla)
            ticker_t30j6 = "BCBA:T30J6"  # Default
            for bono in bonos:
                ticker = bono.get('ticker', '').strip()
                nombre = bono.get('nombre', '').upper()
                tipo_bono = bono.get('tipo_bono', '').strip().lower()
                
                # Buscar T30J6 que sea soberano
                if ticker and 'soberano' in tipo_bono and ('T30J6' in ticker.upper() or 'T30J6' in nombre):
                    ticker_t30j6 = ticker
                    break
            
            # Mostrar los gráficos de TradingView
            # Crear 2 filas de 2 columnas cada una
            col1, col2 = st.columns(2)
            
            with col1:
                
                # AL30
                al30_html = f"""
                    <div class="tradingview-widget-container" style="height: 300px; width: 100%; margin-top: -20px;">
                        <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
                        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                        {{
                        "symbol": "{ticker_al30}",
                        "width": "100%",
                        "height": "300",
                        "locale": "es",
                        "dateRange": "1D",
                        "colorTheme": "light",
                        "isTransparent": true,
                        "autosize": false,
                        "largeChartUrl": "",
                        "hideTopToolbar": true,
                        "hideLegend": false,
                        "saveImage": false
                        }}
                        </script>
                    </div>
                """
                st.components.v1.html(al30_html, height=300)
                
            with col2:
                # T30J6
                t30j6_html = f"""
                <div class="tradingview-widget-container" style="height: 300px; width: 100%;">
                    <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
                    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                    {{
                    "symbol": "{ticker_t30j6}",
                    "width": "100%",
                    "height": "300",
                    "locale": "es",
                    "dateRange": "1D",
                    "colorTheme": "light",
                    "isTransparent": true,
                    "autosize": false,
                    "largeChartUrl": "",
                    "hideTopToolbar": true,
                    "hideLegend": false,
                    "saveImage": false
                    }}
                    </script>
                </div>
                """
                st.components.v1.html(t30j6_html, height=300)
            
            # Espaciado reducido antes de la tabla de datos de mercado
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Construir lista de bonos soberanos con ticker válido
            bonos_soberano = []
            
            for bono in bonos:
                ticker = bono.get('ticker', '').strip()
                tipo_bono = bono.get('tipo_bono', '').strip()
                
                if ticker and ticker != '' and ticker != 'SPX500':  # Excluir default y vacíos
                    # Agrupar por tipo de bono (case-insensitive y flexible)
                    tipo_lower = tipo_bono.lower()
                    
                    # Solo incluir bonos soberanos
                    if "soberano" in tipo_lower:
                        symbol_entry = {
                            "name": ticker,
                            "displayName": bono.get('nombre', ticker)
                        }
                        bonos_soberano.append(symbol_entry)
            
            # Filtrar bonos: eliminar AL41, GD41, GD46, AE38
            bonos_soberano = [b for b in bonos_soberano if b['name'] not in ['AL41', 'GD41', 'GD46', 'AE38'] and 'AL41' not in b['name'] and 'GD41' not in b['name'] and 'GD46' not in b['name'] and 'AE38' not in b['name']]
            bonos_soberano = [b for b in bonos_soberano if 'AL41' not in b.get('displayName', '') and 'GD41' not in b.get('displayName', '') and 'GD46' not in b.get('displayName', '') and 'AE38' not in b.get('displayName', '')]
            
            # Función auxiliar para normalizar ticker
            def normalizar_ticker(ticker_str):
                """Normaliza el ticker removiendo prefijos de exchange"""
                if ':' in ticker_str:
                    return ticker_str.split(':')[1].upper()
                return ticker_str.upper()
            
            # Definir orden de prioridad para los bonos específicos
            orden_prioridad = {
                'AL29': 1,
                'AL30': 2,
                'AL35': 3,
                'GD29': 4,
                'GD30': 5,
                'GD35': 6,
                'GD38': 7
            }
            
            # Bonos T específicos que van después
            bonos_t_especificos = ['T30E6', 'T30J6', 'T15E7', 'TY30P', 'TZXM6', 'TZXD6', 'TZXD7', 'TZX28']
            inicio_t = 100  # Prioridad base para bonos T específicos
            
            def obtener_prioridad(bono):
                """Obtiene la prioridad de ordenamiento de un bono"""
                ticker_norm = normalizar_ticker(bono['name'])
                display_norm = bono.get('displayName', '').upper()
                
                # Buscar en orden de prioridad
                for ticker_prioritario, prioridad in orden_prioridad.items():
                    if ticker_prioritario in ticker_norm or ticker_prioritario in display_norm:
                        return (prioridad, '')  # Tupla con prioridad y string vacío para ordenamiento estable
                
                # Buscar en bonos T específicos
                for i, ticker_t in enumerate(bonos_t_especificos):
                    if ticker_t in ticker_norm or ticker_t in display_norm:
                        return (inicio_t + i, '')  # Tupla con prioridad y string vacío
                
                # Resto de bonos: ordenar alfabéticamente después de los específicos
                return (1000, bono.get('displayName', bono['name']))
            
            # Ordenar la lista completa según prioridad
            bonos_soberano_ordenados = sorted(bonos_soberano, key=obtener_prioridad)
            
            # Agregar bonos T específicos que no estén en la lista (si es necesario)
            bonos_t_manuales = [
                {"name": "BCBA:T30E6", "displayName": "T30E6"},
                {"name": "BCBA:T30J6", "displayName": "T30J6"},
                {"name": "BCBA:T15E7", "displayName": "T15E7"},
                {"name": "BCBA:TY30P", "displayName": "TY30P"},
                {"name": "BCBA:TZXM6", "displayName": "TZXM6"},
                {"name": "BCBA:TZXD6", "displayName": "TZXD6"},
                {"name": "BCBA:TZXD7", "displayName": "TZXD7"},
                {"name": "BCBA:TZX28", "displayName": "TZX28"}
            ]
            
            # Verificar si los bonos T ya están en la lista, si no, agregarlos
            tickers_existentes = {normalizar_ticker(b['name']) for b in bonos_soberano_ordenados}
            for bono_t in bonos_t_manuales:
                ticker_t_norm = normalizar_ticker(bono_t['name'])
                if ticker_t_norm not in tickers_existentes:
                    # Insertar en la posición correcta según prioridad
                    prioridad_t = obtener_prioridad(bono_t)
                    insertado = False
                    for i, b in enumerate(bonos_soberano_ordenados):
                        if obtener_prioridad(b) > prioridad_t:
                            bonos_soberano_ordenados.insert(i, bono_t)
                            insertado = True
                            break
                    if not insertado:
                        bonos_soberano_ordenados.append(bono_t)
            
            # Construir JSON de símbolos insertando separador después de GD38
            symbols_groups = []
            
            # Encontrar la posición de GD38 e insertar separador antes de los bonos T
            bonos_finales = []
            encontrado_gd38 = False
            
            for bono in bonos_soberano_ordenados:
                ticker_norm = normalizar_ticker(bono['name'])
                display_norm = bono.get('displayName', '').upper()
                
                # Verificar si es GD38
                if 'GD38' in ticker_norm or 'GD38' in display_norm:
                    bonos_finales.append(bono)
                    encontrado_gd38 = True
                    # Insertar separador (símbolo vacío) después de GD38
                    bonos_finales.append({"name": "", "displayName": ""})
                else:
                    bonos_finales.append(bono)
            
            # Si no se encontró GD38, insertar separador antes del primer bono T
            if not encontrado_gd38:
                for i, bono in enumerate(bonos_finales):
                    ticker_norm = normalizar_ticker(bono['name'])
                    display_norm = bono.get('displayName', '').upper()
                    if any(ticker_t in ticker_norm or ticker_t in display_norm for ticker_t in bonos_t_especificos):
                        bonos_finales.insert(i, {"name": "", "displayName": ""})
                        break
            
            if bonos_finales:
                symbols_groups.append({
                    "name": "Bonos Soberanos",
                    "symbols": bonos_finales
                })
            
            # Widget Market Data - Ancho completo
            market_data_html = f"""
            <style>
                .tradingview-widget-container-right {{
                    font-size: 13.248px !important;
                }}
            </style>
            <div class="tradingview-widget-container tradingview-widget-container-right" style="height: 800px; width: 100%; font-size: 13.248px; margin-top: 0;">
                <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%; font-size: 13.248px;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js" async>
                {{
                "colorTheme": "light",
                "locale": "es",
                "largeChartUrl": "",
                "isTransparent": true,
                "showSymbolLogo": false,
                "backgroundColor": "transparent",
                "support_host": "https://www.tradingview.com",
                "width": "100%",
                "height": "800",
                "symbolsGroups": {json.dumps(symbols_groups, ensure_ascii=False)}
                }}
                </script>
                <script>
                    // NOTA IMPORTANTE: TradingView renderiza el contenido en un iframe de otro dominio (tradingview.com).
                    // Por políticas de seguridad del navegador (CORS - Cross-Origin Resource Sharing), 
                    // NO ES POSIBLE acceder al contenido del iframe desde JavaScript.
                    // Por lo tanto, ocultar la columna "Apertura" NO ES TÉCNICAMENTE POSIBLE.
                    // TradingView no proporciona una opción de configuración para ocultar columnas específicas.
                    // El código a continuación intentará ocultarla, pero fallará silenciosamente debido a CORS.
                    
                    function modificarColumnas() {{
                        var container = document.querySelector('.tradingview-widget-container-right');
                        if (!container) return;
                        
                        var iframe = container.querySelector('iframe');
                        if (!iframe) {{
                            setTimeout(modificarColumnas, 500);
                            return;
                        }}
                        
                        try {{
                            var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                            if (!iframeDoc) {{
                                setTimeout(modificarColumnas, 500);
                                return;
                            }}
                            
                            var tables = iframeDoc.querySelectorAll('table');
                            tables.forEach(function(table) {{
                                var headers = table.querySelectorAll('th');
                                headers.forEach(function(th, index) {{
                                    var text = th.textContent || th.innerText || '';
                                    var colIndex = index + 1;
                                    
                                    // Reducir ancho de columna Nombre (primera columna)
                                    if (text.includes('Nombre') || text.includes('Name') || index === 0) {{
                                        table.querySelectorAll('th:nth-child(' + colIndex + '), td:nth-child(' + colIndex + ')').forEach(function(el) {{
                                            el.style.maxWidth = '80px';
                                            el.style.width = '80px';
                                            el.style.minWidth = '80px';
                                            el.style.overflow = 'hidden';
                                            el.style.textOverflow = 'ellipsis';
                                            el.style.whiteSpace = 'nowrap';
                                        }});
                                    }}
                                    
                                    // Intentar ocultar columna Apertura
                                    if (text.includes('Apertura') || text.includes('Open') || text.includes('Abrir')) {{
                                        table.querySelectorAll('th:nth-child(' + colIndex + '), td:nth-child(' + colIndex + ')').forEach(function(el) {{
                                            el.style.display = 'none';
                                        }});
                                    }}
                                }});
                            }});
                        }} catch(e) {{
                            // Esto fallará debido a CORS - es el comportamiento esperado
                            // No se puede acceder al contenido del iframe de TradingView por políticas de seguridad
                        }}
                    }}
                    
                    // Intentar múltiples veces (aunque no funcionará debido a CORS)
                    setTimeout(modificarColumnas, 1000);
                    setTimeout(modificarColumnas, 2000);
                    setTimeout(modificarColumnas, 3000);
                </script>
            </div>
            """
            st.components.v1.html(market_data_html, height=800)
    
    # S4 (Indices) - Prioridad más alta (después de S3)
    elif st.session_state.get('indices_activo', False):
        # Ocultar sidebar cuando Indices está activo
        st.markdown("""
        <style>
            .stSidebar {
                display: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Widget Ticket Tape de TradingView con acciones del Merval
        # Acciones principales del índice Merval de Argentina
        symbols_merval = [
            "BCBA:GGAL",  # Grupo Financiero Galicia
            "BCBA:PAMP",  # Pampa Energía
            "BCBA:YPF",   # YPF
            "BCBA:BBAR",  # Banco BBVA Argentina
            "BCBA:BMA",   # Banco Macro
            "BCBA:CRESY", # Cresud
            "BCBA:LOMA",  # Loma Negra
            "BCBA:MIRG",  # Mirgor
            "BCBA:PGR",   # Phoenix Global Resources
            "BCBA:TX",    # Ternium Argentina
            "BCBA:TGSU2", # Transportadora de Gas del Sur
            "BCBA:VALO"   # Valores
        ]
        
        ticket_tape_html = f"""
        <div class="tradingview-widget-container" style="width: 100%; height: 100px;">
            <div class="tradingview-widget-container__widget" style="width: 100%; height: 100px;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
            {{
            "symbols": {json.dumps([{{"proName": symbol, "title": symbol.split(':')[1] if ':' in symbol else symbol}} for symbol in symbols_merval], ensure_ascii=False)},
            "showSymbolLogo": true,
            "colorTheme": "light",
            "isTransparent": true,
            "displayMode": "adaptive",
            "locale": "es",
            "backgroundColor": "transparent"
            }}
            </script>
        </div>
        """
        st.components.v1.html(ticket_tape_html, height=100)
    
    # S2 (Calculadora de Flujos) - Prioridad alta (solo si mercados e indices no están activos)
    elif st.session_state.get('flujos_bono_seleccionado') and not st.session_state.get('mercados_activo', False) and not st.session_state.get('indices_activo', False):
        # Inicializar lista de bonos seleccionados si no existe
        if 'flujos_bonos_seleccionados' not in st.session_state:
            st.session_state.flujos_bonos_seleccionados = []
        
        # Agregar bono actual a la lista si no está ya
        bono_actual = st.session_state.get('flujos_bono_seleccionado')
        if bono_actual and bono_actual not in [b['nombre'] for b in st.session_state.flujos_bonos_seleccionados]:
            # Encontrar el bono en la lista completa de bonos (no solo los filtrados)
            bono_info = next((bono for bono in bonos if bono['nombre'] == bono_actual), None)
            if bono_info:
                st.session_state.flujos_bonos_seleccionados.append({
                    'nombre': bono_actual,
                    'nominales': '',
                    'precio': '',
                    'info': bono_info
                })
        
        # Mostrar lista de bonos seleccionados con recuadro transparente
        st.markdown("""
        <div style="
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 8px 0 20px 0;
            background-color: transparent;
            text-align: center;
            font-weight: 600;
            color: #333;
        ">
            Bonos Seleccionados para Flujos
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.flujos_bonos_seleccionados:
            for i, bono in enumerate(st.session_state.flujos_bonos_seleccionados):
                # Layout con 6 columnas para incluir precio
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{bono['nombre']}**")
                
                with col2:
                    st.write("Nominales:")
                
                with col3:
                    # Usar text_input para permitir campo vacío
                    nominales_text = st.text_input(
                        "",
                        value=str(bono['nominales']) if bono['nominales'] != '' else "",
                        key=f"nominales_{i}",
                        label_visibility="collapsed"
                    )
                    # Convertir a número y actualizar session_state
                    try:
                        nominales = int(nominales_text) if nominales_text else 0
                    except ValueError:
                        nominales = 0
                    st.session_state.flujos_bonos_seleccionados[i]['nominales'] = nominales
                
                with col4:
                    st.write("Precio:")
                
                with col5:
                    # Input para precio del bono en base 100
                    precio_key = f"precio_flujo_{i}"
                    
                    # Inicializar precio en session_state si no existe
                    if precio_key not in st.session_state:
                        precio_actual = bono.get('precio', 0.0)
                        if precio_actual and precio_actual > 0:
                            st.session_state[precio_key] = float(precio_actual)
                        else:
                            st.session_state[precio_key] = 100.0  # Valor por defecto en base 100
                    
                    # Usar number_input para validación automática
                    precio = st.number_input(
                        "",
                        min_value=0.0,
                        max_value=200.0,
                        step=0.01,
                        format="%.2f",
                        key=precio_key,
                        label_visibility="collapsed"
                    )
                    
                    # Actualizar session_state
                    st.session_state.flujos_bonos_seleccionados[i]['precio'] = precio
                
                with col6:
                    if st.button("🗑️", key=f"remove_{i}", help="Eliminar bono"):
                        st.session_state.flujos_bonos_seleccionados.pop(i)
                        st.rerun()
            
            # Botón para agregar más bonos
            st.markdown("---")
            
            # Botón para calcular flujos
            if st.button("Calcular Flujos", type="secondary", use_container_width=True):
                st.session_state.flujos_calcular = True
            
            # Mostrar tarjetas de métricas si se está calculando
            if st.session_state.get('flujos_calcular', False):
                # Obtener fecha actual
                fecha_actual = pd.Timestamp.now().date()
                
                st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
                
                # Primera fila de métricas
                col1, col2, col3, col4, col5 = st.columns(5)
                
                # Calcular métricas
                cantidad_bonos = len(st.session_state.flujos_bonos_seleccionados)
                total_intereses = 0
                total_amortizaciones = 0
                total_general = 0
                cupon_ponderado = 0.0
                total_nominales = 0
                suma_cupones_ponderados = 0
                
                # Calcular totales de los flujos y cupón ponderado
                if st.session_state.flujos_bonos_seleccionados:
                    for bono_item in st.session_state.flujos_bonos_seleccionados:
                        if bono_item['nominales'] > 0:
                            bono_info = bono_item['info']
                            nominales = bono_item['nominales']
                            
                            # Calcular cupón ponderado
                            # Detectar si el bono tiene cupón variable
                            cupones_unicos = set()
                            for flujo in bono_info['flujos']:
                                fecha_flujo = flujo['fecha']
                                if hasattr(fecha_flujo, 'date'):
                                    fecha_flujo = fecha_flujo.date()
                                
                                if fecha_flujo >= fecha_actual:
                                    cupones_unicos.add(flujo['cupon_vigente'])
                            
                            # Si hay múltiples cupones, calcular cupón ponderado del bono
                            if len(cupones_unicos) > 1:
                                # Bono con cupón variable - calcular cupón ponderado
                                suma_cupones_bono = 0
                                total_flujos_bono = 0
                                for flujo in bono_info['flujos']:
                                    fecha_flujo = flujo['fecha']
                                    if hasattr(fecha_flujo, 'date'):
                                        fecha_flujo = fecha_flujo.date()
                                    
                                    if fecha_flujo >= fecha_actual:
                                        suma_cupones_bono += flujo['cupon_vigente']
                                        total_flujos_bono += 1
                                
                                if total_flujos_bono > 0:
                                    cupon_ponderado_bono = suma_cupones_bono / total_flujos_bono
                                else:
                                    cupon_ponderado_bono = bono_info.get('tasa_cupon', 0)
                            else:
                                # Bono con cupón fijo
                                cupon_ponderado_bono = bono_info.get('tasa_cupon', 0)
                            
                            suma_cupones_ponderados += cupon_ponderado_bono * nominales
                            total_nominales += nominales
                            
                            for flujo in bono_info['flujos']:
                                fecha_cupon = flujo['fecha']
                                if hasattr(fecha_cupon, 'date'):
                                    fecha_cupon = fecha_cupon.date()
                                
                                if fecha_cupon >= fecha_actual:
                                    intereses = flujo['cupon'] * nominales / 100
                                    amortizaciones = flujo['capital'] * nominales / 100
                                    total = flujo['total'] * nominales / 100
                                    
                                    total_intereses += intereses
                                    total_amortizaciones += amortizaciones
                                    total_general += total
                
                # Calcular cupón ponderado final
                if total_nominales > 0:
                    cupon_ponderado = suma_cupones_ponderados / total_nominales
                
                with col1:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-label">Cantidad Bonos</div>
                        <div class="metric-value">{cantidad_bonos}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-label">Total Intereses</div>
                        <div class="metric-value">${formatear_numero(total_intereses, 2)}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-label">Total Amortizaciones</div>
                        <div class="metric-value">${formatear_numero(total_amortizaciones, 2)}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f'''
                    <div class="metric-card">
                        <div class="metric-label">Total</div>
                        <div class="metric-value">${formatear_numero(total_general, 2)}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                with col5:
                    # Calcular TIR solo si todos los bonos tienen precio
                    tir_calculada = None
                    todos_tienen_precio = True
                    
                    if st.session_state.flujos_bonos_seleccionados:
                        # Verificar que todos los bonos tengan precio
                        for bono_item in st.session_state.flujos_bonos_seleccionados:
                            if bono_item['nominales'] > 0 and (not bono_item.get('precio') or bono_item.get('precio', 0) <= 0):
                                todos_tienen_precio = False
                                break
                        
                        if todos_tienen_precio:
                            # Preparar datos para TIR: fechas y valores
                            fechas_tir = []
                            valores_tir = []
                            
                            # Agregar valor actual (inversión inicial)
                            # El precio se ingresa en base 100, se convierte a base 1 dividiendo por 100
                            total_inversion = 0
                            for bono_item in st.session_state.flujos_bonos_seleccionados:
                                if bono_item['nominales'] > 0 and bono_item.get('precio', 0) > 0:
                                    precio_base1 = bono_item['precio'] / 100  # Convertir de base 100 a base 1
                                    total_inversion += bono_item['nominales'] * precio_base1
                            
                            if total_inversion > 0:
                                fechas_tir.append(fecha_actual)
                                valores_tir.append(-total_inversion)  # Negativo (inversión)
                            
                            # Agregar flujos futuros
                            for bono_item in st.session_state.flujos_bonos_seleccionados:
                                if bono_item['nominales'] > 0:
                                    bono_info = bono_item['info']
                                    nominales = bono_item['nominales']
                                    
                                    for flujo in bono_info['flujos']:
                                        fecha_flujo = flujo['fecha']
                                        if hasattr(fecha_flujo, 'date'):
                                            fecha_flujo = fecha_flujo.date()
                                        
                                        if fecha_flujo >= fecha_actual:
                                            fechas_tir.append(fecha_flujo)
                                            total_flujo = flujo['total'] * nominales / 100
                                            valores_tir.append(total_flujo)  # Positivo (retorno)
                            
                            # Calcular TIR usando la misma función que la calculadora de rendimientos
                            if len(valores_tir) > 1:
                                try:
                                    # Preparar datos para calcular_ytm
                                    precio_dirty = -valores_tir[0]  # Valor actual (positivo)
                                    flujos = valores_tir[1:]  # Flujos futuros
                                    fechas = fechas_tir[1:]  # Fechas futuras
                                    
                                    # Usar la función calcular_ytm existente
                                    tir_efectiva = calcular_ytm(
                                        precio_dirty=precio_dirty,
                                        flujos=flujos,
                                        fechas=fechas,
                                        fecha_liquidacion=fecha_actual,
                                        base_calculo="ACT/365",
                                        periodicidad=2
                                    )
                                    
                                    # Convertir TIR efectiva a TIR semestral
                                    # Fórmula: TIR_semestral = 2 * ((1 + TIR_efectiva)^(1/2) - 1)
                                    tir_calculada = 2 * ((1 + tir_efectiva) ** (1/2) - 1)
                                    
                                except Exception as e:
                                    tir_calculada = 0.0
                    
                    # Mostrar TIR o valor vacío
                    if tir_calculada is not None:
                        st.markdown(f'''
                        <div class="metric-card">
                            <div class="metric-label">TIR Semestral</div>
                            <div class="metric-value">{tir_calculada:.2%}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div class="metric-card">
                            <div class="metric-label">TIR Semestral</div>
                            <div class="metric-value">-</div>
                        </div>
                        ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar tabla de flujos si se presionó calcular
            if st.session_state.get('flujos_calcular', False):
                
                # Obtener fecha actual
                fecha_actual = pd.Timestamp.now().date()
                
                # Recopilar todos los flujos de todos los bonos seleccionados
                todos_flujos = []
                
                for bono_item in st.session_state.flujos_bonos_seleccionados:
                    if bono_item['nominales'] > 0:  # Solo si tiene nominales
                        bono_info = bono_item['info']
                        nominales = bono_item['nominales']
                        
                        # Calcular flujos para este bono (similar a S1)
                        flujos_bono = []
                        fechas_bono = []
                        
                        # Obtener fechas de cupones y amortizaciones
                        for flujo in bono_info['flujos']:
                            fecha_cupon = flujo['fecha']
                            if hasattr(fecha_cupon, 'date'):
                                fecha_cupon = fecha_cupon.date()
                            
                            if fecha_cupon >= fecha_actual:  # Solo fechas futuras
                                flujos_bono.append({
                                    'fecha': fecha_cupon,
                                    'activo': bono_item['nombre'],
                                    'cupon': flujo['cupon_vigente'],
                                    'intereses': round(flujo['cupon'] * nominales / 100, 2),
                                    'amortizaciones': round(flujo['capital'] * nominales / 100, 2),
                                    'total': round(flujo['total'] * nominales / 100, 2)
                                })
                                fechas_bono.append(fecha_cupon)
                        
                        todos_flujos.extend(flujos_bono)
                
                if todos_flujos:
                    # Calcular total de inversión (nominales × precio en base 1)
                    # El precio se ingresa en base 100, se convierte a base 1 dividiendo por 100
                    total_inversion = 0
                    for bono_item in st.session_state.flujos_bonos_seleccionados:
                        if bono_item['nominales'] > 0 and bono_item.get('precio', 0) > 0:
                            precio_base1 = bono_item['precio'] / 100  # Convertir de base 100 a base 1
                            total_inversion += bono_item['nominales'] * precio_base1
                    
                    # Agregar fila inicial con fecha actual y total de inversión
                    fila_inicial = {
                        'fecha': fecha_actual,
                        'activo': 'Valor Actual',
                        'cupon': 0.0,
                        'intereses': 0.0,
                        'amortizaciones': 0.0,
                        'total': total_inversion
                    }
                    
                    # Insertar fila inicial al principio
                    todos_flujos.insert(0, fila_inicial)
                    
                    # Ordenar por fecha
                    todos_flujos.sort(key=lambda x: x['fecha'])
                    
                    # Crear DataFrame
                    df_flujos = pd.DataFrame(todos_flujos)
                    
                    # Formatear fechas a DD/MM/YY
                    df_flujos['fecha'] = pd.to_datetime(df_flujos['fecha']).dt.strftime('%d/%m/%y')
                    
                    # Formatear números con separadores de miles
                    df_flujos['intereses'] = df_flujos['intereses'].apply(lambda x: formatear_numero(x, 2))
                    df_flujos['amortizaciones'] = df_flujos['amortizaciones'].apply(lambda x: formatear_numero(x, 2))
                    df_flujos['total'] = df_flujos['total'].apply(lambda x: formatear_numero(x, 2))
                    
                    # Formatear cupón como porcentaje con 2 decimales
                    df_flujos['cupon'] = df_flujos['cupon'].apply(lambda x: f"{x*100:.2f}%")
                    
                    # Mostrar tabla de flujos con alineación a la derecha
                    st.markdown("""
                    <style>
                    /* Ocultar columna de numeración */
                    .stTable td:first-child, .stTable th:first-child {
                        display: none !important;
                    }
                    /* Alinear columnas numéricas a la derecha */
                    .stTable td:nth-child(4), .stTable td:nth-child(5), .stTable td:nth-child(6), .stTable td:nth-child(7) {
                        text-align: right !important;
                    }
                    .stTable th:nth-child(4), .stTable th:nth-child(5), .stTable th:nth-child(6), .stTable th:nth-child(7) {
                        text-align: right !important;
                    }
                    /* Forzar alineación específica para columna Total */
                    .stTable td:last-child {
                        text-align: right !important;
                    }
                    .stTable th:last-child {
                        text-align: right !important;
                    }
                    .stTable th {
                        text-transform: capitalize !important;
                    }
                    /* Forzar alineación a la izquierda para columna Activo (columna 3) */
                    .stTable td:nth-child(3), .stTable th:nth-child(3) {
                        text-align: left !important;
                    }
                    /* Asegurar que todas las columnas no numéricas estén a la izquierda */
                    .stTable td:nth-child(2), .stTable th:nth-child(2) {
                        text-align: left !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.table(df_flujos)
                    
                    # Gráfico de flujos por trimestre
                    st.markdown("---")
                    st.markdown("### Flujos por Trimestre (Próximos 5 Años)")
                    
                    # Preparar datos para el gráfico
                    df_flujos_copy = df_flujos.copy()
                    df_flujos_copy['fecha'] = pd.to_datetime(df_flujos_copy['fecha'])
                    
                    # Filtrar solo flujos futuros (excluir fila inicial)
                    df_futuros = df_flujos_copy[df_flujos_copy['activo'] != 'Valor Actual'].copy()
                    
                    if not df_futuros.empty:
                        # Crear columna de trimestre
                        df_futuros['año'] = df_futuros['fecha'].dt.year
                        df_futuros['trimestre'] = df_futuros['fecha'].dt.quarter
                        df_futuros['trimestre_label'] = df_futuros['trimestre'].astype(str) + 'Q' + df_futuros['año'].astype(str).str[2:]
                        
                        # Asegurar que las columnas sean numéricas
                        df_futuros['intereses'] = pd.to_numeric(df_futuros['intereses'], errors='coerce').fillna(0)
                        df_futuros['amortizaciones'] = pd.to_numeric(df_futuros['amortizaciones'], errors='coerce').fillna(0)
                        
                        # Agrupar por trimestre
                        df_trimestral = df_futuros.groupby(['año', 'trimestre', 'trimestre_label']).agg({
                            'intereses': 'sum',
                            'amortizaciones': 'sum'
                        }).reset_index()
                        
                        # Crear etiqueta completa para el eje X
                        df_trimestral['periodo'] = df_trimestral['trimestre'].astype(str) + 'Q' + df_trimestral['año'].astype(str).str[2:]
                        
                        # Filtrar solo los próximos 5 años
                        año_actual = pd.Timestamp.now().year
                        df_trimestral = df_trimestral[df_trimestral['año'] <= año_actual + 5]
                        
                        # Asegurar que los valores sean numéricos
                        df_trimestral['intereses'] = pd.to_numeric(df_trimestral['intereses'], errors='coerce').fillna(0)
                        df_trimestral['amortizaciones'] = pd.to_numeric(df_trimestral['amortizaciones'], errors='coerce').fillna(0)
                        
                        if not df_trimestral.empty:
                            # Crear gráfico de barras apiladas
                            fig = go.Figure()
                            
                            # Agregar barras de intereses
                            fig.add_trace(go.Bar(
                                name='Intereses',
                                x=df_trimestral['periodo'],
                                y=df_trimestral['intereses'],
                                marker_color='#87CEEB',  # Celeste claro
                                hovertemplate='<b>%{x}</b><br>Intereses: $%{y:,.2f}<extra></extra>'
                            ))
                            
                            # Agregar barras de amortizaciones
                            fig.add_trace(go.Bar(
                                name='Amortizaciones',
                                x=df_trimestral['periodo'],
                                y=df_trimestral['amortizaciones'],
                                marker_color='#708090',  # Gris azulado
                                hovertemplate='<b>%{x}</b><br>Amortizaciones: $%{y:,.2f}<extra></extra>'
                            ))
                            
                            # Configurar layout
                            fig.update_layout(
                                xaxis_title='Trimestre',
                                yaxis_title='Monto ($)',
                                barmode='stack',
                                height=500,
                                showlegend=True,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                hovermode='closest'
                            )
                            
                            # Formatear eje Y como moneda
                            fig.update_layout(
                                yaxis=dict(
                                    tickformat='$,.0f'
                                )
                            )
                            
                            # Mostrar gráfico
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No hay flujos futuros en los próximos 5 años")
                    else:
                        st.info("No hay flujos futuros para mostrar")
                else:
                    st.warning("⚠️ No se encontraron flujos futuros para los bonos seleccionados")
        else:
            st.info("🔧 CALCULADORA DE FLUJOS - Pantalla lista para nuevas funcionalidades")
    
    # S1 (Calculadora de Rendimientos) - Mostrar cuando hay bono seleccionado (sin necesidad de calcular)
    elif st.session_state.bono_seleccionado and not st.session_state.get('flujos_bono_seleccionado') and not st.session_state.get('mercados_activo', False) and not st.session_state.get('indices_activo', False):
        # Obtener el bono actual del session_state
        bono_actual = next(bono for bono in bonos_filtrados if bono['nombre'] == st.session_state.bono_seleccionado)
        
        # Layout principal
        col1, col2 = st.columns([1, 2])
        
        # COLUMNA IZQUIERDA - INPUTS Y BOTONES
        with col1:
            # Solo mostrar inputs si hay bono seleccionado Y NO hay bono en S2
            if st.session_state.bono_seleccionado and not st.session_state.get('flujos_bono_seleccionado'):
                # Encontrar el bono seleccionado
                bono_actual_main = next(bono for bono in bonos_filtrados if bono['nombre'] == st.session_state.bono_seleccionado)
                
                # Crear una key única basada en el bono para que el input se resetee al cambiar de bono
                precio_key_main = f"precio_dirty_{st.session_state.bono_seleccionado}"
                
                # Inicializar el precio en session_state si no existe
                if precio_key_main not in st.session_state:
                    # Intentar obtener precio desde PyOBD (BYMA Data)
                    ticker = bono_actual_main.get('ticker', '').strip()
                    precio_byma = None
                    
                    if ticker and ticker != '' and ticker != 'SPX500':
                        precio_byma = obtener_precio_byma(ticker)
                    
                    # Usar precio de BYMA si está disponible, sino usar 100.0 como default
                    if precio_byma and precio_byma > 0:
                        st.session_state[precio_key_main] = precio_byma
                    else:
                        st.session_state[precio_key_main] = 100.0
                
                # Inputs con ancho reducido al 70%
                col_input_left, col_input_center, col_input_right = st.columns([0.15, 0.7, 0.15])
                
                with col_input_center:
                    fecha_liquidacion = st.date_input(
                        "Fecha de Liquidación",
                        value=get_next_business_day(),
                        format="DD/MM/YYYY",
                        key="fecha_liquidacion_main"
                    )
                    
                    # Usar solo la key sin value, Streamlit manejará el valor automáticamente desde session_state
                    precio_dirty = st.number_input(
                        "Precio Dirty (base 100)",
                        min_value=0.0,
                        max_value=200.0,
                        step=0.01,
                        format="%.2f",
                        key=precio_key_main,
                        help="💡 El precio se obtiene automáticamente desde BYMA (si está disponible). Puedes modificarlo manualmente si lo deseas."
                    )
        
                # Botones de cálculo y volver con ancho reducido al 70%
                col_btn_left, col_btn_center, col_btn_right = st.columns([0.15, 0.7, 0.15])
                
                with col_btn_center:
                    col_calc, col_volver = st.columns(2)
                    
                    with col_calc:
                        if st.button("Calcular", type="secondary", use_container_width=True, key="calcular_main"):
                            st.session_state.calcular = True
                    
                    with col_volver:
                        if st.button("Volver", type="secondary", use_container_width=True, key="volver_main"):
                            # Resetear TODAS las selecciones - estado inicial completo
                            st.session_state.calcular = False
                            st.session_state.bono_seleccionado = None
                            st.session_state.tipo_seleccionado = "Seleccione un Tipo"
                            
                            # Limpiar keys de precio
                            keys_to_delete = [key for key in st.session_state.keys() if key.startswith('precio_dirty_')]
                            for key in keys_to_delete:
                                del st.session_state[key]
                            
                            # Limpiar TODAS las selecciones de flujos
                            st.session_state.flujos_bono_seleccionado = None
                            st.session_state.flujos_tipo_seleccionado = "Seleccione un Tipo"
                            st.session_state.flujos_calcular = False
                            if 'flujos_bonos_seleccionados' in st.session_state:
                                del st.session_state['flujos_bonos_seleccionados']
                            
                            # Incrementar claves únicas para forzar reset de selectbox
                            st.session_state.tipo_selectbox_key += 1
                            st.session_state.flujos_tipo_selectbox_key += 1
                            
                            # Limpiar TODOS los selectbox para forzar reset
                            if 'bono_selectbox' in st.session_state:
                                del st.session_state['bono_selectbox']
                            if 'flujos_bono_selectbox' in st.session_state:
                                del st.session_state['flujos_bono_selectbox']
                            
                            st.rerun()
                
                # Mostrar información del bono seleccionado con el mismo centrado que los inputs
                col_info_left, col_info_center, col_info_right = st.columns([0.15, 0.7, 0.15])
                
                with col_info_center:
                    st.markdown("---")
                    st.markdown("### Información del Bono")
                    
                    # Mapear periodicidad a texto
                    periodicidad_texto_info = {
                        1: "anual",
                        2: "semestral", 
                        3: "trimestral",
                        4: "trimestral",
                        6: "bimestral",
                        12: "mensual"
                    }.get(bono_actual_main['periodicidad'], f"{bono_actual_main['periodicidad']} veces al año")
                    
                    # Calcular fecha de vencimiento
                    fecha_vencimiento_info = encontrar_fecha_vencimiento(bono_actual_main['flujos'])
                    
                    # Calcular cupón vigente basado en la fecha actual
                    from datetime import date
                    cupon_vigente_actual_info = encontrar_cupon_vigente(date.today(), bono_actual_main['flujos'])
                    
                    # Información del bono con mejor formato y mayor interlineado
                    st.markdown(f"""
                    <div style="line-height: 1.8; margin: 0.5rem 0; padding: 0;">
                        <p style="margin: 0.5rem 0; padding: 0.2rem 0;"><strong>Nombre:</strong> {bono_actual_main['nombre']}</p>
                        <p style="margin: 0.5rem 0; padding: 0.2rem 0;"><strong>Vencimiento:</strong> {fecha_vencimiento_info.strftime('%d/%m/%Y') if fecha_vencimiento_info else 'N/A'}</p>
                        <p style="margin: 0.5rem 0; padding: 0.2rem 0;"><strong>Tasa de cupón:</strong> {cupon_vigente_actual_info:.2%}</p>
                        <p style="margin: 0.5rem 0; padding: 0.2rem 0;"><strong>Periodicidad:</strong> {periodicidad_texto_info}</p>
                        <p style="margin: 0.5rem 0; padding: 0.2rem 0;"><strong>Base de cálculo:</strong> {bono_actual_main['base_calculo']}</p>
                        <p style="margin: 0.5rem 0; padding: 0.2rem 0;"><strong>Ticker:</strong> {bono_actual_main['ticker']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # COLUMNA DERECHA - RESULTADOS (solo si se presionó Calcular)
        with col2:
            if st.session_state.calcular:
                # Obtener fecha_liquidacion y precio_dirty desde session_state
                fecha_liquidacion = st.session_state.get('fecha_liquidacion_main', get_next_business_day())
                precio_dirty = st.session_state.get('precio_dirty_main', 100.0)
        
        # Convertir fecha_liquidacion a datetime para comparación
        fecha_liquidacion_dt = pd.to_datetime(fecha_liquidacion)
        
        # Calcular flujos de caja
        flujos = []
        fechas = []
        flujos_capital = []
        
        for flujo in bono_actual['flujos']:
            if flujo['fecha'] > fecha_liquidacion_dt:
                flujos.append(flujo['total'])
                fechas.append(flujo['fecha'])
                flujos_capital.append(flujo['capital'])
        
        if not flujos:
            st.error("❌ No hay flujos futuros para calcular")
        else:
            # Continuar con los cálculos solo si hay flujos
            # Calcular YTM
            ytm_efectiva = calcular_ytm(
                precio_dirty,
                flujos,
                fechas,
                fecha_liquidacion,
                bono_actual['base_calculo'],
                bono_actual['periodicidad']
            )
        
        # Calcular YTM anualizada según periodicidad
        ytm_anualizada = bono_actual['periodicidad'] * ((1 + ytm_efectiva) ** (1 / bono_actual['periodicidad']) - 1)
        
        # Calcular duración Macaulay
        duracion_macaulay = calcular_duracion_macaulay(
            flujos,
            fechas,
            fecha_liquidacion,
            ytm_efectiva,
            bono_actual['base_calculo']
        )
        
        # Calcular duración modificada
        duracion_modificada = calcular_duracion_modificada(
            duracion_macaulay,
            ytm_anualizada / bono_actual['periodicidad'],
            bono_actual['periodicidad']
        )
        
        # Calcular capital residual
        capital_residual = 100 - sum([flujo['capital'] for flujo in bono_actual['flujos'] if flujo['fecha'] <= fecha_liquidacion_dt])
        
        # Calcular intereses corridos
        fecha_ultimo_cupon = encontrar_ultimo_cupon(fecha_liquidacion_dt, [flujo['fecha'] for flujo in bono_actual['flujos']])
        if fecha_ultimo_cupon:
            intereses_corridos = calcular_intereses_corridos(
                fecha_liquidacion,
                fecha_ultimo_cupon,
                bono_actual['tasa_cupon'],
                capital_residual,
                bono_actual['base_calculo']
            )
        else:
            intereses_corridos = 0
        
        # Calcular precio limpio
        precio_limpio = precio_dirty - intereses_corridos
        
        # Calcular vida media
        vida_media = calcular_vida_media(
            flujos_capital,
            fechas,
            fecha_liquidacion,
            bono_actual['base_calculo']
        )
        
        # Calcular paridad
        valor_tecnico = capital_residual + intereses_corridos
        paridad = precio_limpio / valor_tecnico if valor_tecnico > 0 else 0
        
        # Encontrar próximo cupón
        proximo_cupon = encontrar_proximo_cupon(fecha_liquidacion_dt, [flujo['fecha'] for flujo in bono_actual['flujos']])
        
        # Calcular cupón vigente
        cupon_vigente = encontrar_cupon_vigente(fecha_liquidacion, bono_actual['flujos'])
        
        # Mapear periodicidad a texto
        periodicidad_texto = {
            1: "anual",
            2: "semestral", 
            3: "trimestral",
            4: "trimestral",
            6: "bimestral",
            12: "mensual"
            }.get(bono_actual['periodicidad'], f"{bono_actual['periodicidad']} veces al año")
        
        # Métricas principales
        st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
        
        # Primera fila
        col1_1, col1_2, col1_3, col1_4 = st.columns(4)
        with col1_1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Precio Limpio</div>
                <div class="metric-value">{formatear_numero(precio_limpio, 4)}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col1_2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Intereses Corridos</div>
                <div class="metric-value">{formatear_numero(intereses_corridos, 4)}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col1_3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Capital Residual</div>
                <div class="metric-value">{formatear_numero(capital_residual, 2)}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col1_4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Cupón Vigente</div>
                <div class="metric-value">{cupon_vigente:.2%}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Segunda fila
        st.markdown('<div class="metrics-row">', unsafe_allow_html=True)
        col2_1, col2_2, col2_3, col2_4 = st.columns(4)
        
        with col2_1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">TIR Efectiva</div>
                <div class="metric-value">{ytm_efectiva:.4%}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2_2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">TIR {periodicidad_texto.title()}</div>
                <div class="metric-value">{ytm_anualizada:.4%}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2_3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Duración Modificada</div>
                <div class="metric-value">{formatear_numero(duracion_modificada, 2)} años</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2_4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Duración Macaulay</div>
                <div class="metric-value">{formatear_numero(duracion_macaulay, 2)} años</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tercera fila
        st.markdown('<div class="metrics-row">', unsafe_allow_html=True)
        col3_1, col3_2, col3_3, col3_4 = st.columns(4)
        
        with col3_1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Valor Técnico</div>
                <div class="metric-value">{formatear_numero(valor_tecnico, 4)}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3_2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Paridad</div>
                <div class="metric-value">{formatear_numero(paridad, 4)}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3_3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Próximo Cupón</div>
                <div class="metric-value">{proximo_cupon.strftime('%d/%m/%Y') if proximo_cupon else 'N/A'}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3_4:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Vida Media</div>
                <div class="metric-value">{formatear_numero(vida_media, 2)} años</div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SECCIÓN FLUJO DE FONDOS - FORMATO MEJORADO
        st.markdown("## Flujo de Fondos")
        
        # Crear DataFrame con formato mejorado
        # Primera fila: fecha de liquidación y precio pagado (negativo)
        fechas_con_liquidacion = [fecha_liquidacion] + fechas
        capital_con_liquidacion = [""] + [formatear_numero(c, 1) if c > 0 else "" for c in flujos_capital]
        cupon_con_liquidacion = [""] + [formatear_numero(f-c, 1) for f, c in zip(flujos, flujos_capital)]
        total_con_liquidacion = [f"-{formatear_numero(precio_dirty, 1)}"] + [formatear_numero(f, 1) for f in flujos]
        
        df_simple = pd.DataFrame({
            'Fecha': [f.strftime('%d/%m/%Y') for f in fechas_con_liquidacion],
            'Capital': capital_con_liquidacion,
            'Cupón': cupon_con_liquidacion,
            'Total': total_con_liquidacion
        })
        
        # CSS para mejorar la visualización de la tabla
        st.markdown("""
        <style>
        .stTable {
            border: none !important;
            border-radius: 8px !important;
            background-color: #f8f9fa !important;
        }
        .stTable table {
            width: 100% !important;
            border-collapse: collapse !important;
            font-size: 12px !important;
        }
        .stTable th {
            background-color: #64748b !important;
            color: white !important;
            font-weight: bold !important;
            padding: 5px 3px !important;
            text-align: center !important;
            border: 1px solid #64748b !important;
            height: 22px !important;
        }
        .stTable td {
            padding: 3px 3px !important;
            text-align: center !important;
            border: 1px solid #ddd !important;
            background-color: white !important;
            color: black !important;
            height: 18px !important;
        }
        .stTable tbody tr {
            height: 18px !important;
        }
        /* Ocultar la primera columna (índice) */
        .stTable table tr th:first-child,
        .stTable table tr td:first-child {
            display: none !important;
        }
        
        /* Prevenir scroll automático al hacer clic en Calcular */
        .main {
            scroll-behavior: auto !important;
        }
        
        /* Mantener la sección de resultados visible */
        .main .stColumn:first-child {
            position: sticky !important;
            top: 0 !important;
            z-index: 10 !important;
        }
        
        .metrics-grid {
            position: relative !important;
            z-index: 5 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Mostrar tabla con formato mejorado
        st.table(df_simple)
        
        # Gráfico del bono seleccionado - Ancho completo (minigráfico expandido)
        bono_avanzado_html = f"""
        <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
            <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
            {{
            "symbol": "{bono_actual['ticker']}",
            "width": "100%",
            "height": "500",
            "locale": "es",
            "dateRange": "12M",
            "colorTheme": "light",
            "isTransparent": true,
            "autosize": false,
            "largeChartUrl": "",
            "hideTopToolbar": true,
            "hideLegend": false,
            "saveImage": false
            }}
            </script>
        </div>
        """
        st.components.v1.html(bono_avanzado_html, height=500)
        
        # JavaScript para prevenir scroll automático al hacer clic en Calcular
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Interceptar clics en el botón Calcular
            document.addEventListener('click', function(e) {
                // Verificar si es el botón Calcular
                if (e.target.matches('button[data-testid="baseButton-primary"]') || 
                    e.target.textContent.includes('Calcular')) {
                    
                    // Prevenir el comportamiento por defecto
                    e.preventDefault();
                    
                    // Forzar scroll hacia arriba después de un pequeño delay
                    setTimeout(function() {
                        window.scrollTo({
                            top: 0,
                            left: 0,
                            behavior: 'auto'
                        });
                    }, 100);
                }
            });
            
            // También interceptar el evento de submit del formulario
            document.addEventListener('submit', function(e) {
                e.preventDefault();
                setTimeout(function() {
                    window.scrollTo({
                        top: 0,
                        left: 0,
                        behavior: 'auto'
                    });
                }, 100);
            });
        });
        </script>
        """, unsafe_allow_html=True)
    else:
        # No mostrar nada cuando hay bono seleccionado pero no se ha calculado
        pass
    
    if not st.session_state.get('mercados_activo', False) and not st.session_state.get('indices_activo', False) and not st.session_state.get('bono_seleccionado'):
        # Mostrar los 4 gráficos de TradingView cuando no se ha calculado (solo si mercados e indices no están activos)
        # Crear 2 filas de 2 columnas cada una
        col1, col2 = st.columns(2)
        
        with col1:
            # S&P 500
            sp500_html = """
                <div class="tradingview-widget-container" style="height: 300px; width: 100%;">
                    <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
                    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                    {
                    "symbol": "SPX500",
                    "width": "100%",
                    "height": "300",
                    "locale": "es",
                    "dateRange": "12M",
                    "colorTheme": "light",
                    "isTransparent": true,
                    "autosize": false,
                    "largeChartUrl": "",
                    "hideTopToolbar": true,
                    "hideLegend": false,
                    "saveImage": false
                    }
                    </script>
                </div>
            """
            st.components.v1.html(sp500_html, height=300)
            
        with col2:
            # IMV Merval
            imv_html = """
            <div class="tradingview-widget-container" style="height: 300px; width: 100%;">
                <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                {
                "symbol": "IMV",
                "width": "100%",
                "height": "300",
                "locale": "es",
                "dateRange": "12M",
                "colorTheme": "light",
                "isTransparent": true,
                "autosize": false,
                "largeChartUrl": "",
                "hideTopToolbar": true,
                "hideLegend": false,
                "saveImage": false
                }
                </script>
            </div>
            """
            st.components.v1.html(imv_html, height=300)
        
        # Espaciado reducido antes de la tabla de datos de mercado
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Construir listas de bonos agrupadas por tipo con ticker válido
        bonos_soberano = []
        bonos_corporativo_ley_arg = []
        bonos_corporativo_ley_argentina = []
        bonos_otros = []
        
        for bono in bonos:
            ticker = bono.get('ticker', '').strip()
            tipo_bono = bono.get('tipo_bono', '').strip()
            
            if ticker and ticker != '' and ticker != 'SPX500':  # Excluir default y vacíos
                symbol_entry = {
                    "name": ticker,
                    "displayName": bono.get('nombre', ticker)
                }
                
                # Agrupar por tipo de bono (case-insensitive y flexible)
                tipo_lower = tipo_bono.lower()
                
                if "soberano" in tipo_lower and "usd" in tipo_lower:
                    bonos_soberano.append(symbol_entry)
                elif "corporativo" in tipo_lower and "ley" in tipo_lower and "arg" in tipo_lower and "argentina" not in tipo_lower:
                    # Corporativo Ley Arg (sin "Argentina")
                    bonos_corporativo_ley_arg.append(symbol_entry)
                elif "corporativo" in tipo_lower and "ley" in tipo_lower and "argentina" in tipo_lower:
                    # Corporativo Ley Argentina
                    bonos_corporativo_ley_argentina.append(symbol_entry)
                elif "soberano" in tipo_lower:
                    # Cualquier otro tipo soberano
                    bonos_soberano.append(symbol_entry)
                else:
                    bonos_otros.append(symbol_entry)
        
        # Ordenar cada lista de bonos alfabéticamente por displayName
        bonos_soberano.sort(key=lambda x: x['displayName'])
        bonos_corporativo_ley_arg.sort(key=lambda x: x['displayName'])
        bonos_corporativo_ley_argentina.sort(key=lambda x: x['displayName'])
        bonos_otros.sort(key=lambda x: x['displayName'])
        
        # Construir JSON de símbolos con bonos segmentados
        bonos_groups = []
        
        if bonos_soberano:
            bonos_groups.append({
                "name": "Bonos Soberanos",
                "symbols": bonos_soberano
            })
        
        if bonos_corporativo_ley_arg:
            bonos_groups.append({
                "name": "Corporativo Ley Arg",
                "symbols": bonos_corporativo_ley_arg
            })
        
        if bonos_corporativo_ley_argentina:
            bonos_groups.append({
                "name": "Corporativo Ley Argentina",
                "symbols": bonos_corporativo_ley_argentina
            })
        
        if bonos_otros:
            bonos_groups.append({
                "name": "Corporativos Ley NY",
                "symbols": bonos_otros
            })
        
        # Construir JSON de símbolos
        symbols_groups = [
                {
                    "name": "Indices",
                    "symbols": [
                    {"name": "SPX500", "displayName": "S&P 500"},
                    {"name": "NASDAQ:IXIC", "displayName": "NASDAQ"},
                    {"name": "BMFBOVESPA:IBOV", "displayName": "Bovespa"},
                    {"name": "IMV", "displayName": "Merval"}
                ]
            }
        ]
        
        # Agregar grupos de bonos
        symbols_groups.extend(bonos_groups)
        
        # Agregar Monedas y Commodities
        symbols_groups.append({
                    "name": "Monedas",
                    "symbols": [
                {"name": "FX_IDC:USDARS", "displayName": "USD/ARS"},
                {"name": "FX_IDC:USDEUR", "displayName": "USD/EUR"},
                {"name": "FX_IDC:USDGBP", "displayName": "USD/GBP"},
                {"name": "FX_IDC:USDJPY", "displayName": "USD/JPY"}
            ]
        })
        
        symbols_groups.append({
                    "name": "Commodities",
                    "symbols": [
                {"name": "TVC:USOIL", "displayName": "Petróleo WTI"},
                {"name": "TVC:UKOIL", "displayName": "Petróleo Brent"},
                {"name": "TVC:GOLD", "displayName": "Oro"},
                {"name": "TVC:SILVER", "displayName": "Plata"}
            ]
        })
        
        # Widget Market Data - Ancho completo
        market_data_html = f"""
        <div class="tradingview-widget-container" style="height: 800px; width: 100%; font-size: 8px; margin-top: 0;">
            <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%; font-size: 8px;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js" async>
            {{
            "colorTheme": "light",
            "locale": "es",
            "largeChartUrl": "",
            "isTransparent": true,
            "showSymbolLogo": false,
            "backgroundColor": "transparent",
            "support_host": "https://www.tradingview.com",
            "width": "100%",
            "height": "800",
            "symbolsGroups": {json.dumps(symbols_groups, ensure_ascii=False)}
            }}
            </script>
        </div>
        """
        st.components.v1.html(market_data_html, height=800)
        
        
except FileNotFoundError:
    st.error("❌ No se pudo cargar el archivo de datos")
    st.info("Asegúrese de que el archivo 'bonos_flujos.xlsx' esté en el directorio correcto")
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
