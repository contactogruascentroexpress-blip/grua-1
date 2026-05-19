#!/usr/bin/env python3
"""
GCE Frontend Protection & Optimization Script
Genera src/index.html (desarrollo) y dist/index.html (producción).
"""

import re, os, json

INPUT   = '/home/user/grua-1/index.html'
SRC_OUT = '/home/user/grua-1/src/index.html'
DIST_OUT = '/home/user/grua-1/dist/index.html'
MAP_OUT  = '/home/user/grua-1/src/class-mapping.json'

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# ================================================================
# FASE 1 — Leer fuente original
# ================================================================
src = read_file(INPUT)
print(f'Fuente leída: {len(src):,} bytes / {src.count(chr(10))+1} líneas')

# ================================================================
# FASE 2 — Versión DESARROLLO: limpiar + cabecera de autoría
# ================================================================
dev_header = (
    '<!-- ============================================================\n'
    '     GRÚAS CENTRO EXPRESS — versión DESARROLLO\n'
    '     © 2025 Grúas Centro Express. Todos los derechos reservados.\n'
    '     Diseño y código propietario — prohibida reproducción.\n'
    '     Mantenedor: +56984062331\n'
    '     ============================================================ -->\n'
)
write_file(SRC_OUT, dev_header + src)
print('✓ src/index.html escrito (versión desarrollo)')

# ================================================================
# FASE 3 — Extraer CSS y JS para análisis de clases
# ================================================================
css_match = re.search(r'<style>(.*?)</style>', src, re.DOTALL)
css_raw   = css_match.group(1) if css_match else ''

all_js = ''
for m in re.finditer(r'<script(?:\s[^>]*)?>([^<]*(?:<(?!/script>)[^<]*)*)</script>', src, re.DOTALL):
    all_js += m.group(1) + '\n'

# Clases definidas en CSS
css_defined = set(re.findall(r'\.(-?[a-zA-Z][a-zA-Z0-9_-]*)', css_raw))

# Clases referenciadas como strings en JS → NO renombrar
js_protected = set()
for m in re.finditer(r"""['"`]([a-zA-Z][a-zA-Z0-9_ -]*)['"`]""", all_js):
    for token in m.group(1).split():
        js_protected.add(token)

# Clases de estado usadas dinámicamente → proteger siempre
ALWAYS_PROTECT = {
    'active', 'visible', 'hidden', 'open', 'closed', 'show', 'hide',
    'cursor-hover', 'glitch-active', 'wa-typing-wrap', 'reveal',
    'magnetic-btn',   # tiene listener JS
}

safe_to_rename = css_defined - js_protected - ALWAYS_PROTECT
print(f'Clases CSS: {len(css_defined)} | JS-protegidas: {len(js_protected)} | Renombrables: {len(safe_to_rename)}')

