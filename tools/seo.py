# SEO-обработка собранного сайта (вызывается из build.py после сборки страниц).
#
# Для каждой страницы в docs/ добавляет:
#   canonical, og:url, og:image, og:site_name, og:locale, twitter:card,
#   разметку Schema.org (JSON-LD): организация на главной, услуга на страницах услуг,
#   «хлебные крошки» на внутренних страницах.
# Создаёт: docs/sitemap.xml, docs/robots.txt, docs/CNAME.
#
# Домен меняется в одном месте — SITE.
import os, re, json, html, datetime

SITE = 'https://clue.by'
DOMAIN = 'clue.by'
OG_IMAGE = '/assets/img/og/clue-og.jpg'
TELEGRAM = 'https://t.me/ClueDesign'

ORG = {
    '@type': 'ProfessionalService',
    '@id': SITE + '/#studio',
    'name': 'Веб-студия clue',
    'alternateName': 'clue',
    'url': SITE + '/',
    'logo': SITE + '/assets/img/logo/apple-touch-icon.png',
    'image': SITE + OG_IMAGE,
    'description': 'Проектируем, разрабатываем и тестируем сайты для бизнеса: лендинги, сайты компаний, редизайн, дизайн и SEO.',
    'address': {'@type': 'PostalAddress', 'addressLocality': 'Могилёв', 'addressRegion': 'Могилёвская область', 'addressCountry': 'BY'},
    'areaServed': [{'@type': 'City', 'name': 'Могилёв'}, {'@type': 'Country', 'name': 'Беларусь'}, {'@type': 'Country', 'name': 'Россия'}],
    'knowsLanguage': 'ru',
    'currenciesAccepted': 'BYN',
    'sameAs': [TELEGRAM],
}

# страницы услуг: минимальная цена в BYN (как на сайте)
SERVICE_PRICE = {
    '/uslugi/lending/': 1200,
    '/uslugi/sait-kompanii/': 2500,
    '/uslugi/redizain/': 1500,
    '/uslugi/dizain-saita/': 900,
    '/otrasli/avtosalony/': 2500,
    '/otrasli/studii/': 2500,
}

# приоритеты для sitemap
PRIORITY = {'/': '1.0', '/uslugi/': '0.9', '/proekty/': '0.8', '/kontakty/': '0.7', '/o-studii/': '0.6', '/politika/': '0.2', '/otrasli/avtosalony/': '0.8', '/otrasli/studii/': '0.8'}


def _url_path(rel):
    rel = rel.replace(os.sep, '/')
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel


def _meta(s, name, attr='name'):
    m = re.search(r'<meta %s="%s" content="([^"]*)"' % (attr, re.escape(name)), s)
    return html.unescape(m.group(1)) if m else ''


def _crumbs(s, path):
    """Хлебные крошки из навигации страницы: <nav class="crumbs"> … </nav>."""
    m = re.search(r'<nav class="crumbs[^"]*"[^>]*>(.*?)</nav>', s, re.S)
    if not m:
        return None
    items, pos = [], 1
    for href, text in re.findall(r'<a href="([^"]*)"[^>]*>(.*?)</a>', m.group(1)):
        # относительную ссылку переводим в абсолютную от текущей страницы
        base = path if path.endswith('/') else path.rsplit('/', 1)[0] + '/'
        parts = [p for p in base.strip('/').split('/') if p]
        for seg in href.split('/'):
            if seg == '..':
                parts = parts[:-1]
            elif seg not in ('', '.'):
                parts.append(seg)
        url = SITE + '/' + '/'.join(parts) + ('/' if parts else '')
        items.append({'@type': 'ListItem', 'position': pos, 'name': (lambda x: x[:1].upper() + x[1:])(re.sub('<[^>]+>', '', text).strip()), 'item': url})
        pos += 1
    cur = re.search(r'<span aria-current="page">(.*?)</span>', m.group(1))
    if cur:
        items.append({'@type': 'ListItem', 'position': pos, 'name': (lambda x: x[:1].upper() + x[1:])(re.sub('<[^>]+>', '', cur.group(1)).strip()), 'item': SITE + path})
    return {'@type': 'BreadcrumbList', 'itemListElement': items} if len(items) > 1 else None


