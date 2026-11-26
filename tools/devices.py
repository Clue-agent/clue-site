# Макеты устройств clue: iPhone, iPad, MacBook, окно браузера, объёмный телефон и подиум.
# Картинка экрана подставляется как есть: телефон 390×844 (лучше 780×1688), планшет ~1.44:1, ноутбук 16:10.
# Строка состояния (9:41, связь, батарея) рисуется поверх экрана:
#   sb='light' — белая (для тёмных экранов), sb='dark' — чёрная (для светлых), sb='none' — не рисовать
#   (если на скриншоте из Figma строка состояния уже есть).
import html

def esc(t): return html.escape(t, quote=False)

SB_ICONS = ('<svg class="dv-sb__ic" viewBox="0 0 68 12" aria-hidden="true">'
            '<rect x="0" y="8" width="3" height="4" rx="1"/><rect x="4.5" y="6" width="3" height="6" rx="1"/>'
            '<rect x="9" y="3.5" width="3" height="8.5" rx="1"/><rect x="13.5" y="1" width="3" height="11" rx="1"/>'
            '<path d="M30 3.2a10 10 0 0 1 13.2 0l-1.4 1.5a8 8 0 0 0-10.4 0zM32.4 5.8a6.4 6.4 0 0 1 8.4 0l-1.4 1.5a4.4 4.4 0 0 0-5.6 0zM34.8 8.4a2.8 2.8 0 0 1 3.6 0L36.6 10.4z"/>'
            '<rect x="47.5" y="1.5" width="18" height="9" rx="2.6" fill="none" stroke="currentColor" stroke-opacity=".4"/>'
            '<rect x="49.5" y="3.5" width="14" height="5" rx="1.4"/><path d="M66.6 4.5v3a1.6 1.6 0 0 0 0-3z" opacity=".4"/></svg>')

def _screen(src, alt, w, h, sb, lazy=True):
    bar = '' if sb == 'none' else f'<span class="dv-sb dv-sb--{sb}" aria-hidden="true"><b>9:41</b>{SB_ICONS}</span>'
    ld = ' loading="lazy"' if lazy else ''
    return (f'<div class="dv-ph__in"><img src="{src}" alt="{esc(alt)}" width="{w}" height="{h}"{ld}>'
            f'{bar}<span class="dv-ph__di" aria-hidden="true"></span></div>')

def phone(src, alt='', cls='', sb='light', lazy=True):
    """iPhone: металлическая рамка, чёрное стекло, Dynamic Island, кнопки по бокам."""
    btn = ''.join(f'<i class="dv-ph__b dv-ph__b--{k}" aria-hidden="true"></i>' for k in ('act', 'vu', 'vd', 'pw'))
    return f'<div class="dv-ph {cls}">{btn}<div class="dv-ph__g">{_screen(src, alt, 390, 844, sb, lazy)}</div></div>'

def phone3d(src, alt='', sb='light'):
    """iPhone в пространстве: лицевая сторона + слои корпуса, кнопки на ребре и мягкая тень."""
    layers = ''.join(f'<i class="p3__l" style="--z:{k}"></i>' for k in range(1, 11))
    btns = ''.join(f'<span class="p3__btn p3__btn--{k}"></span>' for k in ('a', 'b', 'c', 'p'))
    return (f'<div class="p3"><div class="p3__sh" aria-hidden="true"></div><div class="p3__body">{layers}{btns}'
            f'<div class="p3__front dv-ph dv-ph--flat"><div class="dv-ph__g">{_screen(src, alt, 390, 844, sb, lazy=False)}</div></div></div></div>')

def tablet(src, alt='', cls=''):
    """iPad в горизонтальном положении: алюминиевая рамка, ровная тонкая рамка экрана, камера."""
    return (f'<div class="dv-tb {cls}"><i class="dv-tb__b dv-tb__b--1" aria-hidden="true"></i><i class="dv-tb__b dv-tb__b--2" aria-hidden="true"></i>'
            f'<div class="dv-tb__g"><span class="dv-tb__cam" aria-hidden="true"></span>'
            f'<div class="dv-tb__in"><img src="{src}" alt="{esc(alt)}" width="1180" height="820" loading="lazy"></div></div></div>')

def laptop(src, alt='', lazy=True):
    """MacBook: тонкая рамка с вырезом под камеру, алюминиевое основание."""
    ld = ' loading="lazy"' if lazy else ''
    return (f'<div class="laptop"><div class="laptop__scr"><img src="{src}" alt="{esc(alt)}" width="1440" height="900"{ld}></div>'
            f'<div class="laptop__base"></div></div>')

def browser(src, alt=''):
    return (f'<div class="dv-br"><div class="dv-br__bar"><i></i><i></i><i></i><span></span></div>'
            f'<img src="{src}" alt="{esc(alt)}" width="1440" height="900" loading="lazy"></div>')

def podium(inner):
    """Подиум-цилиндр, над которым парит устройство."""
    return f'<div class="pod"><div class="pod__dev">{inner}</div><div class="pod__sh" aria-hidden="true"></div><div class="pod__base" aria-hidden="true"></div></div>'
