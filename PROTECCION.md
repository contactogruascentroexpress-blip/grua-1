# Grúas Centro Express — Protección y Optimización Frontend

**Versión:** 1.0.0  
**Fecha:** 2025-05-19  
**Proyecto:** gruascentroexpress.cl  
**Autor:** Grúas Centro Express

---

## 1. Estructura del proyecto

```
grua-1/
├── index.html              ← Fuente original (sin modificar)
├── build.py                ← Script de compilación/protección
├── PROTECCION.md           ← Este documento
├── src/
│   ├── index.html          ← Versión DESARROLLO (editable, con cabecera autoría)
│   └── class-mapping.json  ← Tabla de clases CSS renombradas
└── dist/
    └── index.html          ← Versión PRODUCCIÓN (protegida, minificada)
```

---

## 2. Archivos modificados

| Archivo | Acción |
|---|---|
| `dist/index.html` | Producción: minificado + clases ofuscadas + protecciones |
| `src/index.html` | Desarrollo: copia con cabecera de autoría |
| `src/class-mapping.json` | Tabla de mapeo clases originales → ofuscadas |
| `build.py` | Script Python que genera src/ y dist/ |

El archivo `index.html` raíz **no fue modificado** y permanece como fuente de verdad.

---

## 3. Medidas de protección aplicadas

### 3.1 Ofuscación de clases CSS (140 clases renombradas)

Todas las clases CSS que no son referenciadas por nombre en JavaScript fueron renombradas a identificadores cortos y sin significado:

```
.hero          → .xau
.service-card  → .xcn
.services-grid → .xcq
.container     → .xq
.section-title → .xck
.cotizador-form → .xs
.trust-card    → .xde
.gallery-item  → .xas
.btn-yellow    → .xo
.topbar        → .xcy
.footer        → .xah
.hero-title    → .xbi
.hero-content  → .xay
```

El listado completo está en `src/class-mapping.json`.

Las clases **no renombradas** son aquellas que JavaScript añade dinámicamente (`active`, `visible`, `cursor-hover`, `glitch-active`, `reveal`, etc.). Renombrarlas sin modificar el JS rompería las animaciones y el comportamiento interactivo.

### 3.2 Eliminación de comentarios

- Todos los comentarios HTML `<!-- ... -->` eliminados, salvo:
  - Bloque Google Tag Manager (necesario para GTM)
- Todos los comentarios CSS `/* ... */` eliminados
- Todos los comentarios JS `//` y `/* */` eliminados, salvo:
  - Scripts del GTM (no se tocan)
  - Bloque JSON-LD de Schema.org (no se toca)

### 3.3 Minificación

- **HTML**: líneas colapsadas de 3.123 a 787 (75% reducción de líneas)
- **CSS**: espacios y saltos eliminados dentro del bloque `<style>`
- **JS**: espacios y líneas en blanco eliminados en bloques `<script>`
- **Tamaño total**: 125.876 bytes → 97.148 bytes (−22.8%)

### 3.4 Anti-copia de imágenes

Script añadido al final del `<body>` que:
- Desactiva el **clic derecho** sobre elementos `<img>`
- Desactiva el **arrastre** de imágenes (`draggable="false"` + listener `dragstart`)
- Muestra **marca de autoría en la consola** de DevTools:
  ```
  © Grúas Centro Express  [amarillo]
  Código propietario. Prohibida reproducción.  [rojo]
  ```

No se aplicaron bloqueos invasivos que afecten la experiencia del usuario general.

### 3.5 Copyright y metadatos

- **Footer**: texto `© Grúas Centro Express. Todos los derechos reservados.` asegurado
- **Meta tags añadidos**:
  ```html
  <meta name="copyright" content="© 2025 Grúas Centro Express"/>
  <meta name="author" content="Grúas Centro Express"/>
  ```
- **Versión desarrollo**: cabecera con datos de autoría, fecha y datos de contacto

### 3.6 Preservado intacto (sin cambios)

