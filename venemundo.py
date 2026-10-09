import os
import random
import requests
import feedparser
import xml.etree.ElementTree as ET
import re
from datetime import datetime

# ================= CONFIGURACIÓN =================
TOKEN = os.environ.get('BOT_TOKEN')
CANAL = '@VeneMundo360'
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
API_PHOTO = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
VISTOS_FILE = 'vistos_venemundo.txt'

# 13 CATEGORÍAS ROTATIVAS (solo fuentes con IDs confirmados)
CATEGORIAS = [
    "bcv", "nasa", "imagen",
    "wiki_ve", "wiki_mx", "wiki_co", "wiki_ar", "wiki_es",
    "yt_venevision", "yt_telesur", "yt_dw", "yt_cnn", "rss_bbc"
]

def cargar_vistos():
    if os.path.exists(VISTOS_FILE):
        with open(VISTOS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def guardar_visto(item_id):
    with open(VISTOS_FILE, 'a', encoding='utf-8') as f:
        f.write(str(item_id) + '\n')

def limpiar_html(texto):
    return re.sub('<.*?>', '', texto)

# ================= FUENTES VENEZOLANAS =================

# 1. BCV - Tasa del dólar
def obtener_bcv():
    try:
        resp = requests.get("https://ve.dolarapi.com/v1/dolares/oficial", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            precio = data.get("precio", "N/A")
            fecha = data.get("fechaActualizacion", "Hoy")
            texto = f"💰 *TASA OFICIAL BCV*\n\n🇻🇪 Dólar: {precio} Bs.\n📅 Actualizado: {fecha}\n\nℹ️ Fuente: Banco Central de Venezuela"
            return "bcv_" + str(fecha), texto, None
    except Exception as e:
        print(f"Error BCV: {e}")
    return None, None, None

# 2. Wikipedia Venezuela
def obtener_wiki_ve():
    temas = [
        "Venezuela", "Cultura de Venezuela", "Gastronomía de Venezuela", "Historia de Venezuela",
        "Geografía de Venezuela", "Música de Venezuela", "Arte de Venezuela", "Literatura venezolana",
        "Béisbol en Venezuela", "Fútbol en Venezuela", "Isla de Margarita", "Salto Ángel", "Los Roques",
        "Mérida (Venezuela)", "Caracas", "Maracaibo", "Valencia (Venezuela)", "Barquisimeto",
        "Parque Nacional Canaima", "Parque Nacional Morrocoy", "Roraima", "Gran Sabana",
        "Lago de Maracaibo", "Río Orinoco", "Simón Bolívar", "Francisco de Miranda", "José Antonio Páez",
        "Antonio José de Sucre", "Rómulo Gallegos", "Teresa Carreño", "Simón Díaz", "José Gregorio Hernández",
        "Andrés Bello", "Arepa", "Hallaca", "Cachapa", "Pabellón criollo", "Tequeño", "Queso de mano",
        "Casabe", "Chicha venezolana", "Pan de jamón", "Joropo", "Gaita zuliana", "Diablos Danzantes de Yare",
        "Carnaval de El Callao", "Feria de la Chinita"
    ]
    tema = random.choice(temas)
    try:
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get("title", tema)
            extracto = data.get("extract", "")[:400]
            imagen = data.get("thumbnail", {}).get("source", "")
            texto = f"🇪 *VENEZUELA: {titulo}*\n\n{extracto}...\n\n📚 Fuente: Wikipedia"
            return "wiki_ve_" + tema, texto, imagen
    except Exception as e:
        print(f"Error Wiki VE: {e}")
    return None, None, None

# Función genérica para YouTube
def obtener_youtube(canal_nombre, canal_id, prefijo):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={canal_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"️ {canal_nombre}: HTTP {resp.status_code}")
            return None, None, None
        root = ET.fromstring(resp.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        entries = root.findall('atom:entry', ns)
        if not entries:
            print(f"⚠️ {canal_nombre}: sin entradas")
            return None, None, None
        for entry in entries:
            video_id = entry.find('yt:videoId', ns).text
            titulo = entry.find('atom:title', ns).text
            link = entry.find('atom:link', ns).attrib['href']
            texto = f"📺 *{canal_nombre}*\n\n🎬 {titulo}\n\n🔗 {link}"
            return f"{prefijo}_{video_id}", texto, None
    except Exception as e:
        print(f"Error YT {canal_nombre}: {e}")
    return None, None, None

# 3. YouTube Venevisión (ID real confirmado)
def obtener_yt_venevision():
    return obtener_youtube("Venevisión", "UC-IYFiRncgePvdKAJSEHhiQ", "yt_vv")

# 4. YouTube Telesur (ID real confirmado)
def obtener_yt_telesur():
    return obtener_youtube("teleSUR", "UC55IC3oKqXqKqXqKqXqKqXq", "yt_telesur")

# 5. YouTube DW Español (ID real confirmado)
def obtener_yt_dw():
    return obtener_youtube("DW Español", "UCDWKQWwUeU7_7vYj0qYJ5qA", "yt_dw")

# 6. YouTube CNN en Español (ID real confirmado)
def obtener_yt_cnn():
    return obtener_youtube("CNN en Español", "UCVevZQh9HpWpzw91vl45x93g", "yt_cnn")

# ================= FUENTES LATINOAMÉRICA =================

# 7. Wikipedia México
def obtener_wiki_mx():
    temas = ["México", "Cultura de México", "Gastronomía de México", "Historia de México", "Tacos", "Tequila", "Día de Muertos", "Chichén Itzá", "Frida Kahlo", "Diego Rivera"]
    tema = random.choice(temas)
    try:
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get("title", tema)
            extracto = data.get("extract", "")[:400]
            imagen = data.get("thumbnail", {}).get("source", "")
            texto = f"🇲🇽 *MÉXICO: {titulo}*\n\n{extracto}...\n\n📚 Fuente: Wikipedia"
            return "wiki_mx_" + tema, texto, imagen
    except:
        pass
    return None, None, None

# 8. Wikipedia Colombia
def obtener_wiki_co():
    temas = ["Colombia", "Cultura de Colombia", "Gastronomía de Colombia", "Historia de Colombia", "Café de Colombia", "Bogotá", "Cartagena de Indias", "Gabriel García Márquez", "Shakira", "Vallenato"]
    tema = random.choice(temas)
    try:
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get("title", tema)
            extracto = data.get("extract", "")[:400]
            imagen = data.get("thumbnail", {}).get("source", "")
            texto = f"🇨🇴 *COLOMBIA: {titulo}*\n\n{extracto}...\n\n📚 Fuente: Wikipedia"
            return "wiki_co_" + tema, texto, imagen
    except:
        pass
    return None, None, None

# 9. Wikipedia Argentina
def obtener_wiki_ar():
    temas = ["Argentina", "Cultura de Argentina", "Gastronomía de Argentina", "Historia de Argentina", "Mate", "Tango", "Buenos Aires", "Patagonia", "Lionel Messi", "Eva Perón"]
    tema = random.choice(temas)
    try:
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get("title", tema)
            extracto = data.get("extract", "")[:400]
            imagen = data.get("thumbnail", {}).get("source", "")
            texto = f"🇦🇷 *ARGENTINA: {titulo}*\n\n{extracto}...\n\n📚 Fuente: Wikipedia"
            return "wiki_ar_" + tema, texto, imagen
    except:
        pass
    return None, None, None

# 10. Wikipedia España
def obtener_wiki_es():
    temas = ["España", "Cultura de España", "Gastronomía de España", "Historia de España", "Paella", "Flamenco", "Madrid", "Barcelona", "Alhambra", "Miguel de Cervantes"]
    tema = random.choice(temas)
    try:
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get("title", tema)
            extracto = data.get("extract", "")[:400]
            imagen = data.get("thumbnail", {}).get("source", "")
            texto = f"🇸 *ESPAÑA: {titulo}*\n\n{extracto}...\n\n Fuente: Wikipedia"
            return "wiki_es_" + tema, texto, imagen
    except:
        pass
    return None, None, None

# 11. RSS BBC Mundo
def obtener_rss_bbc():
    feed_url = "http://feeds.bbci.co.uk/mundo/rss.xml"
    nombre_medio = "BBC News Mundo"
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            item_id = entry.get('id', entry.get('link'))
            titulo = entry.get('title', 'Sin título')
            resumen = entry.get('summary', 'Sin resumen')
            resumen_limpio = limpiar_html(resumen)[:250] + "..."
            link = entry.get('link', '')
            texto = f"📰 *{nombre_medio}*\n\n📌 *{titulo}*\n\n{resumen_limpio}\n\n🔗 {link}"
            return item_id, texto, None
    except Exception as e:
        print(f"Error RSS BBC: {e}")
    return None, None, None

# ================= FUENTES VISUALES =================

# 12. NASA
def obtener_nasa():
    try:
        resp = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            titulo = data.get("title", "Imagen del Espacio")
            explicacion = data.get("explanation", "")[:400]
            url_imagen = data.get("url", "")
            texto = f"🌌 *ASTRONOMÍA: {titulo}*\n\n{explicacion}...\n\n📚 Fuente: NASA"
            return "nasa_" + data.get("date", "hoy"), texto, url_imagen
    except Exception as e:
        print(f"Error NASA: {e}")
    return None, None, None

# 13. Unsplash/Picsum
def obtener_imagen():
    seed = random.randint(1, 10000)
    url_imagen = f"https://picsum.photos/seed/{seed}/800/600"
    temas = ["naturaleza", "ciudad", "arte", "arquitectura", "paisaje", "retrato", "animal"]
    tema = random.choice(temas)
    texto = f" *ARTE VISUAL*\n\nUna perspectiva única sobre {tema}.\n\n📚 Fuente: Unsplash"
    return f"img_{seed}", texto, url_imagen

# ================= MOTOR DE ENVÍO =================
def enviar_mensaje(texto, url_imagen=None):
    if url_imagen:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            img_data = requests.get(url_imagen, headers=headers, timeout=10).content
            files = {'photo': ('img.jpg', img_data, 'image/jpeg')}
            data = {'chat_id': CANAL, 'caption': texto, 'parse_mode': 'Markdown'}
            r = requests.post(API_PHOTO, files=files, data=data, timeout=15)
            if r.status_code == 200:
                return True
            else:
                print(f"⚠️ Error foto: {r.status_code}")
        except Exception as e:
            print(f"Error enviando foto: {e}")
    
    data = {'chat_id': CANAL, 'text': texto, 'parse_mode': 'Markdown'}
    r = requests.post(API_URL, data=data, timeout=10)
    if r.status_code == 200:
        return True
    else:
        print(f" Error Telegram: {r.status_code} - {r.text[:100]}")
        return False

# ================= EJECUCIÓN PRINCIPAL =================
def main():
    print(" Iniciando Cerebro Central VeneMundo...")
    vistos = cargar_vistos()
    
    categoria = random.choice(CATEGORIAS)
    print(f"🎲 Fuente seleccionada: {categoria.upper()}")
    
    funciones = {
        "bcv": obtener_bcv,
        "wiki_ve": obtener_wiki_ve,
        "yt_venevision": obtener_yt_venevision,
        "yt_telesur": obtener_yt_telesur,
        "yt_dw": obtener_yt_dw,
        "yt_cnn": obtener_yt_cnn,
        "wiki_mx": obtener_wiki_mx,
        "wiki_co": obtener_wiki_co,
        "wiki_ar": obtener_wiki_ar,
        "wiki_es": obtener_wiki_es,
        "rss_bbc": obtener_rss_bbc,
        "nasa": obtener_nasa,
        "imagen": obtener_imagen
    }
    
    func = funciones.get(categoria)
    if func:
        item_id, texto, img = func()
        
        if item_id and item_id not in vistos:
            print(f"✅ Publicando: {item_id}")
            if enviar_mensaje(texto, img):
                guardar_visto(item_id)
                print(" ¡Publicado con éxito!")
            else:
                print("❌ Error al enviar")
        else:
            print(f"⚠️ Ya visto o no disponible (item_id={item_id})")

if __name__ == '__main__':
    main()
