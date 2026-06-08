# EduTrack WebView Android

Este proyecto es una app Android mínima que carga tu sitio web en una `WebView`.

## Qué hace
- Abre la URL: `https://edutrack-39tm.onrender.com`
- Usa `WebView` con JavaScript y DOM storage habilitados
- Requiere conexión a Internet para funcionar

## Cómo usarlo

### Opción 1: Android Studio
1. Abre Android Studio.
2. Selecciona `Open` y elige la carpeta `android-webview`.
3. Deja que Android Studio sincronice el proyecto y descargue dependencias.
4. Ejecuta el proyecto en un emulador o dispositivo.
5. Para generar APK: `Build > Build Bundle(s) / APK(s) > Build APK(s)`.

### Opción 2: línea de comandos (si tienes Gradle instalado)
En la carpeta `android-webview`:

```bash
./gradlew assembleRelease
```

El APK generado se encontrará en `app/build/outputs/apk/release/app-release.apk`.

## Cambiar la URL
Si deseas apuntar a otro servidor, edita `MainActivity.java` y modifica la constante:

```java
private static final String APP_URL = "https://edutrack-39tm.onrender.com";
```

## Nota
Esta app solo muestra la versión web de tu proyecto. No convierte el backend Python a Android.
