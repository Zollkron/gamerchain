# PlayerGold Landing Page

Landing page oficial para PlayerGold ($PRGLD) - La criptomoneda para gamers.

## Características

- **Diseño moderno y atractivo**: Interfaz one-page con animaciones suaves y diseño responsive
- **Detección automática de SO**: Detecta automáticamente el sistema operativo del usuario (Windows, macOS, Linux) y recomienda la descarga apropiada
- **Secciones informativas**: 
  - Hero con CTA principal
  - Sobre PlayerGold y características principales
  - Tecnología GamerChain y consenso PoAIP
  - Misión y valores del proyecto
  - Sección de descargas con opciones para cada SO
- **Responsive**: Optimizado para desktop, tablet y móvil
- **Animaciones**: Efectos de scroll y animaciones suaves para mejor UX

## Estructura de Archivos

```
web/
├── index.html          # Página principal HTML
├── styles.css          # Estilos CSS con diseño moderno
├── script.js           # JavaScript para detección de SO y funcionalidades
├── assets/
│   └── logo.svg        # Logo de PlayerGold
└── README.md           # Este archivo
```

## Tecnologías Utilizadas

- HTML5 semántico
- CSS3 con variables CSS y Grid/Flexbox
- JavaScript vanilla (sin dependencias)
- Google Fonts (Inter)

## Funcionalidades JavaScript

### Detección de Sistema Operativo

La página detecta automáticamente el sistema operativo del usuario usando:
- `navigator.platform`
- `navigator.userAgent`

Y recomienda la descarga apropiada del wallet.

### Smooth Scrolling

Navegación suave entre secciones usando scroll behavior nativo.

### Animaciones de Scroll

Elementos aparecen con animaciones cuando entran en el viewport usando Intersection Observer API.

### Efectos de Navbar

La barra de navegación cambia su apariencia al hacer scroll.

## Despliegue

### Desarrollo Local

Simplemente abre `index.html` en un navegador o usa un servidor local:

```bash
# Python
python -m http.server 8000

# Node.js
npx http-server

# PHP
php -S localhost:8000
```

Luego visita `http://localhost:8000`

### Producción

La página puede ser desplegada en cualquier servicio de hosting estático:

- **GitHub Pages**: Sube a un repositorio y activa GitHub Pages
- **Netlify**: Arrastra la carpeta `web/` a Netlify
- **Vercel**: Conecta el repositorio y despliega
- **AWS S3 + CloudFront**: Sube a S3 y configura CloudFront
- **Nginx/Apache**: Copia los archivos al directorio web del servidor

### Configuración de URLs de Descarga

En producción, actualiza las URLs de descarga en `script.js`:

```javascript
const downloadURLs = {
    'windows': 'https://releases.playergold.es/PlayerGold-Setup-Windows.exe',
    'macos': 'https://releases.playergold.es/PlayerGold-Setup-macOS.dmg',
    'linux': 'https://releases.playergold.es/PlayerGold-Setup-Linux.AppImage'
};
```

## Personalización

### Colores

Los colores se definen en variables CSS en `styles.css`:

```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --accent-color: #ec4899;
    /* ... más colores */
}
```

### Contenido

Todo el contenido está en `index.html` y puede ser editado directamente.

### Logo

Reemplaza `assets/logo.svg` con tu propio logo manteniendo las dimensiones 40x40px.

## Requisitos Cumplidos

✅ **Requisito 17.1**: Landing page de una sola página con diseño moderno y atractivo  
✅ **Requisito 17.2**: Sección destacando "hecho por gamers para gamers, totalmente libre, democrático y sin censura"  
✅ **Requisito 17.3**: Explicación de la misión de pagos justos sin censura  
✅ **Requisito 17.4**: Énfasis en administración mediante IA sin sesgos ideológicos  
✅ **Requisito 17.5**: Detección automática de SO para descargas del wallet  

## Navegadores Soportados

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Licencia

MIT License - Ver archivo LICENSE en la raíz del proyecto.

## Contacto

Para más información sobre PlayerGold, visita:
- GitHub: https://github.com/playergold
- Documentación: Ver `docs/Technical_Whitepaper.md`
