/* an.js — quién entra en la web y quién pulsa «descargar», en PostHog.
 *
 * Lo carga cada página con <script defer src="/assets/an.js"></script> y manda dos cosas:
 *
 *   $pageview  — una por página vista, con `fuente` (la red de la bio: ?s=tt|ig|yt) y,
 *                en las páginas de app, `app`.
 *   descarga   — cada clic en un enlace a App Store o Google Play, venga del índice o de
 *                una página de app, con `app`, `tienda`, `fuente` y `pagina`.
 *
 * Va a su propio proyecto de PostHog (`web`, 281538), no al de ninguna app: mezclarlos
 * obligaría a filtrar por una propiedad en todas las consultas de producto para siempre.
 *
 * Sin cookies y sin localStorage: `cookieless_mode: 'always'` hace que la identidad la
 * calcule PostHog en su servidor con un hash del día + IP + navegador, que caduca cada
 * 24 h. Por eso esta web no lleva banner de cookies, y por eso «visitantes» significa
 * «visitantes distintos ese día», no personas seguidas en el tiempo.
 *
 * El clic a la tienda se manda con `sendBeacon` a propósito: el navegador se va a la
 * tienda en el mismo instante, y una petición normal se queda a medias al descargar la
 * página. El beacon lo entrega el navegador aunque la página ya no esté.
 */
(function () {
  var TOKEN = 'phc_no447c6NMGBvvAZHX3mVHadBXjF6sks5ZvVFSULqbEUd';
  var HOST = 'https://eu.i.posthog.com';

  // La red de la que viene, tal cual la lleva la bio: ?s=tt (TikTok), ig, yt.
  var REDES = { tt: 'tiktok', ig: 'instagram', yt: 'youtube' };
  var s = new URLSearchParams(location.search).get('s') || '';
  var fuente = REDES[s] || s || 'directo';

  // La app de la página: en /mtc/, /anime/, /looksmax/ y /zodiaco/ la pone el generador
  // en <body data-app>. En el índice no hay una sola app, así que ahí va vacía y cada
  // clic dice la suya.
  var app = document.body.getAttribute('data-app') || '';
  var pagina = location.pathname;

  function tienda(url) {
    if (url.indexOf('apps.apple.com') > -1) return 'app store';
    if (url.indexOf('play.google.com') > -1) return 'google play';
    return '';
  }

  // Cuál es la app de ESTE enlace. En una página de app es la de la página; en el índice
  // es el nombre de su tarjeta, que es lo que se lee en la propia web.
  function deQuien(a) {
    if (app) return app;
    var tarjeta = a.closest ? a.closest('.card') : null;
    var nombre = tarjeta && tarjeta.querySelector('.name');
    return nombre ? nombre.textContent.replace(/\s*→\s*$/, '').trim() : 'desconocida';
  }

  function arranca() {
    if (!window.posthog || !window.posthog.init) return;
    window.posthog.init(TOKEN, {
      api_host: HOST,
      defaults: '2025-05-24',
      cookieless_mode: 'always',
      autocapture: false,            // los clics que importan se mandan a mano, con nombre
      disable_session_recording: true,
      capture_performance: false,
      capture_pageview: false      // la manda esta misma función, con `fuente` y `app` puestas
    });
    window.posthog.register({ fuente: fuente });
    if (app) window.posthog.register({ app: app });
    window.posthog.capture('$pageview');

    document.addEventListener('click', function (ev) {
      var a = ev.target.closest ? ev.target.closest('a[href]') : null;
      if (!a) return;
      var t = tienda(a.href);
      if (!t) return;
      window.posthog.capture('descarga', {
        app: deQuien(a),
        tienda: t,
        fuente: fuente,
        pagina: pagina,
        destino: a.href
      }, { transport: 'sendBeacon' });
    });
  }

  var js = document.createElement('script');
  js.src = 'https://eu-assets.i.posthog.com/static/array.js';
  js.async = true;
  js.crossOrigin = 'anonymous';
  js.onload = arranca;
  document.head.appendChild(js);
})();
