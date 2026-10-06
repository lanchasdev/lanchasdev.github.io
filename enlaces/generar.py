#!/usr/bin/env python3
"""Páginas de enlace para la bio de TikTok, Instagram y YouTube: una por app.

    python3 enlaces/generar.py                # rehace el HTML con lo ya bajado
    python3 enlaces/generar.py --bajar mtc    # además vuelve a bajar icono, capturas y textos
    python3 enlaces/generar.py --textos       # solo nombre y frase de Play en cada idioma

Cada página sale en `/<slug>/index.html` y lleva al lado su icono y sus capturas, bajadas
de las tiendas para que no dependan de enlazar su CDN. El texto de la página (nombre, frase,
descargas) se copia de la ficha de Google Play en español e inglés y se elige por el idioma
del móvil que la abre.

En la bio se pone el enlace con la red detrás, `lanchasdev.github.io/mtc?s=tt`, y la página
se la pasa a la tienda: a Play como `utm_source` (sale en Play Console ▸ Adquisición) y a
App Store como `ct` (App Analytics ▸ Campañas, solo si hay `PT`, el «provider token» del
equipo que da App Store Connect al crear un enlace de campaña: sin él Apple ignora `ct`).
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PT = "128303735"  # provider token de App Store Connect (Análisis ▸ Campañas ▸ +); vacío = los clics de iOS no se atribuyen

APPS = [
    {
        "slug": "mtc", "ios": "6759268591", "play": "com.bydark.traditional.chinese.acupuncture",
        # Las láminas con las mascotas enseñando la app gustan más que las capturas de la ficha:
        # están solo en español, así que en inglés siguen saliendo las de App Store.
        "capturas_propias": {"es": "/Users/alberto/Proyectos/mtc/phone/assets/new-screens/store-concepts-v1"},
        "privacidad": "medicina-china", "descargas": {"es": "+1000 descargas", "en": "1K+ downloads"},
        # Su web de contenido, enlazada en el pie: es un enlace más hacia ella para Google.
        "web": ("https://medicinatradicionalchina.com/", "Guía de medicina china"),
        "tema": {"bg": "#0d1f19", "bg2": "#12302a", "fg": "#f3ecdb", "muted": "#b6c2b3",
                 "accent": "#d8b25a", "glow": "#1f7a4a"},
        # Los nombres con los que ha estado en cada tienda, para que un asistente que la conozca
        # por uno los junte. Las cifras de info.json son las de la ficha de App Store 1.0.8.
        "antes": ["Chinese Medicine: Acupuncture", "Medicina China: Acupuntura",
                  "TCM: Acupuncture & Acupressure"],
        "categoria": "EducationalApplication",
        "idiomas": ["es", "en", "fr", "pt", "ar", "hi", "ja", "ko", "zh", "zh-TW"],
    },
    {
        "slug": "anime", "ios": "6755445114", "play": "com.bydark.animefoodrecipe",
        "privacidad": "anime-food", "descargas": None,
        "web": ("https://recetasdeanime.com/", "Recetas de anime"),
        "tema": {"bg": "#1e0f05", "bg2": "#3a1a06", "fg": "#fff4e6", "muted": "#e8c9a6",
                 "accent": "#ff8a1f", "glow": "#ff7a00"},
        "antes": ["Japanese Food Anime: Cookbook"],
        "categoria": "LifestyleApplication",
        "idiomas": ["es", "en", "ar", "de", "fr", "hi", "id", "it", "ja", "ko", "pt", "ru", "th", "tr", "zh"],
    },
    {
        "slug": "looksmax", "ios": "6756071839", "play": "com.bydark.looksmaxinghabit",
        "privacidad": "looksmax", "descargas": None,
        "web": ("https://glowupformen.com/", "Guías de glow up"),
        # Leo Glow 2.0 (oct 2026): negro y lima, como la app. Icono y capturas puestos a mano desde
        # store-assets/ porque App Store sigue en la 1.2.0 hasta que aprueben la 2.0.3: un
        # --bajar de esta app traería el icono viejo. Los textos sí se pueden refrescar (--textos).
        "fijas": True,
        "tema": {"bg": "#0a0b0a", "bg2": "#141712", "fg": "#f4f7ec", "muted": "#b3baa6",
                 "accent": "#e3fa5c", "glow": "#9bd400"},
        # ChatGPT y Google mandan ~60 descargas al mes (App Store Connect ▸ Referencias de app,
        # sep 2026) por el nombre «Looksmaxxing: Glow Up Coach», que desde el 05-10-2026 vuelve a
        # ser el de App Store y el de la página. Aquí van los demás nombres con los que ha estado o
        # está (Play cambia el título por mercado) para que un asistente los junte todos.
        "antes": ["Leo Glow", "Leo AI: Glow Up & Looksmaxxing", "Looksmaxxing: Gamify Your Life",
                  "Looksmaxxing: Self Discipline", "Looksmaxxing: Glow Up Hombres",
                  "Looksmaxxing Glow Up Masculino", "Looksmaxing Habit Roulette",
                  "Looksmaxxing Habit Wheeler"],
        "categoria": "LifestyleApplication",
        "idiomas": ["es", "en", "ar", "de", "fr", "hi", "id", "it", "ja", "ko", "pl", "pt", "ru", "th", "tr",
                    "vi", "zh"],
    },
    {
        "slug": "zodiaco", "ios": "", "play": "com.celestialpath.zodiac",
        "privacidad": "", "descargas": {"es": "+1000 descargas", "en": "1K+ downloads"},
        "web": ("https://horoscopochinohoy.com/", "Horóscopo chino 2027"),
        "tema": {"bg": "#f6ecd8", "bg2": "#efdcb8", "fg": "#3b2415", "muted": "#7a5a40",
                 "accent": "#c4561d", "glow": "#e9a44a", "claro": True},
        "categoria": "LifestyleApplication",
        "idiomas": ["es", "en", "ar", "bn", "de", "fr", "hi", "id", "it", "ja", "ko", "ms", "pt", "ru", "th",
                    "tr", "vi", "zh", "zh-TW"],
    },
]

# Cómo pide Play cada idioma de la página (`hl`), cuando no es el mismo código.
HL_PLAY = {"zh": "zh-CN", "zh-TW": "zh-TW", "pt": "pt-BR"}
RTL = {"ar"}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read()


def _play(pkg, hl):
    h = _get(f"https://play.google.com/store/apps/details?id={pkg}&hl={hl}").decode()
    titulo = html.unescape(re.search(r'og:title" content="([^"]*)', h).group(1))
    # Play pega su nombre al título en cada idioma, unas veces detrás («… - Google Play のアプリ»)
    # y otras delante («Приложения в Google Play – …»): se quita el trozo que lo lleva.
    titulo = re.sub(r"\s+[-–]\s+[^-–]*Google Play[^-–]*$", "", titulo)
    titulo = re.sub(r"^[^-–]*Google Play[^-–]*\s+[-–]\s+", "", titulo)
    frase = html.unescape(re.search(r'og:description" content="([^"]*)', h).group(1))
    icono = re.search(r'og:image" content="([^"=]*)', h).group(1)
    # Las capturas de la ficha son las únicas imágenes que Play sirve a 526x296 (el resto son
    # iconos): el texto alternativo cambia con el idioma y no sirve para reconocerlas.
    capturas = list(dict.fromkeys(re.findall(r'src="(https://play-lh\.googleusercontent\.com/[\w-]+)=w526-h296', h)))
    return titulo, frase, icono, capturas


def textos(app, datos):
    """Nombre y frase de la ficha de Play en cada idioma de la página.

    Es el texto que cada mercado ve en su tienda, no una traducción: si Play no tiene ficha en
    ese idioma devuelve la inglesa, y entonces la página se queda con la inglesa también."""
    for lang in app["idiomas"]:
        titulo, frase, _, _ = _play(app["play"], HL_PLAY.get(lang, lang))
        datos["nombre"][lang], datos["frase"][lang] = titulo, frase
    return datos


def bajar(app):
    """Icono y capturas (español e inglés) de las tiendas, y los textos de todos los idiomas."""
    dest = RAIZ / app["slug"]
    dest.mkdir(exist_ok=True)
    datos = {"nombre": {}, "frase": {}, "capturas": {}}
    for lang in ("es", "en"):
        titulo, frase, icono_play, capturas = _play(app["play"], lang)
        datos["nombre"][lang], datos["frase"][lang] = titulo, frase
        if app["ios"]:
            pais = "es" if lang == "es" else "us"
            r = json.loads(_get(f"https://itunes.apple.com/lookup?id={app['ios']}&country={pais}"))["results"][0]
            urls = [re.sub(r"/\d+x\d+bb\.\w+$", "/460x1000bb.jpg", u) for u in r["screenshotUrls"]]
            icono = re.sub(r"/\d+x\d+bb\.\w+$", "/512x512bb.png", r["artworkUrl512"])
        else:
            urls = [u + "=w460-h1000-rw" for u in capturas]
            icono = icono_play + "=s512"
        nombres = []
        propias = app.get("capturas_propias", {}).get(lang)
        if propias:
            for viejo in dest.glob(f"{lang}-*.jpg"):
                viejo.unlink()
            for i, f in enumerate(sorted(pathlib.Path(propias).glob("*.png")), 1):
                nombre = f"{lang}-{i}.jpg"
                subprocess.run(["sips", "-Z", "1000", "-s", "format", "jpeg", "-s", "formatOptions", "80",
                                str(f), "--out", str(dest / nombre)], check=True, capture_output=True)
                nombres.append(nombre)
            urls = []
        for i, u in enumerate(urls[:6], 1):
            nombre = f"{lang}-{i}.jpg"
            (dest / nombre).write_bytes(_get(u))
            if not app["ios"]:  # Play las da en webp sin pérdida: ~700 KB cada una
                subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "80",
                                str(dest / nombre), "--out", str(dest / nombre)], check=True, capture_output=True)
            nombres.append(nombre)
        datos["capturas"][lang] = nombres
    (dest / "icono.png").write_bytes(_get(icono))
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", str(dest / "icono.png"),
                    "--out", str(dest / "icono.jpg")], check=True, capture_output=True)
    (dest / "icono.png").unlink()
    textos(app, datos)
    (dest / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    return datos


APPLE = ('<svg viewBox="0 0 384 512" aria-hidden="true"><path fill="currentColor" d="M318.7 268.7c-.2-36.7 '
         '16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 '
         '141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 '
         '17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 '
         '24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>')
PLAY = ('<svg viewBox="0 0 512 512" aria-hidden="true"><path fill="#00d7fe" d="M47 25c-6 6-9 15-9 27v408c0 12 3 21 '
        '9 27l2 2 229-229v-6L49 23z"/><path fill="#ffce00" d="M354 336l-76-76v-6l76-76 2 1 90 51c26 15 26 39 0 54l-90 '
        '51z"/><path fill="#ff3a44" d="M356 335l-78-78L47 488c9 9 23 10 39 1l270-154"/><path fill="#00f076" '
        'd="M356 179L86 26c-16-9-30-8-39 1l231 230z"/></svg>')

# Los textos fijos de la página (botones, pie), por idioma. Los de cada app van en <slug>/info.json.
TEXTOS = json.loads((RAIZ / "enlaces" / "textos.json").read_text())


def contenido(app):
    """El info.json de la app: {idioma: {etiquetas, titulo, texto, funciones, faq}}."""
    f = RAIZ / app["slug"] / "info.json"
    return json.loads(f.read_text()) if f.exists() else {}


def idiomas_de(app, info_app):
    """Los idiomas que la página puede enseñar enteros: los de la app que tienen info.json y
    botones traducidos. El español va primero porque es el que lleva el HTML visible."""
    return [l for l in app["idiomas"] if l in info_app and l in TEXTOS]


def info(app, datos, info_app, langs):
    """El bloque «qué es» en todos los idiomas y su JSON-LD.

    Todos los idiomas van escritos en el HTML, no metidos después con JavaScript: los
    rastreadores de los asistentes (ChatGPT, Gemini) y de los buscadores leen el HTML tal
    cual llega. El script solo esconde los que no tocan."""
    if not langs:
        return "", ""
    e = lambda s: html.escape(s, quote=True)
    bloques = []
    for lang in langs:
        i = info_app[lang]
        parrafos = "".join(f"<p>{e(p)}</p>" for p in i["texto"])
        funciones = "".join(f"<li>{e(f)}</li>" for f in i["funciones"])
        faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in i["faq"])
        oculto = "" if lang == "es" else " hidden"
        rtl = ' dir="rtl"' if lang in RTL else ""
        bloques.append(f'<section class="info" lang="{lang}"{rtl} data-info{oculto}><h2>{e(i["titulo"])}</h2>'
                       f'{parrafos}<ul>{funciones}</ul><div class="faq">{faq}</div></section>')
    url = f"https://lanchasdev.github.io/{app['slug']}/"
    tiendas = [f"https://play.google.com/store/apps/details?id={app['play']}"]
    if app["ios"]:
        tiendas.insert(0, f"https://apps.apple.com/app/id{app['ios']}")
    nombre = datos["nombre"].get("en") or datos["nombre"]["es"]
    alias = [n for n in dict.fromkeys([*datos["nombre"].values(), *app.get("antes", [])]) if n != nombre]
    base = info_app.get("en") or info_app[langs[0]]
    ld = [{
        "@context": "https://schema.org", "@type": "SoftwareApplication",
        "name": nombre, "alternateName": alias,
        "description": " ".join(base["texto"]),
        "applicationCategory": app.get("categoria", "LifestyleApplication"),
        "operatingSystem": "iOS, Android" if app["ios"] else "Android",
        "inLanguage": langs,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "image": f"{url}icono.jpg", "url": url, "sameAs": tiendas,
        "author": {"@type": "Organization", "name": "Lanchas Dev", "url": "https://lanchasdev.github.io/"},
    }, {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "inLanguage": lang,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for lang in langs for q, a in info_app[lang]["faq"]],
    }]
    # `</` dentro de un <script> lo cerraría: se escapa la barra.
    jsonld = "".join('<script type="application/ld+json">'
                     + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>" for x in ld)
    return "".join(bloques), jsonld


def pagina(app, datos):
    t = app["tema"]
    e = lambda s: html.escape(s, quote=True)
    info_app = contenido(app)
    langs = idiomas_de(app, info_app)
    bloque_info, jsonld = info(app, datos, info_app, langs)
    capturas = "".join(
        f'<img src="{c}" alt="" loading="lazy" width="230" height="500" data-lang-src>' for c in datos["capturas"]["es"])
    etiquetas = "".join(f"<li>{e(x)}</li>" for x in info_app["es"]["etiquetas"]) if langs else ""
    privacidad = (f'<a href="/privacidad/{app["privacidad"]}/" data-t="privacidad">Privacidad</a> · '
                  if app["privacidad"] else "")
    web = (f'<a href="{app["web"][0]}">{html.escape(app["web"][1])}</a> · ' if app.get("web") else "")
    ios = (f'<a class="store" id="ios" href="https://apps.apple.com/app/id{app["ios"]}">{APPLE}'
           f'<span><small data-t="ios_sub">Descárgala en</small>App Store</span></a>') if app["ios"] else ""
    datos_js = json.dumps({
        "slug": app["slug"], "ios": app["ios"], "play": app["play"], "pt": PT,
        "nombre": datos["nombre"], "frase": datos["frase"], "capturas": datos["capturas"],
        "etiquetas": {l: info_app[l]["etiquetas"] for l in langs}, "descargas": app["descargas"],
        "textos": {l: TEXTOS[l] for l in langs}, "langs": langs, "rtl": sorted(RTL),
    }, ensure_ascii=False)
    pill_desc = f'<li class="dl" data-desc>{e(app["descargas"]["es"])}</li>' if app["descargas"] else ""
    return f"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(datos["nombre"]["es"])}</title>
<meta name="description" content="{e(datos["frase"]["es"])}">
<meta name="theme-color" content="{t["bg"]}">
<meta property="og:title" content="{e(datos["nombre"]["es"])}">
<meta property="og:description" content="{e(datos["frase"]["es"])}">
<meta property="og:image" content="https://lanchasdev.github.io/{app["slug"]}/icono.jpg">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="https://lanchasdev.github.io/{app["slug"]}/">
{jsonld}
<link rel="icon" href="icono.jpg">
<link rel="apple-touch-icon" href="icono.jpg">
<script defer src="/assets/an.js" data-sitio="portfolio"></script>
<style>
:root{{--bg:{t["bg"]};--bg2:{t["bg2"]};--fg:{t["fg"]};--muted:{t["muted"]};--accent:{t["accent"]};--glow:{t["glow"]};
--card:{"rgba(255,255,255,.55)" if t.get("claro") else "rgba(255,255,255,.06)"};
--line:{"rgba(59,36,21,.14)" if t.get("claro") else "rgba(255,255,255,.12)"};
--btn:{"#1d130c" if t.get("claro") else "#fff"};--btnfg:{"#fff" if t.get("claro") else "#0b0b0f"}}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{background:var(--bg)}}
body{{min-height:100svh;color:var(--fg);font:16px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,sans-serif;
-webkit-font-smoothing:antialiased;background:radial-gradient(120% 70% at 50% -10%,color-mix(in srgb,var(--glow) 55%,transparent) 0%,transparent 60%),
linear-gradient(180deg,var(--bg2),var(--bg) 70%);overflow-x:hidden}}
.halo{{position:fixed;inset:-20% -20% auto;height:70vh;background:url(icono.jpg) center/cover;filter:blur(70px) saturate(1.4);
opacity:{".35" if t.get("claro") else ".28"};z-index:0;pointer-events:none}}
main{{position:relative;z-index:1;max-width:440px;margin:0 auto;padding:max(48px,env(safe-area-inset-top)) 20px
max(28px,env(safe-area-inset-bottom));display:flex;flex-direction:column;align-items:center;text-align:center}}
.icono{{position:relative;width:124px;height:124px;margin-bottom:22px;animation:entra .6s cubic-bezier(.2,.8,.2,1) both}}
.icono img{{width:100%;height:100%;border-radius:28px;display:block;box-shadow:0 18px 40px -12px rgba(0,0,0,.55),0 0 0 1px var(--line)}}
{'.icono::before{content:"";position:absolute;inset:-7px;border-radius:34px;background:conic-gradient(#22c55e,#eab308,#f97316,#ef4444,#d946ef,#6366f1,#0ea5e9,#22c55e);filter:blur(10px);opacity:.75;z-index:-1;animation:gira 8s linear infinite}' if t.get("anillo") else ""}
h1{{font-size:1.65rem;line-height:1.15;letter-spacing:-.02em;font-weight:750;animation:entra .6s .05s both}}
.frase{{color:var(--muted);margin-top:10px;font-size:1rem;max-width:34ch;animation:entra .6s .1s both}}
.pills{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin-top:16px;animation:entra .6s .15s both}}
.pills li{{font-size:.78rem;font-weight:600;padding:5px 11px;border-radius:99px;background:var(--card);border:1px solid var(--line);
backdrop-filter:blur(8px)}}
.pills .gratis,.pills .dl{{background:color-mix(in srgb,var(--accent) 22%,transparent);border-color:color-mix(in srgb,var(--accent) 45%,transparent)}}
.botones{{width:100%;display:flex;flex-direction:column;gap:12px;margin-top:28px;animation:entra .6s .2s both}}
.store{{display:flex;align-items:center;justify-content:center;gap:14px;height:64px;border-radius:18px;text-decoration:none;
color:var(--fg);background:var(--card);border:1px solid var(--line);backdrop-filter:blur(10px);font-size:1.25rem;font-weight:650;
letter-spacing:-.01em;transition:transform .15s ease,box-shadow .15s ease}}
.store svg{{width:28px;height:28px;flex:none}}
.store span{{display:flex;flex-direction:column;align-items:flex-start;line-height:1.05}}
.store small{{font-size:.68rem;font-weight:500;opacity:.75;letter-spacing:.01em;margin-bottom:3px}}
.store.primero{{background:var(--btn);color:var(--btnfg);border-color:transparent;height:70px;
box-shadow:0 14px 30px -12px color-mix(in srgb,var(--glow) 80%,transparent)}}
.store:active{{transform:scale(.97)}}
@media(hover:hover){{.store:hover{{transform:translateY(-2px)}}}}
.aviso{{font-size:.82rem;color:var(--muted);margin-top:2px}}
h2{{align-self:flex-start;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:38px 0 12px;font-weight:650}}
.capturas{{width:calc(100% + 40px);display:flex;gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;padding:0 20px 8px;
scrollbar-width:none;-webkit-overflow-scrolling:touch}}
.capturas::-webkit-scrollbar{{display:none}}
.capturas img{{flex:none;width:44%;max-width:190px;height:auto;aspect-ratio:auto;border-radius:16px;scroll-snap-align:start;
box-shadow:0 10px 24px -12px rgba(0,0,0,.6);border:1px solid var(--line);background:var(--card)}}
.info{{width:100%;text-align:left;margin-top:6px}}
.info h2{{margin-top:34px}}
.info p{{color:var(--fg);opacity:.9;margin:0 0 10px;font-size:.95rem}}
.info ul{{margin:4px 0 6px 18px;color:var(--muted);font-size:.9rem}}
.info li{{margin:4px 0}}
.faq{{margin-top:14px;display:flex;flex-direction:column;gap:8px}}
.faq details{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px}}
.faq summary{{cursor:pointer;font-weight:650;font-size:.92rem}}
.faq details p{{margin:8px 0 0;color:var(--muted);font-size:.9rem}}
footer{{margin-top:34px;font-size:.8rem;color:var(--muted)}}
footer a{{color:inherit;text-underline-offset:3px}}
@keyframes entra{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
@keyframes gira{{to{{filter:blur(10px) hue-rotate(360deg)}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
</head><body data-app="{app["slug"]}">
<div class="halo" aria-hidden="true"></div>
<main>
<div class="icono"><img src="icono.jpg" alt="" width="124" height="124"></div>
<h1 data-nombre>{e(datos["nombre"]["es"])}</h1>
<p class="frase" data-frase>{e(datos["frase"]["es"])}</p>
<ul class="pills"><li class="gratis" data-t="gratis">Gratis</li>{pill_desc}{etiquetas}</ul>
<div class="botones">
{ios}
<a class="store" id="play" href="https://play.google.com/store/apps/details?id={app["play"]}">{PLAY}<span><small data-t="play_sub">Disponible en</small>Google Play</span></a>
{'' if app["ios"] else '<p class="aviso" id="aviso" hidden data-t="solo_android"></p>'}
</div>
<h2 data-t="capturas">Así es por dentro</h2>
<div class="capturas">{capturas}</div>
{bloque_info}
<footer>{web}{privacidad}<a href="/" data-t="hecha">Hecha por Lanchas Dev</a></footer>
</main>
<script>
(function(){{
var D={datos_js};
var q=new URLSearchParams(location.search), s=(q.get("s")||q.get("utm_source")||"").replace(/[^\\w.-]/g,"").slice(0,40);
// El idioma del móvil, si la app lo tiene: primero el código entero (zh-TW), luego la raíz
// (pt-BR → pt). Si no hay ninguno, inglés. `?lang=xx` lo fuerza, para revisar cada uno.
var pedidos=[q.get("lang")].concat(navigator.languages||[navigator.language]).filter(Boolean), lang="";
for(var i=0;i<pedidos.length&&!lang;i++){{
  var c=pedidos[i].replace("_","-"), r=c.split("-")[0].toLowerCase();
  if(/^zh-(tw|hk|hant)/i.test(c)&&D.langs.indexOf("zh-TW")>=0) lang="zh-TW";
  else if(D.langs.indexOf(c)>=0) lang=c;
  else if(D.langs.indexOf(r)>=0) lang=r;
}}
if(!lang) lang=D.langs.indexOf("en")>=0?"en":"es";
var T=D.textos[lang], uno=function(o){{return o&&(o[lang]||o.en||o.es);}};
document.documentElement.lang=lang;
if(D.rtl.indexOf(lang)>=0) document.documentElement.dir="rtl";
if(lang!=="es"){{
  document.title=uno(D.nombre);
  document.querySelector("[data-nombre]").textContent=uno(D.nombre);
  document.querySelector("[data-frase]").textContent=uno(D.frase);
  var p=document.querySelectorAll(".pills li:not(.gratis):not(.dl)");
  (uno(D.etiquetas)||[]).forEach(function(x,i){{if(p[i])p[i].textContent=x;}});
  // Todas las apps con cifra tienen la misma («1K+»): el texto sale de textos.json.
  var dl=document.querySelector("[data-desc]"); if(dl&&D.descargas) dl.textContent=T.descargas;
  // Capturas solo hay en español e inglés: el resto de idiomas ve las inglesas.
  document.querySelector(".capturas").innerHTML=D.capturas.en.map(function(c){{
    return '<img src="'+c+'" alt="" loading="lazy" width="230" height="500">';}}).join("");
}}
document.querySelectorAll("[data-info]").forEach(function(n){{n.hidden=n.lang!==lang;}});
document.querySelectorAll("[data-t]").forEach(function(n){{n.textContent=T[n.dataset.t];}});
var ua=navigator.userAgent, android=/Android/.test(ua);
// El iPad se presenta como un Mac: lo delata que tenga pantalla táctil.
var ios=!android&&(/iPhone|iPad|iPod/.test(ua)||(navigator.platform==="MacIntel"&&navigator.maxTouchPoints>1));
var a=document.getElementById("ios"), g=document.getElementById("play"), cont=g.parentNode;
if(s){{
  if(a&&D.pt) a.href+="?pt="+D.pt+"&ct="+encodeURIComponent(s+"-"+D.slug)+"&mt=8";
  g.href+="&referrer="+encodeURIComponent("utm_source="+s+"&utm_medium=bio&utm_campaign="+D.slug);
}}
if(ios&&a){{a.classList.add("primero");}}
else if(android||!a){{g.classList.add("primero");cont.insertBefore(g,cont.firstChild);}}
else{{a.classList.add("primero");}}
if(ios&&!a){{var av=document.getElementById("aviso");if(av)av.hidden=false;}}
}})();
</script>
</body></html>
"""


