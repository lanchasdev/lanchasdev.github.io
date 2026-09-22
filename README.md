# lanchasdev.github.io

La web de desarrollador de las apps de Lanchas Dev. Tiene cinco cosas y ninguna
más:

- **`app-ads.txt`**, en la raíz. Es lo que declara qué redes tienen permiso para
  vender los huecos de anuncio de las apps. Va en la raíz del dominio a
  propósito: AdMob lo busca ahí y solo ahí, tomando el dominio de la web de
  desarrollador declarada en cada ficha de tienda. Una línea por cuenta de red,
  no por app, así que este único fichero cubre las once.
- **El índice**, con las apps y sus enlaces a las tiendas.
- **Las páginas de enlace para la bio** de TikTok, Instagram y YouTube: `/mtc/`,
  `/anime/`, `/looksmax/` y `/zodiaco/`. Estas sí se generan, con
  `python3 enlaces/generar.py --bajar` (nombre, frase, icono y capturas salen de
  las fichas de las tiendas; los colores y las etiquetas están en el propio
  script). En la bio va con la red detrás, `lanchasdev.github.io/mtc?s=tt`
  (`ig`, `yt`), y la página se lo pasa a Play como `utm_source`.
- **Las políticas de privacidad**, una por app: las once, sin pendientes. Cada
  app recoge cosas distintas y copiar la de otra sería declarar lo que no hace,
  así que cada una está escrita contra el código de SU app. Cuatro dicen que no
  recogen nada porque no recogen nada; la de Medicina China es larga porque es
  la única con cuentas, sincronización y suscripción.

- **La medición**, `assets/an.js`, que carga cada página. Manda a PostHog dos
  cosas y ninguna más: un `$pageview` por página vista y un evento `descarga`
  por cada clic en un botón de App Store o Google Play, con la app, la tienda y
  la red de la que venía (`?s=tt|ig|yt`). Es lo que cierra el círculo: la página
  de la bio ya decía a la tienda de dónde venía el clic, pero no se sabía cuánta
  gente llegaba y no pulsaba.

El armazón (estilo, cabecera, migas) es el mismo en todas y sale de copiar el de
una existente. El texto no se genera: se escribe leyendo qué SDK lleva la app,
qué permisos pide y a dónde llama. Cuando una app cambie lo que recoge, se toca
su página; no hay plantilla que regenerar.

**El enlace que hay que declarar en la ficha** es
`https://lanchasdev.github.io/privacidad/<slug>/`, y el mismo tiene que ir en el
botón de privacidad DENTRO de la app. Si los dos no coinciden, la tienda enseña
uno y el usuario ve otro.

## Para que AdMob lo dé por bueno

En cada ficha hay que declarar este dominio como **web de desarrollador** — que
no es el campo de la política de privacidad:

- Google Play: datos de contacto de la ficha.
- App Store Connect: *Marketing URL* de la versión.

AdMob lo rastrea en unas 24 horas y enseña el estado en Anuncios → Configuración
→ app-ads.txt.

## Qué mide la web y qué no

Los datos van a su propio proyecto de PostHog (**web**, `281538`, en la nube
europea), no al de ninguna app: mezclar la web con el producto obliga a filtrar
por una propiedad en todas las consultas para siempre. El panel está en
<https://eu.posthog.com/project/281538/dashboard/968605>.

No hay banner de cookies porque no hay cookies: `an.js` arranca PostHog en modo
`cookieless`, sin cookies ni `localStorage`, y la identidad la calcula el
servidor de PostHog con un hash del día, la IP y el navegador que caduca cada
24 h. La consecuencia hay que tenerla delante al leer los números: «visitantes»
son visitantes distintos **ese día**, no personas seguidas en el tiempo, y quien
vuelve mañana cuenta como nuevo.

El clic a la tienda se manda con `sendBeacon`: el navegador se va a App Store en
el mismo instante y una petición normal se quedaría a medias. Los `$pageview`
que salgan de `localhost` están marcados como tráfico interno en el proyecto, no
ensucian el panel.
