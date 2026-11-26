# Обычные страницы clue (контакты, о студии, политика): в src/pages/<slug>.html лежит только содержимое,
# а шапка, меню, футер и окно заявки берутся с главной. Пишет docs/<slug>/index.html
#
# В начале файла страницы — служебные строки:
#   <!--title: Контакты — clue-->
#   <!--description: Как связаться со студией clue ...-->
#   <!--nav: kontakty-->        какой пункт меню подсветить (proekty, uslugi, o-studii, kontakty)
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_service import HEADER, MNAV, FOOTER, MODAL, rebase, esc, SRC, OUT

# корень сайта: '/' для своего домена; для адреса вида user.github.io/repo/ — '/repo/'
SITE_BASE = '/'

def meta(src, key):
    m = re.search(r'<!--' + key + r':\s*(.*?)-->', src)
    return m.group(1).strip() if m else ''

def page(slug, src):
    title, desc, nav = meta(src, 'title'), meta(src, 'description'), meta(src, 'nav')
    body = re.sub(r'<!--(title|description|nav):.*?-->\n?', '', src)
    cur = HEADER
    if nav == 'uslugi':
        cur = cur.replace('class="pill dd__btn"', 'class="pill dd__btn" aria-current="page"', 1)
    elif nav:
        cur = re.sub(r'(<a class="pill" href="' + nav + r'/")', r'\1 aria-current="page"', cur, count=1)
    head = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#F2F2F2">
<link rel="icon" type="image/svg+xml" href="assets/img/logo/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/logo/favicon-32.png">
<link rel="apple-touch-icon" href="assets/img/logo/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/InterDisplay-Regular.woff" as="font" type="font/woff" crossorigin>
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add('js');setTimeout(function(){{document.documentElement.classList.add('ft-done')}},2500)</script>
</head>
<body class="page-{slug.replace('/', '-')}">
<a class="skip" href="#main">Перейти к содержанию</a>

'''
    out = head + cur + MNAV + '<main id="main">\n\n' + body + '\n</main>\n\n' + FOOTER + MODAL + '<script src="assets/js/main.js" defer></script>\n</body>\n</html>\n'
    parts = slug.split('/')
    return rebase(out, len(parts), parts[0])

def build_all():
    pages = os.path.join(SRC, 'pages')
    done = []
    for f in sorted(os.listdir(pages)):
        if not f.endswith('.html') or f == 'index.html':
            continue
        if f == '404.html':   # GitHub Pages отдаёт её на любом неизвестном адресе — поэтому пути от корня сайта
            src = open(os.path.join(pages, f), encoding='utf-8').read()
            out = page('404', src).replace('<head>', f'<head>\n<base href="{SITE_BASE}">', 1)
            out = out.replace('href="../', 'href="').replace('src="../', 'src="').replace('url(../', 'url(')
            open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(out.replace('href="404/"', 'href="./"'))
            done.append(os.path.join(OUT, '404.html'))
            continue
        slug = f[:-5].replace('--', '/')   # uslugi--sait-kompanii.html → /uslugi/sait-kompanii/
        if slug.startswith('uslugi/') and os.path.isfile(os.path.join(SRC, 'data', 'uslugi', slug.split('/', 1)[1] + '.json')):
            continue   # у услуги есть данные в src/data/uslugi — страницу собирает gen_service, ручная не нужна
        src = open(os.path.join(pages, f), encoding='utf-8').read()
        p = os.path.join(OUT, slug, 'index.html')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(page(slug, src))
        done.append(p)
    return done

if __name__ == '__main__':
    for p in build_all():
        print('ok', p)
