# 🚀 Quick Start - PlayerGold Landing Page

## Ver la Landing Page Localmente

### Opción 1: Python (Recomendado)
```bash
cd web
python -m http.server 8000
```
Luego abre tu navegador en: http://localhost:8000

### Opción 2: Node.js
```bash
cd web
npx http-server -p 8000
```
Luego abre tu navegador en: http://localhost:8000

### Opción 3: PHP
```bash
cd web
php -S localhost:8000
```
Luego abre tu navegador en: http://localhost:8000

### Opción 4: Abrir directamente
Simplemente abre el archivo `web/index.html` en tu navegador favorito.

## 🧪 Probar la Funcionalidad

### Test de Detección de SO
1. Abre `web/test-landing.html` en tu navegador
2. Verifica que detecta tu sistema operativo correctamente
3. Revisa que todos los requisitos están marcados como cumplidos

### Test de Navegación
1. Abre `web/index.html`
2. Haz clic en los enlaces del navbar
3. Verifica que el scroll es suave

### Test de Descargas
1. Abre `web/index.html`
2. Verifica que el botón principal muestra tu SO
3. Verifica que la card de descarga correspondiente está destacada

### Test Responsive
1. Abre `web/index.html`
2. Abre las DevTools (F12)
3. Activa el modo responsive (Ctrl+Shift+M)
4. Prueba diferentes tamaños de pantalla

## 📱 Dispositivos de Prueba

### Desktop
- Resolución: 1920x1080 o superior
- Navegadores: Chrome, Firefox, Edge, Safari

### Tablet
- Resolución: 768x1024
- Orientación: Portrait y Landscape

### Mobile
- Resolución: 375x667 (iPhone SE)
- Resolución: 414x896 (iPhone 11)
- Resolución: 360x640 (Android)

## 🎨 Personalización Rápida

### Cambiar Colores
Edita las variables CSS en `styles.css`:
```css
:root {
    --primary-color: #6366f1;    /* Tu color primario */
    --secondary-color: #8b5cf6;  /* Tu color secundario */
    --accent-color: #ec4899;     /* Tu color de acento */
}
```

### Cambiar Contenido
Edita el texto directamente en `index.html`. Todas las secciones están claramente marcadas con comentarios.

### Cambiar Logo
Reemplaza `assets/logo.svg` con tu propio logo (40x40px recomendado).

## 🐛 Solución de Problemas

### El servidor no inicia
- Verifica que estás en el directorio `web/`
- Verifica que Python/Node/PHP está instalado
- Prueba con otro puerto: `python -m http.server 8001`

### Las animaciones no funcionan
- Verifica que JavaScript está habilitado
- Abre la consola del navegador (F12) para ver errores
- Verifica que `script.js` se carga correctamente

### El diseño se ve roto
- Verifica que `styles.css` se carga correctamente
- Limpia la caché del navegador (Ctrl+Shift+R)
- Verifica que Google Fonts se carga (requiere internet)

### La detección de SO no funciona
- Abre la consola del navegador (F12)
- Ejecuta: `detectOS()`
- Debería retornar: 'windows', 'macos', o 'linux'

## 📚 Documentación Adicional

- **README.md**: Documentación completa del proyecto
- **IMPLEMENTATION_SUMMARY.md**: Resumen de la implementación
- **VERIFICATION.md**: Verificación de requisitos cumplidos

## 🚀 Desplegar a Producción

### GitHub Pages
```bash
git add web/
git commit -m "Add PlayerGold landing page"
git push origin main
```
Luego activa GitHub Pages en la configuración del repositorio.

### Netlify
1. Arrastra la carpeta `web/` a https://app.netlify.com/drop
2. O conecta tu repositorio Git

### Vercel
```bash
cd web
vercel deploy
```

## ✅ Checklist Pre-Despliegue

Antes de desplegar a producción, verifica:

- [ ] URLs de descarga actualizadas en `script.js`
- [ ] Logo final en `assets/logo.svg`
- [ ] Meta tags de SEO añadidos
- [ ] Google Analytics configurado (opcional)
- [ ] Pruebas en múltiples navegadores
- [ ] Pruebas en múltiples dispositivos
- [ ] Optimización de imágenes
- [ ] Minificación de CSS/JS (opcional)

## 🎉 ¡Listo!

Tu landing page de PlayerGold está lista para usar. Si tienes preguntas o encuentras problemas, consulta la documentación completa en `README.md`.

---

**PlayerGold** - Libertad financiera para gamers 🎮
