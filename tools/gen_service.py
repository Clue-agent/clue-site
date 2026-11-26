# Генератор страниц услуг clue: берёт шапку, меню, футер и окно заявки с главной (src/pages/index.html),
# подставляет данные услуги и пишет uslugi/<slug>/index.html
import re, os, sys, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
OUT = os.path.join(ROOT, 'docs')
home = open(os.path.join(SRC, 'pages', 'index.html'), encoding='utf-8').read()

def cut(a, b):
    i = home.index(a); j = home.index(b, i)
    return home[i:j]

HEADER = cut('<!-- ШАПКА -->', '<!-- МОБИЛЬНОЕ МЕНЮ -->')
MNAV   = cut('<!-- МОБИЛЬНОЕ МЕНЮ -->', '<main id="main">')
FOOTER = cut('<footer class="card ft">', '<!-- МОДАЛЬНОЕ ОКНО')
MODAL  = cut('<!-- МОДАЛЬНОЕ ОКНО', '<script src="assets/js/main.js"')
CTA    = cut('<!-- БОЛЬШОЙ ПРИЗЫВ', '</main>')
U = '<svg class="mark__u" viewBox="0 0 300 24" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M4 15C80 7 190 5 296 10"/><path pathLength="1" d="M40 21c80-5 160-6 240-3"/></svg>'

def rebase(s, depth=2, section='uslugi'):
    """пути с главной -> пути со страницы <section>/<slug>/"""
    up = '../' * depth
    def fix(m):
        attr, q, v = m.group(1), m.group(2), m.group(3)
        if v.startswith(('#', 'http', 'tel:', 'mailto:', 'data:', '/')):
            return m.group(0)
        if v == './':
            v = up
        elif v.startswith(section + '/'):
            v = '../' * (depth - 1) + v[len(section) + 1:]
            if v == '': v = './'
        else:
            v = up + v
        return f'{attr}={q}{v}{q}'
    s = re.sub(r'url\((assets/[^)]*)\)', lambda m: 'url(' + up + m.group(1) + ')', s)
    return re.sub(r'(href|src)=(["\'])([^"\']*)\2', fix, s)

def esc(t): return html.escape(t, quote=False)

from devices import phone, phone3d, tablet, laptop, browser, podium

def stg(items, start):
    return ''.join(f'<li data-rv><div class="cs-st__h"><h3>{esc(t)}</h3><span>( {start+i:02d} )</span></div><p>{esc(p)}</p><p class="sv-st__r"><span>вы получаете</span>{esc(r)}</p></li>' for i,(t,p,r) in enumerate(items))