def main():
    """`--bajar [slug…]` rehace icono, capturas y textos de esas apps (de todas si no se dice
    cuáles, menos las `fijas`); `--textos` solo vuelve a pedir a Play el nombre y la frase de
    cada idioma. Sin nada, rehace el HTML con lo ya bajado."""
    args = sys.argv[1:]
    pedidas = [a for a in args if not a.startswith("--")]
    for app in APPS:
        f = RAIZ / app["slug"] / "datos.json"
        bajar_esta = "--bajar" in args and (app["slug"] in pedidas or (not pedidas and not app.get("fijas")))
        if bajar_esta or not f.exists():
            datos = bajar(app)
        else:
            datos = json.loads(f.read_text())
            if "--textos" in args:
                datos = textos(app, datos)
                f.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
        (RAIZ / app["slug"] / "index.html").write_text(pagina(app, datos))
        print(f"{app['slug']:9} {datos['nombre']['es']} · {len(datos['capturas']['es'])} capturas")
    mapa()


def mapa():
    """robots.txt y sitemap.xml de todo el sitio, sacados de los index.html que hay.

    Sin ellos el sitio solo se descubre si alguien lo enlaza; con ellos los buscadores, y los
    asistentes que tiran de sus índices, encuentran también las páginas de cada app."""
    paginas = sorted(f.parent.relative_to(RAIZ).as_posix() for f in RAIZ.glob("**/index.html")
                     if not any(p.startswith((".", "_")) or p in ("node_modules", "enlaces")
                                for p in f.relative_to(RAIZ).parts))
    urls = "".join(f"<url><loc>https://lanchasdev.github.io/{'' if p == '.' else p + '/'}</loc></url>\n"
                   for p in paginas)
    (RAIZ / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      f"{urls}</urlset>\n")
    (RAIZ / "robots.txt").write_text("User-agent: *\nAllow: /\n\n"
                                     "Sitemap: https://lanchasdev.github.io/sitemap.xml\n")


if __name__ == "__main__":
    main()