def _ld(obj):
    data = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return f'<script type="application/ld+json">{data}</script>'


def process(out):
    pages = []
    for d, dirs, fs in os.walk(out):
        if os.path.relpath(d, out).split(os.sep)[0] == 'assets':
            continue
        for f in fs:
            if not f.endswith('.html'):
                continue
            p = os.path.join(d, f)
            rel = os.path.relpath(p, out)
            path = _url_path(rel)
            s = open(p, encoding='utf-8').read()
            is404 = rel == '404.html'
            title = re.search(r'<title>(.*?)</title>', s, re.S)
            title = html.unescape(title.group(1).strip()) if title else 'clue'
            desc = _meta(s, 'description')

            head = []
            if is404:
                head.append('<meta name="robots" content="noindex">')
            else:
                head.append(f'<link rel="canonical" href="{SITE}{path}">')
                head.append(f'<meta property="og:url" content="{SITE}{path}">')
            head += [
                '<meta property="og:site_name" content="clue">',
                '<meta property="og:locale" content="ru_RU">',
                f'<meta property="og:image" content="{SITE}{OG_IMAGE}">',
                '<meta property="og:image:width" content="1200">',
                '<meta property="og:image:height" content="630">',
                '<meta property="og:image:alt" content="Студия clue — делаем сайты, которые приводят клиентов">',
                '<meta name="twitter:card" content="summary_large_image">',
            ]
            if not is404:
                graph = []
                if path == '/':
                    graph += [ORG, {'@type': 'WebSite', '@id': SITE + '/#site', 'url': SITE + '/', 'name': 'clue',
                                    'inLanguage': 'ru', 'publisher': {'@id': ORG['@id']}}]
                if path in SERVICE_PRICE:
                    name = re.split(r'\s+[—|]\s+', title)[0].strip()
                    graph.append({
                        '@type': 'Service', 'name': name, 'description': desc, 'url': SITE + path,
                        'provider': {'@id': ORG['@id'], '@type': 'ProfessionalService', 'name': ORG['name'], 'url': ORG['url']},
                        'areaServed': ORG['areaServed'],
                        'offers': {'@type': 'Offer', 'priceCurrency': 'BYN', 'price': SERVICE_PRICE[path],
                                   'priceSpecification': {'@type': 'PriceSpecification', 'minPrice': SERVICE_PRICE[path], 'priceCurrency': 'BYN'}},
                    })
                bc = _crumbs(s, path)
                if bc:
                    graph.append(bc)
                if graph:
                    head.append(_ld({'@context': 'https://schema.org', '@graph': graph}))

            block = '\n'.join(head)
            anchor = re.search(r'<meta property="og:type"[^>]*>', s) or re.search(r'<meta name="description"[^>]*>', s)
            s = s[:anchor.end()] + '\n' + block + s[anchor.end():] if anchor else s.replace('</head>', block + '\n</head>', 1)
            open(p, 'w', encoding='utf-8').write(s)
            if not is404:
                pages.append(path)

    today = datetime.date.today().isoformat()
    pages.sort(key=lambda u: (u != '/', u.count('/'), u))
    urls = '\n'.join(
        f'  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod><priority>{PRIORITY.get(u, "0.8" if u.startswith("/uslugi/") else "0.6")}</priority></url>'
        for u in pages)
    open(os.path.join(out, 'sitemap.xml'), 'w', encoding='utf-8').write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')
    open(os.path.join(out, 'robots.txt'), 'w', encoding='utf-8').write(
        f'User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE}/sitemap.xml\n')
    open(os.path.join(out, 'CNAME'), 'w', encoding='utf-8').write(DOMAIN + '\n')
    return pages
