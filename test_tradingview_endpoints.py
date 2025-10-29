"""
Script para identificar endpoints de TradingView que devuelven precios

USO:
    python test_tradingview_endpoints.py

Este script prueba varios endpoints conocidos de TradingView y muestra
los resultados para que puedas identificar cuál funciona mejor.
"""
import requests
import json
import time
import sys

# Tickers de prueba (algunos bonos argentinos comunes)
test_tickers = ["AL30D", "AL35D", "GD30D", "GD35D"]

def test_endpoint(url, headers=None, method="GET", data=None):
    """Prueba un endpoint y retorna la respuesta"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"\n{'='*80}")
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        print(f"Headers enviados: {headers}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"✅ Éxito! Respuesta JSON (primeros 500 caracteres):")
                print(json.dumps(json_data, indent=2)[:500])
                return json_data
            except:
                print(f"✅ Éxito! Respuesta (texto, primeros 500 caracteres):")
                print(response.text[:500])
                return response.text
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return None

# Headers comunes que usa TradingView
common_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.tradingview.com/",
    "Origin": "https://www.tradingview.com"
}

print("🔍 Probando endpoints conocidos de TradingView...\n")

# Endpoint 1: quote-feed (ya probamos antes, pero con diferentes formatos)
print("\n1️⃣ Probando quote-feed.tradingview.com")
for ticker in test_tickers[:2]:  # Solo los primeros 2 para no hacer demasiadas requests
    formats = [
        ticker,
        f"BYMA:{ticker}",
        f"BCBA:{ticker}",
        f"AR:{ticker}",
    ]
    for fmt in formats:
        url = f"https://quote-feed.tradingview.com/quotes?symbols={fmt}"
        test_endpoint(url, common_headers)
        time.sleep(0.5)  # Pequeña pausa entre requests

# Endpoint 2: symbol-search
print("\n2️⃣ Probando symbol-search.tradingview.com")
for ticker in test_tickers[:2]:
    url = f"https://symbol-search.tradingview.com/symbol_search/?text={ticker}&exchange=&lang=es&search_type=undefined&domain=production&sort_by_country=AR"
    test_endpoint(url, common_headers)
    time.sleep(0.5)

# Endpoint 3: screener (para buscar instrumentos)
print("\n3️⃣ Probando screener.tradingview.com")
for ticker in test_tickers[:2]:
    url = f"https://scanner.tradingview.com/symbol?text={ticker}"
    test_endpoint(url, common_headers)
    time.sleep(0.5)

# Endpoint 4: market-quotes específico (si existe)
print("\n4️⃣ Probando posibles endpoints de market-quotes")
test_symbols = ",".join([f"BYMA:{t}" for t in test_tickers[:2]])
urls_to_try = [
    f"https://market-quotes.tradingview.com/quotes?symbols={test_symbols}",
    f"https://api.tradingview.com/v1/symbols/quotes?symbols={test_symbols}",
    f"https://www.tradingview.com/api/v1/symbols/quotes?symbols={test_symbols}",
]

for url in urls_to_try:
    test_endpoint(url, common_headers)
    time.sleep(0.5)

# Endpoint 5: FINAM (Finam Holdings - proveedor de datos de TradingView)
print("\n5️⃣ Probando FINAM API")
for ticker in test_tickers[:2]:
    # FINAM usa códigos específicos, pero probemos
    url = f"https://finam.ru/api/quotes?code={ticker}&market=2048"  # Market code para Argentina
    test_endpoint(url, common_headers)
    time.sleep(0.5)

print("\n" + "="*80)
print("✅ Prueba completada")
print("\n💡 INSTRUCCIONES PARA IDENTIFICAR EL ENDPOINT MANUALMENTE:")
print("1. Abre tu app en el navegador")
print("2. Presiona F12 para abrir DevTools")
print("3. Ve a la pestaña 'Network' (Red)")
print("4. Filtra por 'XHR' o 'Fetch'")
print("5. Recarga la página o interactúa con la tabla de TradingView")
print("6. Busca requests que devuelvan JSON con datos de precios")
print("7. Haz clic en el request y revisa:")
print("   - Request URL (URL completa)")
print("   - Request Headers (especialmente Referer, User-Agent)")
print("   - Request Payload/Query String (parámetros)")
print("   - Response (estructura del JSON)")
print("\n8. Anota esos detalles y podremos replicarlo en Streamlit")