def card(c):
    """Одна карточка правой панели. kind: rows (по умолчанию), chat, estimate, tasks, serp, bars, plan, chart."""
    k = c.get('kind', 'rows'); e = esc
    if k == 'rows':
        inner = ''.join(f'<div class="pr-brief__r"><span>{e(a)}</span><b>{e(b)}</b></div>' for a, b in c['rows'])
    elif k == 'chat':
        inner = '<div class="pk-chat">' + ''.join(
            f'<div class="pk-msg pk-msg--{sd}"><small>{e(who)}</small><p>{e(tx)}</p></div>' for sd, who, tx in c['msgs']) + '</div>'
    elif k == 'estimate':
        t = c.get('total')
        inner = '<div class="pk-list">' + ''.join(f'<div class="pk-r"><span>{e(a)}</span><b>{e(b)}</b></div>' for a, b in c['items']) \
            + (f'<div class="pk-r pk-r--t"><span>{e(t[0])}</span><b>{e(t[1])}</b></div>' if t else '') + '</div>'
    elif k == 'tasks':
        inner = '<div class="pk-list">' + ''.join(
            f'<div class="pk-t pk-t--{st}"><i></i><span>{e(tx)}</span><em>{e(bd)}</em></div>' for st, tx, bd in c['items']) + '</div>'
    elif k == 'serp':
        g = c['serp']
        inner = (f'<div class="pk-q"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="9" cy="9" r="6"/><path d="M14 14l4 4"/></svg><span>{e(g["q"])}</span></div>'
                 '<div class="pk-s pk-s--ghost"><i></i><i></i></div>'
                 f'<div class="pk-s pk-s--you"><small>{e(g["url"])}</small><b>{e(g["title"])}</b><p>{e(g["desc"])}</p></div>'
                 '<div class="pk-s pk-s--ghost"><i></i><i></i></div>')
    elif k == 'bars':
        inner = '<div class="pk-list">' + ''.join(
            f'<div class="pk-b"><span>{e(w)}</span><u><s style="width:{int(n)}%"></s></u><em>{e(lb)}</em></div>' for w, n, lb in c['items']) + '</div>'
    elif k == 'plan':
        inner = '<div class="pk-list">' + ''.join(
            f'<div class="pk-p"><i>{n}</i><div><b>{e(a)}</b><span>{e(b)}</span></div></div>' for n, (a, b) in enumerate(c['items'], 1)) + '</div>'
    elif k == 'chart':
        arrow = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 9.5l7-7M4 2.5h5.5V8"/></svg>'
        inner = ('<div class="pk-c"><svg viewBox="0 0 300 112" aria-hidden="true"><path class="g" d="M0 30H300M0 62H300M0 94H300"/>'
                 '<path class="a" d="M8 94C40 90 62 84 90 72S140 64 168 50S232 32 292 16V106H8Z"/>'
                 '<path class="l" d="M8 94C40 90 62 84 90 72S140 64 168 50S232 32 292 16"/><circle cx="292" cy="16" r="5"/></svg></div>'
                 '<div class="pk-k">' + ''.join(f'<div><span>{e(a)}</span><b>{arrow}{e(b)}</b></div>' for a, b in c['kpis']) + '</div>')
    else:
        raise ValueError('неизвестный вид карточки: ' + k)
    return f'<div class="pr-brief{"" if k == "rows" else " pk"}"><p class="pr-brief__h">{e(c["title"])} <span>{e(c["tag"])}</span></p>{inner}</div>'


