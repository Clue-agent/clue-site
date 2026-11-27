# Сборка всего сайта clue: src/ → docs/ (папка, которую публикует GitHub Pages).
# Запуск из папки проекта:  python tools/build.py
#
#   src/pages/index.html        главная (пишется вручную)
#   src/pages/<slug>.html       обычные страницы → docs/<slug>/
#   src/data/uslugi/*.json      услуги           → docs/uslugi/<slug>/
#   src/data/proekty/*.json     кейсы            → docs/proekty/<slug>/
#   src/assets/                 стили, скрипты, шрифты, картинки → docs/assets/
#   tools/seo.py                домен, sitemap.xml, robots.txt, CNAME, разметка для поисковиков
import os, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_service, gen_case, gen_page, seo
from gen_service import SRC, OUT

# услуги без своей страницы: название и формат для заявки
SERVICES = {
    'sait-vizitka': ('Сайт-визитка', 'Сайт компании'), 'redizain': ('Редизайн', 'Редизайн'),
    'dizain-saita': ('Дизайн сайта', 'Дизайн'), 'logotip': ('Логотип', 'Дизайн'),
    'firmennyi-stil': ('Фирменный стиль', 'Дизайн'), 'socseti': ('Оформление соцсетей', 'Дизайн'),
    'promo-roliki': ('Промо-ролики', 'Дизайн'), 'seo-optimizaciya': ('SEO-оптимизация', 'Пока не знаю'),
    'seo-prodvizhenie': ('SEO-продвижение', 'Пока не знаю'), 'kopirait': ('Копирайт', 'Пока не знаю'),
    'audit': ('Аудит сайта', 'Пока не знаю'), 'testirovanie': ('Тестирование', 'Пока не знаю'),
    'podderzhka': ('Доработка и поддержка', 'Пока не знаю'),
}

ALIAS = {'sait-vizitka': 'sait-kompanii/#vizitka'}   # визитка — вариант на странице «Сайт компании»

def fix_service_links():
    """Пока у услуги нет своей страницы, ссылка на неё ведёт к её строке на /uslugi/ (там же цена и кнопка заявки)."""
    import re
    for d, _, fs in os.walk(OUT):
        for f in fs:
            if not f.endswith('.html'):
                continue
            p = os.path.join(d, f); s = open(p, encoding='utf-8').read()
            def fix(m):
                href = m.group(1)
                tgt = os.path.normpath(os.path.join(d, href))
                rel = os.path.relpath(tgt, OUT).replace(os.sep, '/')
                mm = re.fullmatch(r'uslugi/([a-z0-9-]+)', rel)
                if not mm or os.path.isfile(os.path.join(tgt, 'index.html')):
                    return m.group(0)
                up = os.path.relpath(os.path.join(OUT, 'uslugi'), d).replace(os.sep, '/')
                al = ALIAS.get(mm.group(1))
                if al and os.path.isfile(os.path.join(OUT, 'uslugi', al.split('/')[0], 'index.html')):
                    return f'href="{up}/{al}"'
                if up == '.':   # уже на странице «Услуги»: клик открывает заявку с этой услугой
                    name, fmt = SERVICES.get(mm.group(1), (mm.group(1), 'Пока не знаю'))
                    return f'href="#zayavka" data-modal data-format="{fmt}" data-msg="Интересует: {name}"'
                return f'href="{up}/#{mm.group(1)}"'
            s2 = re.sub(r'href="([^"#:]+/)"', fix, s)
            if s2 != s:
                open(p, 'w', encoding='utf-8').write(s2)

def unlink_missing_cases():
    """Карточка проекта без своей страницы — показываем без ссылки, а не ведём в никуда."""
    import re
    for d, _, fs in os.walk(OUT):
        for f in fs:
            if not f.endswith('.html'):
                continue
            p = os.path.join(d, f); s = open(p, encoding='utf-8').read()
            def fix(m):
                tgt = os.path.normpath(os.path.join(d, m.group(2)))
                if os.path.isfile(os.path.join(tgt, 'index.html')):
                    return m.group(0)
                inner = re.sub(r'<span class="wk__cur"[^>]*>.*?</span>', '', m.group(4), flags=re.S)
                return f'<div {m.group(1)}{m.group(3)}>{inner}</div>'
            s2 = re.sub(r'<a (class="wk__i[^"]*") href="([^"#:]+)"([^>]*)>(.*?)</a>', fix, s, flags=re.S)
            if s2 != s:
                open(p, 'w', encoding='utf-8').write(s2)

def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(SRC, 'assets'), os.path.join(OUT, 'assets'))
    shutil.copy(os.path.join(SRC, 'pages', 'index.html'), os.path.join(OUT, 'index.html'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()   # GitHub Pages: отдавать файлы как есть
    n = 1
    for kind, gen in (('uslugi', gen_service), ('proekty', gen_case)):
        folder = os.path.join(SRC, 'data', kind)
        for f in sorted(os.listdir(folder)):
            if not f.endswith('.json'):
                continue
            for d in json.load(open(os.path.join(folder, f), encoding='utf-8')):
                p = os.path.join(OUT, kind, d['slug'], 'index.html')
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, 'w', encoding='utf-8').write(gen.page(d))
                n += 1
    n += len(gen_page.build_all())
    fix_service_links()
    unlink_missing_cases()
    # в подборе на «Услугах»: у услуг без своей страницы кнопка «подробнее» не нужна — рядом уже есть «обсудить»
    import re
    up = os.path.join(OUT, 'uslugi', 'index.html')
    if os.path.isfile(up):
        t = open(up, encoding='utf-8').read()
        t = re.sub(r'<a class="btn btn--grey btn--lg btn--white" href="#zayavka" data-modal[^>]*>подробнее <span class="btn__ar" aria-hidden="true">→</span></a>', '', t)
        open(up, 'w', encoding='utf-8').write(t)
    pages = seo.process(OUT)   # canonical, превью, разметка, sitemap.xml, robots.txt, CNAME
    # src/root/ — файлы в корень сайта как есть (подтверждение Яндекс.Вебмастера и т. п.), после seo, чтобы их не трогали
    root = os.path.join(SRC, 'root')
    if os.path.isdir(root):
        for f in os.listdir(root):
            shutil.copy(os.path.join(root, f), os.path.join(OUT, f))
    print(f'готово: {n} страниц в {OUT}, в sitemap: {len(pages)}')

if __name__ == '__main__':
    main()
