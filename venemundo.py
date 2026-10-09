import os
import random
import requests
import feedparser
import xml.etree.ElementTree as ET
from datetime import datetime

# CONFIGURACIÓN
TOKEN = os.environ.get('BOT_TOKEN')
CANAL = '@VeneMundo360'
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
API_PHOTO = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
VISTOS_FILE = 'vistos_venemundo.txt'

# FUENTES DE INFORMACIÓN
FUENTES = {
    "youtube": {
        "nombre": "CNN en Español", # Puedes cambiar este ID por el de Venevisión o Meridiano luego
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCupvZG-5ko_eiXAupbDfxWw",
        "tipo": "video"
    },
    "noticias": {
        "nombre": "BBC News Mundo",
        "url": "http://feeds.bbci.co.uk/mundo/rss.xml",
        "tipo": "rss"
    },
    "cultura": {
        "nombre": "Wikipedia Venezuela",
        "temas": ["Cultura de Venezuela", "Gastronomía de Venezuela", "Historia de Venezuela", "Música de Venezuela"],
        "tipo": "wiki"
    }
}

def cargar_vistos():
    if os.path.exists(VISTOS_FILE):
        with open(VISTOS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def guardar_visto(item_id):
    with open(VISTOS_FILE, 'a', encoding='utf-8') as f:
        f.write(item_id + '\n')

def obtener_youtube():
    fuente = FUENTES["youtube"]
    resp = requests.get(fuente["url"], timeout=10)
    root = ET.fromstring(resp.content)
    
    # El namespace de YouTube Atom feed
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
    entries = root.findall('atom:entry', ns)
    
    for entry in entries:
        video_id = entry.find('yt:videoId', ns).text
        titulo = entry.find('atom:title', ns).text
        link = entry.find('atom:link', ns).attrib['href']
        
        return video_id, f"📺 *NUEVO VIDEO: {fuente['nombre']}*\n\n🎬 {titulo}\n\n🔗 Ver aquí: {link}", "video"
    return None, None, None

def obtener_rss():
    fuente = FUENTES["noticias"]
    feed = feedparser.parse(fuente["url"])
    
    for entry in feed.entries[:5]: # Revisar los 5 más recientes
        item_id = entry.get('id', entry.get('link'))
        titulo = entry.get('title', 'Sin título')
        resumen = entry.get('summary', 'Sin resumen')
        # Limpiar HTML del resumen
        import re
        resumen_limpio = re.sub('<.*?>', '', resumen)[:200] + "..."
        link = entry.get('link', '')
        
        return item_id, f"📰 *NOTICIA: {fuente['nombre']}*\n\n📌 *{titulo}*\n\n{resumen_limpio}\n\n🔗 Leer más: {link}", "rss"
    return None, None, None

def obtener_wiki():
    temas = FUENTES["cultura"]["temas"]
    tema = random.choice(temas)
    url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{tema.replace(' ', '_')}"
    resp = requests.get(url, timeout=10)
    
    if resp.status_code == 200:
        data = resp.json()
        return tema, f"🎨 *CULTURA: {data.get('title')}*\n\n{data.get('extract', '')[:300]}...\n\n📚 Fuente: Wikipedia", "wiki"
    return None, None, None

def enviar_mensaje(texto, es_video=False):
    # Si fuera video con foto, usaríamos sendPhoto, pero por simplicidad y estabilidad usamos sendMessage con formato Markdown
    data = {
        'chat_id': CANAL,
        'text': texto,
        'parse_mode': 'Markdown'
    }
    r = requests.post(API_URL, data=data, timeout=10)
    return r.status_code == 200

def main():
    print("🌍 Iniciando Cerebro Central VeneMundo...")
    vistos = cargar_vistos()
    
    # Elegir una fuente al azar
    clave_fuente = random.choice(list(FUENTES.keys()))
    print(f"🎲 Fuente seleccionada: {clave_fuente}")
    
    if clave_fuente == "youtube":
        item_id, texto, tipo = obtener_youtube()
    elif clave_fuente == "noticias":
        item_id, texto, tipo = obtener_rss()
    else:
        item_id, texto, tipo = obtener_wiki()
        
    if item_id and item_id not in vistos:
        print(f"✅ Publicando: {item_id}")
        if enviar_mensaje(texto):
            guardar_visto(item_id)
            print("🚀 ¡Publicado con éxito en Telegram!")
        else:
            print("❌ Error al enviar a Telegram")
    else:
        print("⚠️ Contenido ya visto o no disponible. Reintentando en el próximo ciclo.")

if __name__ == '__main__':
    main()
