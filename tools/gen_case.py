# Генератор страниц кейсов clue: шапка, меню, футер и окно заявки берутся с главной,
# блоки кейса собираются из данных. Пишет proekty/<slug>/index.html
import os, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_service import HEADER, MNAV, FOOTER, MODAL, CTA, rebase, esc, OUT

U = '<svg class="mark__u" viewBox="0 0 300 24" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M4 15C80 7 190 5 296 10"/><path pathLength="1" d="M40 21c80-5 160-6 240-3"/></svg>'

from devices import phone, tablet, laptop, browser

def stages(items, start):
    return ''.join(f'<li data-rv><div class="cs-st__h"><h3>{esc(t)}</h3><span>( {start+i:02d} )</span></div><p>{esc(p)}</p></li>' for i,(t,p) in enumerate(items))

OTHERS = [
    ('avtodiler', '#DCE6F7', 'Автодилер', 'Премиальный сайт официального дилера: каталог с ценами, подбор по кузову и калькулятор кредита.', 'сайт компании'),
    ('plyn', '#E3E7D6', 'Плынь', 'Сайт студии йоги в Минске: название и логотип, абонементы, аренда залов и сертификаты.', 'сайт компании'),
    ('stroy', '#E6EAF1', 'Строй', 'Редизайн сайта девелопера: новый логотип, поиск на первом экране и каталог проектов с фильтрами.', 'концепт · редизайн'),
]

def industry(d):
    """Ссылка с кейса на отраслевую страницу (поле "industry" в json: адрес, заголовок, текст, кнопка)."""
    if not d.get('industry'):
        return ''
    href, t, p, btn = d['industry']
    return f'''
<!-- 11 ОТРАСЛЕВАЯ СТРАНИЦА -->
<section class="card go" aria-labelledby="ind-t">
  <div class="cs-blue__bg" aria-hidden="true" style="background-image:url(assets/img/deco/waves-white.svg)"></div>
  <div class="go__tx">
    <p class="aside aside--on-b">( для вашего бизнеса )</p>
    <h2 class="go__t" id="ind-t" data-rv>{esc(t)}</h2>
    <p class="go__p">{esc(p)}</p>
  </div>
  <div class="go__act">
    <a class="btn btn--light btn--lg" href="{href}">{esc(btn)} <span class="btn__ar" aria-hidden="true">→</span></a>
  </div>
</section>
'''

def more_projects(cur):
    cards = ''
    for n, (slug, bg, name, text, tag) in enumerate([o for o in OTHERS if o[0] != cur][:3]):
        cards += (f'<a class="wk__i" href="proekty/{slug}/" data-rv><div class="wk__im" style="background:{bg}">'
                  f'<div class="laptop laptop--sm" data-par="-0.05"><div class="laptop__scr"><img src="assets/img/concepts/{slug}.webp" alt="{name} — первый экран" width="1200" height="760" loading="lazy"></div><div class="laptop__base"></div></div>'
                  f'<span class="wk__cur" aria-hidden="true">смотреть<br>кейс</span></div>'
                  f'<div class="wk__tx"><span class="wk__n">( {n+1:02d} )</span><h3>{name}</h3><span class="wk__tg">{tag}</span><p>{esc(text)}</p></div></a>')
    return f'''
<!-- 12 ЕЩЁ ПРОЕКТЫ -->
<section aria-labelledby="more-t">
  <div class="sec"><p class="aside">( ещё проекты )</p><h2 class="sec__t" id="more-t" data-rv>Другие <span class="mark c-b">проекты{U}</span></h2></div>
  <div class="cs-more">{cards}</div>
</section>
'''