def page(d):
    has_ex = bool(d.get('example')); cards = d.get('cards')
    if cards or not has_ex:   # услуга без кейса: поля, нужные только для кадров с макетами, не требуются
        d = {'brief': [], 'checks': [], 'lead_demo': '', 'example_name': '', 'example': 'vector', **d}
    slug = d['slug']; fmt = d['format']
    title = d.get('seo_title') or f"{d['name']} — clue"
    E = f"assets/img/cases/{d['example']}/"; W = 'assets/img/deco/'
    cur = HEADER.replace('class="pill dd__btn"', 'class="pill dd__btn" aria-current="page"')
    msg = f' data-msg="Интересует: {esc(d["msg"])}"' if d.get('msg') else ''
    btn = lambda txt, cls='btn--blue': f'<a class="btn {cls} btn--lg" href="#zayavka" data-modal data-format="{fmt}"{msg}>{esc(txt)} <span class="btn__ar" aria-hidden="true">→</span></a>'
    n = len(d['steps']); half = (n + 1) // 2
    fit = ''.join(f'<li>{esc(t)}</li>' for t,_ in d['fit'])
    res = ''.join(f'<li>{esc(t)}</li>' for t in d['result'])
    inc = ''.join(f'<li data-rv><span class="sv-inc__n">{i+1:02d}</span><div><b>{esc(t)}</b><p>{esc(p)}</p></div></li>' for i,(t,p) in enumerate(d['incl']))
    dep = ''.join(f'<div class="sv-row"><span class="sv-row__k">{i+1:02d}</span><div><b>{esc(t)}</b><p>{esc(p)}</p></div></div>' for i,(t,p) in enumerate(d['depends']))
    add = ''.join(f'<a class="sv-row sv-row--a" href="{h}"><b>{esc(nm)}</b><span>{esc(pr)}</span><i aria-hidden="true">→</i></a>' for nm,h,pr in d['addons'])
    # --- экраны для блока «как проходит»: меняются по мере прокрутки этапов ---
    bf = ''.join(f'<div class="pr-brief__r"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k,v in d['brief'])
    # кадр «Прототип»: по умолчанию — VECTOR; другая услуга может задать свои тексты в JSON, ключ "wire"
    _w = dict(name='Прототип · Desktop', brand='VECTOR', nav=['Модель', 'Технологии', 'Зарядка'], cta='Тест-драйв',
              eyebrow='НОВАЯ МОДЕЛЬ', h1='Электромобиль нового поколения',
              text='Запишитесь на тест-драйв в удобном салоне — перезвоним и подтвердим время.',
              btn='Записаться на тест-драйв →', img='фото модели',
              stats=[['600 км', 'запас хода'], ['3,9 с', 'до 100 км/ч'], ['20 мин', 'зарядка до 80%']],
              note1='Кнопка видна без прокрутки', note2='Цифры вместо длинного текста')
    _w.update(d.get('wire', {}))
    _nav = ''.join(f'<span>{esc(x)}</span>' for x in _w['nav'])
    _st = ''.join(f'<div><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in _w['stats'])
    wire = (f'<div class="pw"><p class="pw__name">{esc(_w["name"])}</p><div class="pw__fr">\n'
      f'      <div class="pw__nav"><b>{esc(_w["brand"])}</b>{_nav}<em>{esc(_w["cta"])}</em></div>\n'
      f'      <div class="pw__hero"><div class="pw__l"><small>{esc(_w["eyebrow"])}</small><p class="pw__h"><span class="pw__sel">{esc(_w["h1"])}<i></i><i></i><i></i><i></i><u>H1 · оффер</u></span></p><p class="pw__p">{esc(_w["text"])}</p><span class="pw__btn">{esc(_w["btn"])}<b class="pw__pin">1</b></span></div>\n'
      f'        <div class="pw__img"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path d="M0 0L100 100M100 0L0 100"/></svg><span>{esc(_w["img"])}</span></div></div>\n'
      f'      <div class="pw__st">{_st}<b class="pw__pin">2</b></div>\n'
      '    </div>\n'
      f'    <div class="pw__note pw__note--1"><b>1</b>{esc(_w["note1"])}</div>\n'
      f'    <div class="pw__note pw__note--2"><b>2</b>{esc(_w["note2"])}</div>\n'
      '    <div class="pw__cur"><svg viewBox="0 0 16 18" aria-hidden="true"><path d="M1 1l13 6.2-5.8 1.6L5.6 15z"/></svg><span>clue</span></div></div>')
    chk = ''.join(f'<li>{esc(c)}</li>' for c in d['checks'])
    frames = f'''
      <div class="pr__f pr__f--brief is-on" data-f="0"><div class="pr-brief"><p class="pr-brief__h">Задача <span>{d.get('brief_tag','концепт '+d['example_name'])}</span></p>{bf}</div></div>
      <div class="pr__f" data-f="1">{wire}</div>
      <div class="pr__f" data-f="2"><div class="pr-dz">{browser(E+'d-hero.webp','Дизайн первого экрана — концепт '+d['example_name'])}<div class="pr-dz__ph">{phone(E+'m-color.webp','')}</div></div></div>
      <div class="pr__f" data-f="3"><div class="pr-qa"><div class="pr-qa__tb">{tablet(E+'t-hero.webp','Проверка на планшете')}</div><div class="pr-qa__ph">{phone(E+d.get('qa_img','m-form.webp'),d.get('qa_alt','Проверка формы на телефоне'))}</div><ul class="pr-qa__l">{chk}</ul></div></div>
      <div class="pr__f" data-f="4"><div class="pr-go"><div class="pr-go__ph">{podium(phone(E+d.get('go_img','m-done.webp'),d.get('go_alt','Экран после заявки')))}</div><div class="pr-go__n"><p class="pr-go__t"><i></i>{esc(d.get('go_title','Новая заявка'))} <span>{esc(d.get('go_when','сейчас'))}</span></p><p>{esc(d['lead_demo'])}</p><small>{esc(d.get('go_note','пример уведомления'))}</small></div></div></div>'''
    if cards:   # вместо макетов — мини-интерфейсы: по одному на этап (вид задаёт ключ "kind")
        frames = '\n' + '\n'.join(
            f'      <div class="pr__f pr__f--brief{" is-on" if i == 0 else ""}" data-f="{i}">{card(c)}</div>'
            for i, c in enumerate(cards))
    import re as _re
    fl = _re.findall(r'<div class="pr__f[^"]*" data-f="\d">(.*?)</div>(?=\n      <div class="pr__f|$)', frames, _re.S)
    mv = lambda i: f'<div class="pr__mv pr__mv--{i}" aria-hidden="true">{fl[i]}</div>' if i < len(fl) else ''
    steps = ''.join(f'<li class="pr__s{" is-on" if i==0 else ""}" data-s="{i}">{mv(i)}<span class="pr__n">( {i+1:02d} )</span><h3>{esc(t)}</h3><p>{esc(p)}</p><p class="sv-st__r"><span>вы получаете</span>{esc(r)}</p></li>' for i,(t,p,r) in enumerate(d['steps']))
    dots = ''.join(f'<i{" class=\"is-on\"" if i==0 else ""}></i>' for i in range(n))
    dep = ''.join(f'<div class="pc__r"><b>{esc(t)}</b><p>{esc(p)}</p></div>' for t,p in d['depends'])
    add = ''.join(f'<a class="pc__a" href="{h}"><b>{esc(nm)}</b><span>{esc(pr)}</span><i aria-hidden="true">→</i></a>' for nm,h,pr in d['addons'])
    body = f'''<!-- 01 ПЕРВЫЙ ЭКРАН УСЛУГИ -->
<section class="card cs-hero sv-hero" aria-labelledby="s-t">
  <div class="cs-hero__bg" aria-hidden="true" style="background-image:url({W}waves-blue.svg)"></div>
  <nav class="crumbs cs-hero__crumbs" aria-label="Хлебные крошки"><a href="./">главная</a><span aria-hidden="true">/</span><a href="uslugi/">услуги</a><span aria-hidden="true">/</span><span aria-current="page">{esc(d['crumb'])}</span></nav>
  <p class="cs-hero__cap">{esc(d['hero_cap'])}</p>
  <h1 class="cs-hero__t sv-hero__t" id="s-t"><span>{esc(d['hero_word'])}</span> <span>{esc(d['h1_b'])}</span></h1>
  <div class="sv-hero__ft">{btn(d['cta'])}<span class="sv-hero__pr"><b>{esc(d['price'])}</b>{esc(d['price_note'])}</span></div>
</section>

<!-- 02 ОБ УСЛУГЕ -->
<section class="card cs-about" aria-labelledby="ab-t">
  <div class="cs-about__l">
    <p class="aside">( об услуге )</p>
    <h2 class="cs-about__t" id="ab-t" data-rv>{esc(d['about_title'])}</h2>
    <p class="cs-about__p">{esc(d['lead'])}</p>
  </div>
  <div class="cs-about__r">
    <p class="aside">( когда нужен )</p>
    <ul class="cs-about__stack">{fit}</ul>
    <p class="aside cs-about__lb2">( на выходе )</p>
    <ul class="cs-about__stack">{res}</ul>
  </div>
</section>

<!-- 03 ЧТО ВХОДИТ -->
<section class="card sv-inc" id="vhodit" aria-labelledby="inc-t">
  <div class="sv-inc__h">
    <h2 class="sv-inc__t" id="inc-t" data-rv>Что входит</h2>
    <p class="sv-inc__p">{esc(d['incl_note'])}</p>
  </div>
  <ul class="sv-inc__list">{inc}</ul>
</section>

<!-- 04 КАК ПРОХОДИТ: экран справа меняется вместе с этапом -->
<section class="card pr" aria-labelledby="pr-t" data-steps>
  <div class="pr__tx">
    <p class="aside">( как проходит )</p>
    <h2 class="sv-st__t" id="pr-t" data-rv>{d['steps_title_a']} {d['steps_title_b']}</h2>
    <p class="pr__lead">{esc(d['steps_lead'])}</p>
    <ol class="pr__list">{steps}</ol>
    <p class="sv-st__note">{esc(d['steps_note'])}</p>
  </div>
  <div class="pr__side"><div class="pr__stage" data-step="0" aria-hidden="true">{frames}
      <div class="pr__dots">{dots}</div>
  </div></div>
</section>

<!-- 05 СТОИМОСТЬ -->
<section class="card pc" id="cena" aria-labelledby="pc-t">
  <div class="pc__main">
    <p class="aside aside--dk">( стоимость )</p>
    <p class="pc__v" id="pc-t">{esc(d['price'])}</p>
    <p class="pc__p">{esc(d['price_text'])}</p>
    {btn('узнать точную цену','btn--light')}
  </div>
  <div class="pc__col"><p class="pc__h">От чего зависит сумма</p>{dep}</div>
  <div class="pc__col"><p class="pc__h">Можно добавить</p>{add}<p class="pc__fn">цены в BYN, точную сумму фиксируем в предложении до старта</p></div>
</section>

<!-- 06 ПРИМЕР -->
<a class="card ex" href="proekty/{d['example']}/" data-cur>
  <div class="ex__tx">
    <p class="aside aside--on-b">( пример — концепт студии )</p>
    <p class="ex__t">{esc(d['example_title'])}</p>
    <span class="ex__more">смотреть кейс {d['example_name']} <span aria-hidden="true">→</span></span>
  </div>
  <div class="ex__im" aria-hidden="true">
    <div class="cs-blue__bg" style="background-image:url({W}waves-white.svg)"></div>
    <div class="ex__lap" data-par="-0.05">{laptop(E+'d-hero.webp')}</div>
    <div class="ex__ph" data-par="-0.12">{phone(E+'m-form.webp')}</div>
  </div>
  <span class="wk__cur" aria-hidden="true">смотреть<br>кейс</span>
</a>
'''
    if not has_ex:
        body = re.sub(r'<!-- 06 ПРИМЕР -->.*?</a>\n', '', body, flags=re.S)
    faq = ''.join(f'<details class="faq__i"><summary>{esc(q)}<i aria-hidden="true"></i></summary><div class="faq__a"><p>{esc(a)}</p></div></details>' for q,a in d['faq'])
    body += f'''
<!-- 12 ВОПРОСЫ -->
<section aria-labelledby="faq-t">
  <div class="sec"><p class="aside">( вопросы )</p><h2 class="sec__t" id="faq-t" data-rv>Вопросы про <span class="mark c-b">{d['faq_word']}{U}</span></h2></div>
  <div class="card faq">{faq}</div>
</section>
'''
    more = ''.join(f'<a class="card more__i" href="{m[2]}" data-rv><span class="more__n">{esc(m[0])}</span><b>{esc(m[1])}</b>' + (f'<span class="more__d">{esc(m[4])}</span>' if len(m) > 4 else '') + f'<span class="more__p">{esc(m[3])}</span><span class="more__ar" aria-hidden="true">→</span></a>' for m in d['more'])
    body += f'''
<!-- 13 ДРУГИЕ УСЛУГИ -->
<section aria-labelledby="more-t">
  <div class="sec"><p class="aside">( {d.get('more_aside','ещё услуги')} )</p><h2 class="sec__t" id="more-t" data-rv>{d.get('more_title_a','Часто берут')} <span class="mark c-b">{d.get('more_title_b','вместе')}{U}</span></h2></div>
  <div class="more">{more}</div>
</section>
''' + CTA
    modal = MODAL
    head = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(d['meta'])}">
<meta property="og:title" content="{esc(title)}">
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
<body class="page-service">
<a class="skip" href="#main">Перейти к содержанию</a>

'''
    out = head + cur + MNAV + '<main id="main">\n\n' + body + '</main>\n\n' + FOOTER + modal + '<script src="assets/js/main.js" defer></script>\n</body>\n</html>\n'
    return rebase(out)

if __name__ == '__main__':
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    for d in data:
        p = os.path.join(OUT, 'uslugi', d['slug'], 'index.html')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(page(d))
        print('ok', p)