# ================================================================
# FASE 4 — Construir tabla de mapeo CSS
# ================================================================
def encode_index(n):
    """Genera nombre corto tipo x0, xa, xb … xz, x10 …"""
    chars = 'abcdefghijklmnopqrstuvwxyz'
    if n < 26:
        return chars[n]
    return chars[(n // 26) - 1] + chars[n % 26]

CLASS_MAP = {}
for i, cls in enumerate(sorted(safe_to_rename)):
    CLASS_MAP[cls] = 'x' + encode_index(i)

write_file(MAP_OUT, json.dumps(CLASS_MAP, indent=2, ensure_ascii=False))
print(f'✓ src/class-mapping.json: {len(CLASS_MAP)} entradas')

# ================================================================
# FASE 5 — Aplicar mapeo al código fuente completo
# ================================================================
prod = src

# 5a. Reemplazar en atributos class="..." del HTML
def replace_html_classes(m):
    tokens = m.group(1).split()
    renamed = ' '.join(CLASS_MAP.get(t, t) for t in tokens)
    return f'class="{renamed}"'

prod = re.sub(r'class="([^"]+)"', replace_html_classes, prod)

# 5b. Reemplazar selectores en CSS  (.nombre → .xNN)
def replace_css_class(m):
    cls = m.group(1)
    new = CLASS_MAP.get(cls)
    return ('.' + new) if new else m.group(0)

prod = re.sub(
    r'\.(-?[a-zA-Z][a-zA-Z0-9_-]*)',
    replace_css_class,
    prod
)

# ================================================================
# FASE 6 — Eliminar comentarios HTML (conservar GTM y noscript)
# ================================================================
def strip_html_comment(m):
    c = m.group(0)
    if '[if' in c or 'Google Tag Manager' in c or 'End Google Tag Manager' in c:
        return c
    return ''

prod = re.sub(r'<!--.*?-->', strip_html_comment, prod, flags=re.DOTALL)

# ================================================================
# FASE 7 — Eliminar comentarios CSS dentro de <style>
# ================================================================
def strip_css_comments(m):
    css = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.DOTALL)
    return m.group(1) + css + m.group(3)

prod = re.sub(r'(<style>)(.*?)(</style>)', strip_css_comments, prod, flags=re.DOTALL)

# ================================================================
# FASE 8 — Eliminar comentarios JS dentro de <script> (no GTM, no JSON-LD)
# ================================================================
def strip_js_comments(m):
    tag, js, end = m.group(1), m.group(2), m.group(3)
    if 'googletagmanager' in js or 'GTM-' in js:
        return m.group(0)
    if 'application/ld+json' in tag:
        return m.group(0)
    if 'src=' in tag:
        return m.group(0)
    # Multi-line comments
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
    # Single-line comments (respetar https://)
    js = re.sub(r'(?<![:"\'`])//[^\n]*', '', js)
    return tag + js + end

prod = re.sub(
    r'(<script(?:\s[^>]*)?>)(.*?)(</script>)',
    strip_js_comments, prod, flags=re.DOTALL
)

# ================================================================
# FASE 9 — Minificar CSS dentro de <style>
# ================================================================
def minify_css(m):
    css = m.group(2)
    css = re.sub(r'\t', ' ', css)
    css = '\n'.join(l.strip() for l in css.split('\n'))
    css = re.sub(r'\n+', ' ', css)
    css = re.sub(r' {2,}', ' ', css)
    css = re.sub(r' *\{ *', '{', css)
    css = re.sub(r' *\} *', '}', css)
    css = re.sub(r' *; *', ';', css)
    css = re.sub(r';+\}', '}', css)
    css = css.strip()
    return m.group(1) + css + m.group(3)

prod = re.sub(r'(<style>)(.*?)(</style>)', minify_css, prod, flags=re.DOTALL)

# ================================================================
# FASE 10 — Minificar JS dentro de <script> (no GTM, no JSON-LD)
# ================================================================
def minify_js(m):
    tag, js, end = m.group(1), m.group(2), m.group(3)
    if 'googletagmanager' in js or 'GTM-' in js:
        return m.group(0)
    if 'application/ld+json' in tag:
        return m.group(0)
    if 'src=' in tag:
        return m.group(0)
    # Colapsar espacios (conservador: no tocar operadores)
    lines = [l.strip() for l in js.split('\n')]
    js = ' '.join(l for l in lines if l)
    js = re.sub(r' {2,}', ' ', js)
    return tag + js + end

prod = re.sub(
    r'(<script(?:\s[^>]*)?>)(.*?)(</script>)',
    minify_js, prod, flags=re.DOTALL
)

# ================================================================
# FASE 11 — Minificar estructura HTML (colapsar espacio entre tags)
# ================================================================
# Quitar líneas vacías y espacios iniciales/finales
lines = [l.strip() for l in prod.split('\n') if l.strip()]
prod = '\n'.join(lines)
# Colapsar espacios múltiples (fuera de tags pre/textarea)
prod = re.sub(r'> {2,}<', '> <', prod)

# ================================================================
# FASE 12 — Copyright: verificar/actualizar footer
# ================================================================
COPY_TEXT = '© Grúas Centro Express. Todos los derechos reservados.'

if COPY_TEXT not in prod:
    # Insertar dentro del footer si existe, o antes de </body>
    copy_html = (
        f'<p style="text-align:center;font-size:.75rem;'
        f'color:#7a7a82;padding:16px 0 4px">{COPY_TEXT}</p>'
    )
    if '</footer>' in prod:
        prod = prod.replace('</footer>', copy_html + '</footer>', 1)
    else:
        prod = prod.replace('</body>', copy_html + '</body>', 1)
    print('✓ Copyright agregado al footer')
else:
    print('✓ Copyright ya presente en footer')

# ================================================================
# FASE 13 — Meta copyright + anti-indexación de copia
# ================================================================
copy_meta = (
    '<meta name="copyright" content="© 2025 Grúas Centro Express"/>'
    '<meta name="author" content="Grúas Centro Express"/>'
)
prod = prod.replace('<meta charset="UTF-8"/>', '<meta charset="UTF-8"/>' + copy_meta, 1)

# ================================================================
# FASE 14 — Anti-copia JS: imágenes + marca en consola
# ================================================================
anti_copy = (
    '<script>'
    '(function(){'
    # Deshabilitar clic derecho solo en imágenes
    'document.addEventListener("contextmenu",function(e){'
    'if(e.target.tagName==="IMG"){e.preventDefault();}},false);'
    # Deshabilitar drag de imágenes
    'document.querySelectorAll("img").forEach(function(i){'
    'i.setAttribute("draggable","false");'
    'i.addEventListener("dragstart",function(e){e.preventDefault();});});'
    # Marca de autoría en consola
    'if(window.console&&console.log){'
    'console.log("%c© Grúas Centro Express","color:#f5c400;font-weight:bold;font-size:14px");'
    'console.log("%cCódigo propietario. Prohibida reproducción.","color:#e03c2f;font-size:11px");}'
    '})();'
    '</script>'
)
prod = prod.replace('</body>', anti_copy + '</body>', 1)

# ================================================================
# FASE 15 — Escribir dist/index.html
# ================================================================
write_file(DIST_OUT, prod)

orig_size = len(src.encode('utf-8'))
prod_size = len(prod.encode('utf-8'))
print(f'✓ dist/index.html escrito')
print(f'  Original : {orig_size:,} bytes')
print(f'  Producción: {prod_size:,} bytes')
print(f'  Reducción : {(1 - prod_size/orig_size)*100:.1f}%')

# ================================================================
# RESUMEN DE CLASES RENOMBRADAS (muestra)
# ================================================================
sample = list(CLASS_MAP.items())[:20]
print('\nMuestra de clases renombradas:')
for old, new in sample:
    print(f'  .{old:30s} → .{new}')
if len(CLASS_MAP) > 20:
    print(f'  ... y {len(CLASS_MAP)-20} más (ver src/class-mapping.json)')
