# lanchasdev.github.io

La web de desarrollador de las apps de Lanchas Dev. Tiene tres cosas y ninguna
más:

- **`app-ads.txt`**, en la raíz. Es lo que declara qué redes tienen permiso para
  vender los huecos de anuncio de las apps. Va en la raíz del dominio a
  propósito: AdMob lo busca ahí y solo ahí, tomando el dominio de la web de
  desarrollador declarada en cada ficha de tienda. Una línea por cuenta de red,
  no por app, así que este único fichero cubre las once.
- **El índice**, con las apps y sus enlaces a las tiendas.
- **Las políticas de privacidad**, una por app. De momento solo está la de Anime
  Food: cada app recoge cosas distintas y copiar la de otra sería declarar lo
  que no hace.

Se genera con el script del kit a partir de `apps.toml`, así que para añadir una
app se toca allí y se vuelve a generar, no se edita el HTML a mano.

## Para que AdMob lo dé por bueno

En cada ficha hay que declarar este dominio como **web de desarrollador** — que
no es el campo de la política de privacidad:

- Google Play: datos de contacto de la ficha.
- App Store Connect: *Marketing URL* de la versión.

AdMob lo rastrea en unas 24 horas y enseña el estado en Anuncios → Configuración
→ app-ads.txt.
