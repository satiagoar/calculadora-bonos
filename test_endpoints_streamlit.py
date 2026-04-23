"""
Página de Streamlit para probar endpoints de TradingView

EJECUTAR:
    streamlit run test_endpoints_streamlit.py

Esta página te ayudará a identificar y probar endpoints de TradingView
de forma interactiva.
"""
import streamlit as st
import requests
import json

st.set_page_config(page_title="TradingView Endpoint Tester", page_icon="🔍")

st.title("🔍 Identificador de Endpoints de TradingView")
st.markdown("---")

st.markdown("""
### 📋 Instrucciones

1. **Abre DevTools en tu navegador** (F12)
2. Ve a la pestaña **Network** (Red)
3. Filtra por **XHR** o **Fetch**
4. Recarga la página donde está la tabla de TradingView
5. Busca requests que devuelvan JSON con precios
6. Copia la información del request exitoso abajo
""")

st.markdown("---")

# Sección 1: Probar endpoint manual
st.subheader("1️⃣ Probar Endpoint Manualmente")

col1, col2 = st.columns(2)

with col1:
    endpoint_url = st.text_input(
        "URL del Endpoint",
        placeholder="https://quote-feed.tradingview.com/quotes?symbols=...",
        help="Pega la URL completa del request que encontraste en DevTools"
    )

    method = st.selectbox("Método HTTP", ["GET", "POST"])

with col2:
    ticker_test = st.text_input(
        "Ticker a Probar",
        value="AL30D",
        help="Ticker del bono que quieres probar"
    )
    
    exchange_format = st.selectbox(
        "Formato de Exchange",
        ["sin prefijo", "BYMA:", "BCBA:", "AR:"],
        help="Formato del ticker en el endpoint"
    )

