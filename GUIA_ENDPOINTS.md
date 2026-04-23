# Guía para Identificar Endpoints de TradingView

## Método 1: Usando DevTools (RECOMENDADO)

### Pasos:

1. **Abrir la aplicación en el navegador**
   - Ejecuta tu app de Streamlit (local o en cloud)
   - Ve a la página donde está la tabla de TradingView

2. **Abrir DevTools**
   - Presiona `F12` o `Ctrl+Shift+I` (Windows/Linux)
   - O `Cmd+Option+I` (Mac)
   - O clic derecho → "Inspeccionar elemento"

3. **Ir a la pestaña Network (Red)**
   - En DevTools, busca la pestaña "Network" o "Red"
   - Si no ves nada, recarga la página con DevTools abierto

4. **Filtrar requests relevantes**
   - Haz clic en el filtro "XHR" o "Fetch" (solo requests AJAX)
   - O busca en el campo de búsqueda: "json", "quote", "market", "data"

5. **Interactuar con la tabla**
   - Si la tabla ya está cargada, haz scroll o espera unos segundos
   - Los requests deberían aparecer en la lista
   - Busca requests que tengan nombres como:
     - `quote-feed`
     - `quotes`
     - `market-quotes`
     - `symbols`
     - `scanner`

6. **Analizar el request exitoso**
   - Haz clic en el request que devuelva JSON con datos de precios
   - Revisa estas secciones:

   **a) Headers (Encabezados):**
   - Ve a "Request Headers"
   - Copia especialmente:
     - `Referer`: generalmente `https://www.tradingview.com/`
     - `User-Agent`: el navegador completo
     - Cualquier header de autorización si existe

   **b) Payload/Query (Parámetros):**
   - Si es GET: revisa "Query String Parameters"
   - Si es POST: revisa "Request Payload"
   - Busca parámetros como:
     - `symbols` o `symbol`
     - `exchange`
     - `locale`

   **c) Response (Respuesta):**
   - Ve a la pestaña "Response" o "Respuesta"
   - Copia la estructura del JSON
   - Identifica dónde están los precios

7. **Ejemplo de lo que podrías encontrar:**

```json
// Request URL:
https://quote-feed.tradingview.com/quotes?symbols=BYMA:AL30D,BYMA:AL35D

// Request Headers:
Referer: https://www.tradingview.com/
User-Agent: Mozilla/5.0 ...

// Response:
[
  {
    "s": "BYMA:AL30D",
    "lp": 45.20,  // last price
    "c": 45.25,   // change
    ...
  }
]
```

## Método 2: Script de Prueba Automática

Ejecuta el script `test_tradingview_endpoints.py`:

```bash
python test_tradingview_endpoints.py
```

Este script prueba varios endpoints conocidos de TradingView.

## Método 3: Inspeccionar el Código del Widget

El widget usa: `embed-widget-market-quotes.js`

1. Busca este archivo en Network
2. Haz clic derecho → "Open in new tab"
3. Busca referencias a endpoints en el código JavaScript
4. Busca llamadas a `fetch()`, `XMLHttpRequest`, o `axios`

## Endpoints Comunes de TradingView

Basado en experiencia previa, TradingView suele usar:

1. **quote-feed.tradingview.com/quotes**
   - Formato: `?symbols=SYMBOL1,SYMBOL2`
   - Retorna: Array de objetos con precios

2. **symbol-search.tradingview.com/symbol_search/**
   - Formato: `?text=TICKER&exchange=&lang=es`
   - Retorna: Array con información del símbolo (puede incluir precio)

3. **scanner.tradingview.com/symbol**
   - Formato: `?text=TICKER`
   - Retorna: Información del símbolo

4. **market-quotes.tradingview.com** (si existe)
   - Similar a quote-feed pero para múltiples símbolos

## Información a Recopilar

Cuando identifiques el endpoint, documenta:

- [ ] URL completa del endpoint
- [ ] Método HTTP (GET/POST)
- [ ] Headers necesarios (especialmente Referer y User-Agent)
- [ ] Formato de parámetros (query string o JSON body)
- [ ] Estructura de la respuesta JSON
- [ ] Ubicación del precio en el JSON (ej: `data[0].lp`, `price`, etc.)
- [ ] Códigos de estado exitosos (200, etc.)

## Próximo Paso

Una vez que tengas esta información, podemos implementar la función en Streamlit para consumir el endpoint.

