# lanchasdev.github.io

La web de desarrollador de las apps de Lanchas Dev. Tiene tres cosas y ninguna
más:

- **`app-ads.txt`**, en la raíz. Es lo que declara qué redes tienen permiso para
  vender los huecos de anuncio de las apps. Va en la raíz del dominio a
  propósito: AdMob lo busca ahí y solo ahí, tomando el dominio de la web de
  desarrollador declarada en cada ficha de tienda. Una línea por cuenta de red,
  no por app, así que este único fichero cubre las once.
- **El índice**, con las apps y sus enlaces a las tiendas.
- **Las políticas de privacidad**, una por app: las once, sin pendientes. Cada
  app recoge cosas distintas y copiar la de otra sería declarar lo que no hace,
  así que cada una está escrita contra el código de SU app. Cuatro dicen que no
  recogen nada porque no recogen nada; la de Medicina China es larga porque es
  la única con cuentas, sincronización y suscripción.

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
