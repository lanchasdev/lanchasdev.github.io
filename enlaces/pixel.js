/* pixel.js — el píxel de Meta en medicinatradicionalchina.com/get, y solo ahí.
 *
 * Para qué: unas 6.000 visitas al mes llegan a /get desde Meta (promociones, DMs de
 * ManyChat, bio). Con el píxel, Meta puede (1) hacer públicos de quien entró y no pulsó la
 * tienda, para volver a enseñarles anuncios, y (2) optimizar las promociones por «llega a
 * la página» y por `Lead` (= clic a App Store o Play) en vez de por clic en el enlace.
 * Las instalaciones y compras NO salen de aquí: llegan por la Conversions API desde
 * RevenueCat al mismo conjunto de datos (3658317280998855, «Guía MTC»).
 *
 * Consentimiento: el píxel deja cookies de Meta, así que en el EEE, Reino Unido y Suiza
 * solo se carga si la persona pulsa «Aceptar» en un aviso pequeño; fuera, se carga directo.
 * El país sale de /cdn-cgi/trace (Cloudflare lo sirve en cualquier zona, sin worker). Si
 * eso falla, se trata como UE: mejor perder la medición que poner cookies sin permiso.
 * La elección se guarda en localStorage («mtc-pixel» = si|no), que es lo mínimo para
 * no preguntar en cada visita. El resto de la web sigue sin cookies.
 *
 * Lo pagado salta solo a la tienda a los ~1,5 s (tienda.js): en la UE no da tiempo a
 * aceptar, y está bien así; Meta ya sabe de esas personas por el propio clic en el anuncio.
 */
(function () {
  var ID = "3658317280998855", CLAVE = "mtc-pixel";
  var EEE = ("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE " +
             "IS LI NO GB CH").split(" ");
  var cargado = false;

  function guardado() { try { return localStorage.getItem(CLAVE); } catch (e) { return null; } }
  function guarda(v) { try { localStorage.setItem(CLAVE, v); } catch (e) {} }

  function carga() {
    if (cargado) return;
    cargado = true;
    /* El cargador oficial de Meta, tal cual. */
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
    n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
    document,'script','https://connect.facebook.net/en_US/fbevents.js');
    // Sin «automatic configuration»: que Meta no adivine eventos por los botones; los
    // mandamos nosotros. Sin coincidencias avanzadas: aquí no hay datos de nadie.
    fbq("set", "autoConfig", false, ID);
    fbq("init", ID);
    fbq("track", "PageView");
  }

  // Clic a la tienda → Lead. Se escucha siempre, pero solo manda si el píxel está cargado.
  // El píxel manda con una imagen, que el navegador cancela si la página se va: por eso,
  // con el píxel cargado, la salida a la tienda espera 300 ms. an.js no mira
  // defaultPrevented y manda su `descarga` con sendBeacon igual.
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("#ios, #play");
    if (!a || !cargado || !window.fbq) return;
    var c = window.mtcCampana || {};
    fbq("track", "Lead", {
      content_name: a.id === "ios" ? "app_store" : "google_play",
      content_category: c.utm_medium || "bio",
    });
    if (ev.defaultPrevented || ev.metaKey || ev.ctrlKey || ev.shiftKey || a.target === "_blank") return;
    ev.preventDefault();
    var destino = a.href;
    setTimeout(function () { location.href = destino; }, 300);
  }, true);

  var TXT = {
    es: ["Usamos el píxel de Meta (cookies) para medir nuestros anuncios.", "Aceptar", "No", "Más info"],
    en: ["We use the Meta pixel (cookies) to measure our ads.", "Accept", "No", "Learn more"],
    pt: ["Usamos o pixel da Meta (cookies) para medir os nossos anúncios.", "Aceitar", "Não", "Saber mais"],
    fr: ["Nous utilisons le pixel Meta (cookies) pour mesurer nos publicités.", "Accepter", "Non", "En savoir plus"],
    de: ["Wir nutzen das Meta-Pixel (Cookies), um unsere Anzeigen zu messen.", "Akzeptieren", "Nein", "Mehr"],
    it: ["Usiamo il pixel di Meta (cookie) per misurare i nostri annunci.", "Accetta", "No", "Info"],
  };

  function aviso() {
    var l = (document.documentElement.lang || "en").split("-")[0], t = TXT[l] || TXT.en;
    var d = document.createElement("div");
    d.id = "aviso-pixel";
    d.setAttribute("role", "dialog");
    d.setAttribute("aria-label", t[0]);
    d.style.cssText = "position:fixed;left:12px;right:12px;bottom:12px;z-index:50;max-width:520px;margin:0 auto;" +
      "padding:12px 14px;border-radius:14px;background:rgba(10,20,16,.94);color:#fff;font:14px/1.4 system-ui,sans-serif;" +
      "box-shadow:0 8px 30px rgba(0,0,0,.35);display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center";
    var p = document.createElement("span");
    p.style.cssText = "flex:1 1 220px";
    p.textContent = t[0] + " ";
    var info = document.createElement("a");
    info.href = "https://lanchasdev.github.io/privacidad/medicina-china/#web";
    info.textContent = t[3];
    info.style.cssText = "color:#9fe3c4";
    p.appendChild(info);
    var boton = function (texto, fuerte, v) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = texto;
      b.style.cssText = "border:0;border-radius:999px;padding:8px 16px;font:600 14px system-ui,sans-serif;cursor:pointer;" +
        (fuerte ? "background:#fff;color:#0b0b0f" : "background:rgba(255,255,255,.14);color:#fff");
      b.onclick = function () { guarda(v); d.remove(); if (v === "si") carga(); };
      return b;
    };
    d.appendChild(p);
    d.appendChild(boton(t[2], false, "no"));
    d.appendChild(boton(t[1], true, "si"));
    document.body.appendChild(d);
  }

  var ya = guardado();
  if (ya === "si") return carga();
  if (ya === "no") return;
  fetch("/cdn-cgi/trace", { cache: "no-store" })
    .then(function (r) { return r.text(); })
    .then(function (txt) {
      var m = /(?:^|\n)loc=([A-Z]{2})/.exec(txt);
      if (m && EEE.indexOf(m[1]) < 0) carga(); else aviso();
    })
    .catch(aviso);
})();