| Elemento | Estado |
|---|---|
| Google Tag Manager (`GTM-M8W57L6F`) | ✓ Intacto |
| Schema.org JSON-LD (LocalBusiness) | ✓ Intacto |
| `<meta name="description">` | ✓ Intacto |
| `<meta name="robots">` | ✓ Intacto |
| `<link rel="canonical">` | ✓ Intacto |
| Open Graph / Twitter Cards | ✓ Intactos |
| Coordenadas geo y areaServed | ✓ Intactos |
| `tel:+56984062331` | ✓ Intacto |
| `wa.me/56984062331` | ✓ Intacto |
| Formulario cotizador (lógica de precios) | ✓ Intacto |
| Animaciones JS (glitch, partículas, cursor) | ✓ Intactas |
| Chat WhatsApp animado | ✓ Intacto |
| Accesibilidad (ARIA, roles) | ✓ Intactos |
| Responsive / media queries | ✓ Intactos |

---

## 4. Qué NO se puede ocultar (limitaciones del navegador)

Por diseño, cualquier navegador debe poder mostrar el código al usuario. Estas cosas **siempre serán visibles** desde DevTools:

- **El HTML estructural** (aunque con clases ofuscadas y sin comentarios)
- **El CSS final** en el panel Styles (aunque con nombres como `.xcn`)
- **El JavaScript** en el panel Sources (aunque sin comentarios y colapsado)
- **Las imágenes** (visibles en el panel Network aunque no se puedan arrastrar)
- **Los textos de contenido** (títulos, descripciones, precios) — son texto visible
- **Las fuentes** y recursos externos (Google Fonts, GTM)

**La protección no es invisibilidad** — es aumentar el costo de copiar y dejar menos código reutilizable directamente.

---

## 5. Cómo volver a editar sin perder la protección

1. **Edita siempre `index.html` (raíz)** — el archivo original, no el dist/
2. Cuando los cambios estén listos, ejecuta:
   ```bash
   python3 build.py
   ```
3. Esto regenera automáticamente:
   - `src/index.html` (versión desarrollo con cabecera)
   - `dist/index.html` (versión producción protegida)
   - `src/class-mapping.json` (actualizado con nuevas clases)
4. **Sube al servidor el contenido de `dist/`**, nunca el `index.html` raíz

---

## 6. Recomendaciones adicionales

### Técnicas (implementables)

- [ ] **Separar `dist/` a rama de despliegue** en Git para tener historial de compilaciones
- [ ] **Convertir imágenes a WebP/AVIF**: reduce peso y dificulta extracción directa
- [ ] **Servir desde CDN con hotlink protection**: impide que terceros enlacen tus imágenes desde otros dominios
- [ ] **Subresource Integrity (SRI)**: si usas recursos externos, añadir `integrity=` para prevenir manipulación
- [ ] **Content Security Policy (CSP)**: cabecera HTTP que controla qué scripts/estilos se pueden cargar
- [ ] **Marca de agua invisible en imágenes**: herramientas como Digimarc o scripts Python (OpenCV) pueden embeber metadata invisible
- [ ] **Renombrar imágenes** de `servicio-nocturno.jpg` a nombres sin significado (ej. `i4k9.webp`)
- [ ] **Lazy loading adicional** con `loading="lazy"` en imágenes del gallery (ya tiene algunas)

### Legales (altamente recomendadas)

- [ ] **Registrar el diseño ante INAPI** (Chile): el diseño visual puede registrarse como obra visual
- [ ] **Carta documento ante infractores**: con prueba de autoría (commits Git fechados) es suficiente base legal
- [ ] **Google DMCA**: si alguien copia y posiciona el sitio, presentar denuncia en [dmca.google.com](https://dmca.google.com) para quitar el sitio copión de los resultados
- [ ] **Repositorio Git privado como prueba**: el historial de commits fechados es evidencia de autoría ante tribunales

### Comerciales

- [ ] **Marca registrada del logo** ante INAPI
- [ ] **Certificado de autoría** con notario del diseño original (con capturas fechadas)

---

## 7. Evidencia de autoría recomendada

Mantener como prueba:

1. **Este repositorio Git** con historial de commits fechados
2. **Capturas de pantalla** del sitio con fecha (usar herramienta como web.archive.org)
3. **Registro en Archive.org**: acceder a [web.archive.org/save](https://web.archive.org/save) y guardar una captura de cada versión
4. **El archivo `src/index.html`** con la cabecera de autoría fechada
5. **El archivo `src/class-mapping.json`** como prueba de que el código dist es derivado del original

---

*Documento generado automáticamente por build.py — Grúas Centro Express © 2025*