# Headers
st.markdown("#### Headers (Opcional)")
with st.expander("Configurar Headers"):
    referer = st.text_input("Referer", value="https://www.tradingview.com/")
    user_agent = st.text_input(
        "User-Agent",
        value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    other_headers = st.text_area(
        "Otros Headers (formato JSON)",
        value='{"Accept": "application/json", "Accept-Language": "es-ES,es;q=0.9"}',
        help='Ejemplo: {"Accept": "application/json"}'
    )

headers = {
    "Referer": referer,
    "User-Agent": user_agent
}

try:
    if other_headers:
        headers.update(json.loads(other_headers))
except:
    st.warning("⚠️ Error al parsear otros headers. Ignorando.")

# Construir URL de prueba
if endpoint_url and ticker_test:
    # Detectar si la URL ya tiene parámetros
    if "symbols=" in endpoint_url or "symbol=" in endpoint_url:
        # Reemplazar el símbolo en la URL
        import re
        if "symbols=" in endpoint_url:
            url_test = re.sub(r'symbols=[^&]*', f'symbols={exchange_format}{ticker_test}'.replace("sin prefijo", ""), endpoint_url)
        else:
            url_test = re.sub(r'symbol=[^&]*', f'symbol={exchange_format}{ticker_test}'.replace("sin prefijo", ""), endpoint_url)
    else:
        # Agregar parámetro
        separator = "&" if "?" in endpoint_url else "?"
        if "symbols=" in endpoint_url.lower() or endpoint_url.lower().endswith("/quotes"):
            url_test = f"{endpoint_url}{separator}symbols={exchange_format}{ticker_test}".replace("sin prefijo", "")
        else:
            url_test = f"{endpoint_url}{separator}symbol={exchange_format}{ticker_test}".replace("sin prefijo", "")
else:
    url_test = endpoint_url

if st.button("🚀 Probar Endpoint", type="primary"):
    if not url_test:
        st.error("❌ Por favor, ingresa una URL")
    else:
        with st.spinner("Probando endpoint..."):
            try:
                if method == "GET":
                    response = requests.get(url_test, headers=headers, timeout=10)
                else:
                    # Para POST, podrías necesitar un body
                    response = requests.post(url_test, headers=headers, json={}, timeout=10)
                
                st.success(f"✅ Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        st.json(data)
                        
                        # Intentar extraer precio
                        st.markdown("#### 💰 Precio Extraído:")
                        precio_encontrado = None
                        
                        if isinstance(data, list) and len(data) > 0:
                            item = data[0]
                            if isinstance(item, dict):
                                precio_encontrado = (item.get('lp') or item.get('price') or 
                                                    item.get('last_price') or item.get('c') or
                                                    item.get('p'))
                        
                        if precio_encontrado:
                            st.success(f"🎯 Precio encontrado: **{precio_encontrado}**")
                        else:
                            st.info("💡 Revisa el JSON de arriba para encontrar dónde está el precio")
                    except:
                        st.text("Respuesta (texto):")
                        st.text(response.text[:1000])
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.text(response.text[:500])
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.markdown("---")

# Sección 2: Probar endpoints conocidos
st.subheader("2️⃣ Probar Endpoints Conocidos")

endpoints_conocidos = [
    {
        "name": "quote-feed (sin prefijo)",
        "url": "https://quote-feed.tradingview.com/quotes?symbols={ticker}",
        "format": ""
    },
    {
        "name": "quote-feed (BYMA:)",
        "url": "https://quote-feed.tradingview.com/quotes?symbols={ticker}",
        "format": "BYMA:"
    },
    {
        "name": "symbol-search",
        "url": "https://symbol-search.tradingview.com/symbol_search/?text={ticker}&exchange=&lang=es&search_type=undefined&domain=production&sort_by_country=AR",
        "format": ""
    },
    {
        "name": "scanner",
        "url": "https://scanner.tradingview.com/symbol?text={ticker}",
        "format": ""
    },
]

ticker_auto = st.text_input("Ticker para pruebas automáticas", value="AL30D")

if st.button("🔄 Probar Todos los Endpoints Conocidos"):
    results = {}
    
    for endpoint in endpoints_conocidos:
        with st.spinner(f"Probando {endpoint['name']}..."):
            try:
                ticker_formatted = f"{endpoint['format']}{ticker_auto}".strip(":")
                url = endpoint['url'].format(ticker=ticker_formatted)
                
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results[endpoint['name']] = {
                            "status": "✅ Éxito",
                            "data": data,
                            "url": url
                        }
                    except:
                        results[endpoint['name']] = {
                            "status": "⚠️ Éxito pero no JSON",
                            "data": response.text[:200],
                            "url": url
                        }
                else:
                    results[endpoint['name']] = {
                        "status": f"❌ Error {response.status_code}",
                        "data": None,
                        "url": url
                    }
            except Exception as e:
                results[endpoint['name']] = {
                    "status": f"❌ Excepción: {str(e)[:50]}",
                    "data": None,
                    "url": endpoint['url']
                }
    
    st.markdown("#### Resultados:")
    for name, result in results.items():
        with st.expander(f"{name} - {result['status']}"):
            st.code(result['url'], language=None)
            if result['data']:
                if isinstance(result['data'], dict) or isinstance(result['data'], list):
                    st.json(result['data'])
                else:
                    st.text(result['data'])

st.markdown("---")

st.subheader("3️⃣ Guía para Usar DevTools")

st.markdown("""
**Ya que los endpoints automáticos no funcionan, necesitamos encontrar el endpoint real que usa el widget:**

### Pasos:

1. **Abre tu app principal** (donde está la tabla de TradingView)
   - Si no está corriendo: `streamlit run app.py`
   - URL: `http://localhost:8501`

2. **Abre DevTools** en esa página
   - Presiona `F12` o `Ctrl+Shift+I`
   - O clic derecho → "Inspeccionar elemento"

3. **Ve a la pestaña Network (Red)**
   - Filtra por **"XHR"** o **"Fetch"**
   - Limpia la lista de requests (botón de clear)

4. **Espera a que cargue la tabla de TradingView**
   - O recarga la página con DevTools abierto

5. **Busca requests que devuelvan JSON**
   - Busca nombres como: "quote", "quotes", "market", "symbol", "data"
   - Haz clic en cualquier request que parezca relevante

6. **Para cada request, revisa:**
   - **Headers** → Copia todos los headers, especialmente:
     - `Referer`
     - `User-Agent`
     - `Cookie` (si existe)
     - Cualquier header de autorización
   - **Payload/Query** → Copia los parámetros
   - **Response** → Copia la estructura del JSON

7. **Pega la información aquí abajo:**
""")

# Campos para documentar el endpoint encontrado
st.markdown("#### 📝 Documentar Endpoint Encontrado")

endpoint_found = st.text_input("URL completa del endpoint", placeholder="https://...")
method_found = st.selectbox("Método HTTP", ["GET", "POST"])

headers_found = st.text_area(
    "Headers (formato JSON)",
    placeholder='{"Referer": "https://www.tradingview.com/", "User-Agent": "...", ...}',
    height=100
)

params_found = st.text_area(
    "Parámetros (Query String o JSON body)",
    placeholder="symbols=BYMA:AL30D,BYMA:AL35D o {'symbols': '...'}",
    height=80
)

response_sample = st.text_area(
    "Respuesta JSON (muestra)",
    placeholder='[{"s": "BYMA:AL30D", "lp": 45.20, ...}]',
    height=150
)

if st.button("💾 Guardar y Probar Endpoint Encontrado"):
    if endpoint_found:
        try:
            # Parsear headers
            headers_dict = {}
            if headers_found:
                try:
                    headers_dict = json.loads(headers_found)
                except:
                    st.warning("⚠️ Headers no son JSON válido, usando como texto simple")
            
            # Probar el endpoint
            with st.spinner("Probando endpoint encontrado..."):
                try:
                    if method_found == "GET":
                        # Agregar params a URL si es GET
                        if params_found and "?" not in endpoint_found:
                            separator = "?" if endpoint_found else ""
                            url_with_params = f"{endpoint_found}{separator}{params_found}"
                        else:
                            url_with_params = endpoint_found
                        
                        response = requests.get(url_with_params, headers=headers_dict, timeout=10)
                    else:
                        # Para POST, parsear params como JSON si es posible
                        post_data = {}
                        if params_found:
                            try:
                                post_data = json.loads(params_found)
                            except:
                                st.info("⚠️ Params no son JSON válido para POST")
                        
                        response = requests.post(endpoint_found, headers=headers_dict, json=post_data, timeout=10)
                    
                    st.success(f"✅ Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            st.json(data)
                            st.success("🎉 ¡Endpoint encontrado y funcionando!")
                        except:
                            st.text("Respuesta (texto):")
                            st.text(response.text[:500])
                    else:
                        st.error(f"❌ Error {response.status_code}")
                        st.text(response.text[:300])
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        except Exception as e:
            st.error(f"Error procesando: {e}")
    else:
        st.warning("⚠️ Por favor ingresa la URL del endpoint")

st.markdown("---")
st.markdown("""
### 📝 Información a Documentar

Cuando encuentres el endpoint que funciona, documenta:

- ✅ **URL completa**
- ✅ **Método HTTP** (GET/POST)
- ✅ **Headers necesarios**
- ✅ **Formato de parámetros**
- ✅ **Estructura del JSON de respuesta**
- ✅ **Dónde está el precio en el JSON** (ej: `data[0].lp`)

Con esta información podremos implementarlo en la app principal.
""")

