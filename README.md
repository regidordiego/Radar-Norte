# NORTE Radar · Valgrande y Cerro del Baile

Panel web estático de seguimiento de promociones en **Alcobendas** y **San Sebastián de los Reyes**. Incluye formularios/enlaces oficiales contrastados a fecha **10 de noviembre de 2026**, un registro editable de solicitudes y un robot que revisa fuentes públicas para detectar nuevos titulares y cambios de páginas.

## Abrir ahora

Abre `index.html` en tu navegador. Las tarjetas, enlaces, filtros y el seguimiento funcionan sin instalar nada. Si lo abres directamente como archivo local, las noticias serán las del último `data/updates.json` embebidas como datos iniciales; para cargar el JSON actualizado, sirve la carpeta con un servidor local o publícala.

Servidor local opcional:

```bash
python -m http.server 8000
```

Visita <http://localhost:8000>.

## Activar la web en GitHub Pages

1. Crea un repositorio nuevo en tu cuenta de GitHub y sube **el contenido** de esta carpeta (incluyendo `.github/workflows`).
2. En **Settings → Pages**, selecciona **Deploy from a branch → main → /(root)**.
3. En **Actions → Actualizar radar inmobiliario → Run workflow**, ejecuta la primera revisión manual.
4. Después, GitHub Actions revisará automáticamente las fuentes aproximadamente dos veces al día y actualizará `data/updates.json` si puede leerlas.
5. Abre la URL de Pages (GitHub la mostrará en Settings → Pages). El radar cargará sus noticias actualizadas automáticamente cada vez que visites la web; para ver nuevos resultados con la web abierta, recarga.

**Privacidad:** un GitHub Pages público y un repositorio público hacen visible el código inicial. El historial personal que edites después en la web se guarda localmente en tu navegador, NO se sube automáticamente a GitHub. No añadas información privada al repositorio. La lista inicial de entidades contactadas forma parte del HTML entregado; si no quieres hacerla pública, bórrala de `INITIAL_CONTACTS` antes de publicar. También puedes usar un alojamiento privado o con autenticación.

## Qué hace y qué NO hace

- ✅ Muestra 4 fichas de referencia con enlaces a las fuentes reales.
- ✅ Permite filtrar Valgrande / Cerro del Baile.
- ✅ Guarda manualmente estados y notas por dispositivo en `localStorage`.
- ✅ Exporta / importa las gestiones mediante JSON.
- ✅ Revisa fuentes públicas y RSS (Google News), y detecta **cambios**, si se configura GitHub Actions.
- ❌ **No** comprueba automáticamente que exista disponibilidad real ni te inscribe en ninguna promoción.
- ❌ **No** convierte titulares o cambios de web en «nuevos pisos disponibles» sin revisión humana.
- ❌ **No** lee tu correo electrónico ni detecta respuestas de promotoras.
- ❌ **No** sincroniza notas entre dispositivos ni lanza notificaciones push desde esta web.

**Los avisos personalizados de ChatGPT** son un proceso independiente de GitHub Actions y no escriben en este repositorio.

## Editar promociones

Las tarjetas iniciales se encuentran en el array `OPP` de `index.html`. Los contactos iniciales están en `INITIAL_CONTACTS`. Si editas esos arrays, cambia la información estática que verá cualquier usuario nuevo; no afectará a las notas ya guardadas en `localStorage`.

El programa `monitor.py` analiza RSS y compara versiones simplificadas del texto visible de las páginas monitorizadas; el sistema puede detectar cambios de diseño o texto sin relevancia y puede omitir novedades publicadas solo en redes sociales, PDF, portales con inicio de sesión, formularios no indexados o páginas que bloqueen robots.

## Fuentes iniciales

- https://emvialsa.org/acceso-a-la-vivienda/inscripciones
- https://valgrandealcobendas.es/
- https://cerrodelbaile.es/
- https://cooperopen.org/valgrande
- https://cooperopen.org/san-sebastian-de-los-reyes
- https://www.pisosenvalgrande.es/
- https://www.grupoibosa.com/
- https://alcobi.es/ciudad/valgrande/vivienda/

## Nota para cooperativas

Antes de aportar dinero, solicita información escrita sobre la situación jurídica del suelo, proyecto urbanístico, licencia, condiciones del depósito, cuenta especial, avales/seguros y calendario. No te apoyes únicamente en las etiquetas del radar para tomar decisiones económicas.