def page(d):
    I = f"assets/img/cases/{d['slug']}/"
    cur = HEADER  # «проекты» в меню
    cur = cur.replace('<a class="pill" href="proekty/">проекты</a>', '<a class="pill" href="proekty/" aria-current="page">проекты</a>')
    fonts = ''.join(f'<div class="sg-type__row"><span class="sg-type__k">{k}</span><span class="sg-type__s" style="font-size:min({fs}px,64px,12vw);font-weight:{fw}">{esc(t)}</span><span class="sg-type__m">{m}</span></div>' for k,fs,fw,t,m in d['type'])
    colors = ''.join(f'<div class="sg-col"><span style="background:{c}"></span><b>{n}</b><small>{c}</small></div>' for n,c in d['colors'])
    stack = ''.join(f'<li>{esc(s)}</li>' for s in d['stack'])
    A = lambda k, v: esc(d.get('alts', {}).get(k, v))   # подписи картинок можно переопределить в данных кейса
    b1, b2, b3 = d.get('buttons', ['Записаться →', 'Узнать о модели', 'Выходные'])
    grid = ''.join(f'<div><b>{w}</b><span style="--n:{n}"></span></div>' for w, n in d.get('grid', [[1440, 12], [768, 8], [390, 4]]))
    body = f'''<!-- 01 ПЕРВЫЙ ЭКРАН КЕЙСА -->
<section class="card cs-hero" aria-labelledby="cs-t">
  <div class="cs-hero__bg" aria-hidden="true" style="background-image:url({I}waves-blue.svg)"></div>
  <nav class="crumbs cs-hero__crumbs" aria-label="Хлебные крошки"><a href="./">главная</a><span aria-hidden="true">/</span><a href="proekty/">проекты</a><span aria-hidden="true">/</span><span aria-current="page">{esc(d['name'])}</span></nav>
  <p class="cs-hero__cap">{esc(d['caption'])}</p>
  <h1 class="cs-hero__t" id="cs-t" style="--k:{min(1, 6.2/len(d['title'])):.3f}"><span>{esc(d['title'])}</span></h1>
  <div class="cs-hero__ph" data-par="-0.12">{phone(I+'m-hero.webp', d['name']+' — мобильная версия, первый экран')}</div>
  {'<span class="cs-badge">концепт студии</span>' if d.get('concept', True) else ''}
</section>

<!-- 02 О ПРОЕКТЕ -->
<section class="card cs-about" aria-label="О проекте">
  <div class="cs-about__l">
    <p class="aside">( о проекте )</p>
    <h2 class="cs-about__t" data-rv>{esc(d['about_title'])}</h2>
    <p class="cs-about__p">{esc(d['about_text'])}</p>
  </div>
  <div class="cs-about__r">
    <p class="aside">( задача )</p>
    <p class="cs-about__task">{esc(d['task'])}</p>
    <p class="aside cs-about__lb2">( стек работ )</p>
    <ul class="cs-about__stack">{stack}</ul>
  </div>
</section>

<!-- 03 БОЛЬШАЯ КАРТОЧКА С НАЗВАНИЕМ -->
<section class="card cs-name" aria-hidden="true">
  <div class="cs-name__ph" data-par="0.08" style="background-image:url({I}photo.webp)"></div>
  <p class="cs-name__t" style="--k:{min(1, 6.2/len(d['name'])):.3f}">{esc(d['name'])}</p>
</section>

<!-- 04 ЭКРАНЫ: КОМПЬЮТЕР И ТЕЛЕФОН -->
<div class="cs-two">
  <div class="card cs-two__i cs-two__i--blue" data-rv><div class="cs-two__lap" data-par="-0.05">{laptop(I+'d-hero.webp', 'Первый экран на компьютере')}</div></div>
  <div class="card cs-two__i cs-two__i--warm" data-rv><div class="cs-two__ph" data-par="-0.1">{phone(I+'m-color.webp', A('m-color','Выбор цвета на телефоне'), 'dv-ph--tilt')}</div></div>
</div>

<!-- 05 ЭТАПЫ 01–03 -->
<section class="card cs-st" aria-label="Этапы работы">
  <div class="cs-st__tx"><p class="aside">( этапы работы )</p><ol class="cs-st__list">{stages(d['stages1'],1)}</ol></div>
  <div class="cs-st__im"><div class="cs-st__tb" data-par="-0.05">{tablet(I+'t-hero.webp',d.get('alt_tablet','Версия для планшета'))}</div><div class="cs-st__ph" data-par="-0.14">{phone(I+'m-hero.webp','Версия для телефона')}</div></div>
</section>

<!-- 06 СТИЛЬ: ШРИФТЫ, ЦВЕТА, КНОПКИ -->
<div class="cs-two">
  <div class="card cs-two__i cs-two__i--warm cs-two__i--sg" data-rv>
    <div class="sg">
      <p class="sg__h">Шрифт</p>
      <p class="sg__font">{esc(d['font'])}</p>
      <div class="sg-type">{fonts}</div>
    </div>
  </div>
  <div class="card cs-two__i cs-two__i--cool cs-two__i--sg" data-rv>
    <div class="sg">
      <p class="sg__h">Цвета</p>
      <div class="sg-cols">{colors}</div>
      <p class="sg__h sg__h--2">Кнопки</p>
      <div class="sg-btns"><span class="sg-b sg-b--w">{esc(b1)}</span><span class="sg-b sg-b--o">{esc(b2)}</span><span class="sg-b sg-b--chip">{esc(b3)}</span></div>
      <p class="sg__h sg__h--2">Сетка</p>
      <div class="sg-grid">{grid}</div>
    </div>
  </div>
</div>

<!-- 07 ЭТАПЫ 04–06 -->
<section class="card cs-st cs-st--rev" aria-label="Этапы работы, продолжение">
  <div class="cs-st__im cs-st__im--phones"><div class="cs-st__bg" aria-hidden="true" style="background-image:url({I}waves-blue.svg)"></div><div data-par="-0.06">{phone(I+'m-form.webp',A('m-form','Форма записи на тест-драйв'))}</div><div data-par="-0.16">{phone(I+'m-done.webp',A('m-done','Экран после записи'))}</div></div>
  <div class="cs-st__tx"><p class="aside">( этапы работы )</p><ol class="cs-st__list">{stages(d['stages2'],4)}</ol></div>
</section>

<!-- 08 СИНЯЯ КАРТОЧКА С ФОРМОЙ -->
<section class="card cs-blue" aria-label="{A('blue','Форма записи')}">
  <div class="cs-blue__bg" aria-hidden="true" style="background-image:url({I}waves-white.svg)"></div>
  <div class="cs-blue__ph" data-par="-0.1">{phone(I+'m-form.webp',A('m-form2','Форма записи на тест-драйв на телефоне'))}</div>
</section>

<!-- 09 ОСНОВНЫЕ СТРАНИЦЫ -->
<section class="card cs-pages" aria-labelledby="pg-t">
  <div class="cs-pages__tx">
    <p class="aside">( о сайте )</p>
    <h2 class="cs-pages__t" id="pg-t" data-rv>Основные страницы</h2>
    {''.join(f'<p class="cs-pages__p">{esc(p)}</p>' for p in d['pages_text'])}
  </div>
  <div class="cs-pages__im" aria-hidden="true">
    <img src="{I}p-home.webp" alt="" loading="lazy" data-par="-0.05"><img src="{I}p-model.webp" alt="" loading="lazy" data-par="0.04"><img src="{I}p-drive.webp" alt="" loading="lazy" data-par="-0.09">
  </div>
</section>

<!-- 10 БРАУЗЕР -->
<section class="card cs-br" aria-label="{A('br','Раздел технологий в браузере')}">
  <div class="cs-br__bg" aria-hidden="true" style="background-image:url({I}waves-blue.svg)"></div>
  <div class="cs-br__w" data-par="-0.06">{browser(I+'d-specs.webp',A('d-specs','Раздел «Технологии» на компьютере'))}</div>
</section>

<!-- 11 ВСЕ ЭКРАНЫ НА ТЕЛЕФОНЕ -->
<section class="card cs-row" aria-labelledby="row-t">
  <div class="cs-row__tx"><p class="aside">( мобильная версия )</p><h2 class="cs-row__t" id="row-t" data-rv>{esc(d['mobile_title'])}</h2><p class="cs-row__p">{esc(d['mobile_text'])}</p></div>
  <div class="cs-row__phs">{''.join(f'<div data-par="{p}">{phone(I+n+".webp","")}</div>' for n,p in [('m-hero','-0.04'),('m-color','-0.1'),('m-form','-0.04'),('m-done','-0.1')])}</div>
</section>

'''
    head = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(d.get('seo_title') or d['name'] + ' — кейс clue')}</title>
<meta name="description" content="{esc(d['meta'])}">
<meta property="og:title" content="{esc(d.get('seo_title') or d['name'] + ' — кейс clue')}">
<meta property="og:description" content="{esc(d['meta'])}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#F2F2F2">
<link rel="icon" type="image/svg+xml" href="assets/img/logo/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/logo/favicon-32.png">
<link rel="apple-touch-icon" href="assets/img/logo/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/InterDisplay-Regular.woff" as="font" type="font/woff" crossorigin>
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.classList.add('js');setTimeout(function(){{document.documentElement.classList.add('ft-done')}},2500)</script>
</head>
<body class="page-case">
<a class="skip" href="#main">Перейти к содержанию</a>

'''
    out = head + cur + MNAV + '<main id="main">\n\n' + body + industry(d) + more_projects(d['slug']) + CTA + '</main>\n\n' + FOOTER + MODAL + '<script src="assets/js/main.js" defer></script>\n</body>\n</html>\n'
    return rebase(out, 2, 'proekty')

if __name__ == '__main__':
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    for d in data:
        p = os.path.join(OUT, 'proekty', d['slug'], 'index.html')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(page(d))
        print('ok', p)
