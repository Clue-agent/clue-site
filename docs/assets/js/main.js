/* Каждая страница открывается с самого начала (браузер не восстанавливает прошлую прокрутку).
   Исключение — ссылка с якорем (#раздел): тогда страница откроется на нужном разделе. */
(() => {
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  const top = () => { if (!location.hash) window.scrollTo({ top: 0, left: 0, behavior: 'instant' }); };
  top();
  window.addEventListener('pageshow', e => { if (e.persisted) top(); });
})();

(() => {
  const body = document.body;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Заголовки h1–h6: спокойное побуквенное появление (только прозрачность, без движения).
  // Каждая буква — пружина (tension 150, friction 24, масса 1), задержка 450 мс, шаг 34 мс.
  // Анимация на пружинах в JS, без CSS-переходов: её можно прервать, и она одинакова в любом браузере.
  (() => {
    const root = document.documentElement;
    const done = () => root.classList.add('ft-done');
    const heads = [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')].filter(h => !h.classList.contains('sr') && h.textContent.trim());
    if (reduce || !('IntersectionObserver' in window)) { done(); return; }
    const T = 150, F = 24, DELAY = 450, STAGGER = 34;
    const split = h => {
      const letters = [];
      const walk = node => {
        [...node.childNodes].forEach(n => {
          if (n.nodeType === 3) {
            if (!n.nodeValue.trim()) return;
            const frag = document.createDocumentFragment();
            n.nodeValue.split(/(\s+)/).forEach(part => {
              if (!part) return;
              if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(part)); return; }
              const w = document.createElement('span');
              w.className = 'tf__w';
              [...part].forEach(ch => {
                const l = document.createElement('span');
                l.className = 'tf__l'; l.textContent = ch; l.style.opacity = '0';
                w.appendChild(l); letters.push(l);
              });
              frag.appendChild(w);
            });
            n.replaceWith(frag);
          } else if (n.nodeType === 1 && n.namespaceURI !== 'http://www.w3.org/2000/svg') walk(n);
        });
      };
      if (!h.querySelector('a, button, input')) h.setAttribute('aria-label', h.textContent.replace(/\s+/g, ' ').trim());
      walk(h);
      h.querySelectorAll('.tf__w').forEach(w => w.setAttribute('aria-hidden', h.hasAttribute('aria-label') ? 'true' : 'false'));
      h.classList.add('tf');
      h.removeAttribute('data-rv');   // у заголовков своё появление — без сдвига снизу
      return letters;
    };
    const map = new Map();
    heads.forEach(h => map.set(h, split(h)));
    done();

    // одна петля на все буквы
    const active = new Set();
    let last = 0, raf = 0;
    const step = now => {
      const dt = Math.min(now - (last || now), 64); last = now;
      active.forEach(s => {
        if (now < s.t0) return;
        for (let i = 0; i < dt; i++) {        // шаг 1 мс — как у react-spring
          const a = -T * (s.x - 1) - F * s.v;
          s.v += a * 0.001; s.x += s.v * 0.001;
        }
        if (Math.abs(1 - s.x) < 0.001 && Math.abs(s.v) < 0.01) { s.el.style.opacity = ''; active.delete(s); }
        else s.el.style.opacity = Math.max(0, Math.min(1, s.x)).toFixed(3);
      });
      raf = active.size ? requestAnimationFrame(step) : 0;
      if (!raf) last = 0;
    };
    const play = h => {
      const t0 = performance.now() + DELAY;
      map.get(h).forEach((el, i) => active.add({ el, t0: t0 + i * STAGGER, x: 0, v: 0 }));
      if (!raf) raf = requestAnimationFrame(step);
    };
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { io.unobserve(e.target); play(e.target); }
    }), { threshold: 0.15 });
    heads.forEach(h => io.observe(h));
  })();

  // Первый экран: запуск анимации заголовка после загрузки шрифтов
  const ready = () => requestAnimationFrame(() => body.classList.add('is-ready'));
  if (document.fonts && document.fonts.ready) {
    Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 800))]).then(ready);
  } else ready();

  // Шапка: тень после прокрутки, прячется вниз, возвращается вверх
  const hd = document.getElementById('hd');
  let lastY = window.scrollY, ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    hd.classList.toggle('is-scrolled', y > 8);
    if (!body.classList.contains('menu-open')) {
      if (y > lastY && y > 160) hd.classList.add('is-hidden');
      else if (y < lastY - 4 || y < 160) hd.classList.remove('is-hidden');
    }
    lastY = y; ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });

  // Мобильное меню
  const burger = hd.querySelector('.hd__burger');
  const menu = document.getElementById('mnav');
  const setMenu = (open) => {
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    body.classList.toggle('menu-open', open);
    if (open) {
      menu.hidden = false;
      hd.classList.remove('is-hidden');
      requestAnimationFrame(() => menu.classList.add('is-open'));
      menu.querySelector('a').focus({ preventScroll: true });
    } else {
      menu.classList.remove('is-open');
      const hide = () => { if (!menu.classList.contains('is-open')) menu.hidden = true; };
      reduce ? hide() : setTimeout(hide, 350);
    }
  };
  burger.addEventListener('click', () => setMenu(burger.getAttribute('aria-expanded') !== 'true'));
  menu.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && body.classList.contains('menu-open')) { setMenu(false); burger.focus(); }
  });
  window.matchMedia('(min-width: 961px)').addEventListener('change', e => { if (e.matches) setMenu(false); });

  // Услуги в мобильном меню: раскрытие
  const acc = menu.querySelector('.mnav__acc');
  if (acc) {
    const accBtn = acc.querySelector('button');
    accBtn.addEventListener('click', () => {
      const open = !acc.classList.contains('is-open');
      acc.classList.toggle('is-open', open);
      accBtn.setAttribute('aria-expanded', String(open));
    });
  }

  // Выпадающее меню «услуги» в шапке
  const dd = document.getElementById('dd');
  if (dd) {
    const ddBtn = dd.querySelector('.dd__btn');
    let t;
    const ddSet = (open) => { clearTimeout(t); dd.classList.toggle('is-open', open); ddBtn.setAttribute('aria-expanded', String(open)); };
    const canHover = window.matchMedia('(hover: hover)').matches;
    if (canHover) {
      dd.addEventListener('mouseenter', () => ddSet(true));
      dd.addEventListener('mouseleave', () => { t = setTimeout(() => ddSet(false), 180); });
    }
    ddBtn.addEventListener('click', e => {
      if (!canHover || !dd.classList.contains('is-open')) { e.preventDefault(); ddSet(!dd.classList.contains('is-open')); }
    });
    ddBtn.addEventListener('keydown', e => { if (e.key === 'ArrowDown') { e.preventDefault(); ddSet(true); dd.querySelector('.dd__panel a').focus(); } });
    dd.addEventListener('focusout', e => { if (!dd.contains(e.relatedTarget)) ddSet(false); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && dd.classList.contains('is-open')) { ddSet(false); ddBtn.focus(); } });
    document.addEventListener('click', e => { if (!dd.contains(e.target)) ddSet(false); });
    dd.querySelectorAll('.dd__panel a').forEach(a => a.addEventListener('click', () => ddSet(false)));
  }

  // Появление при прокрутке (один раз)
  const items = document.querySelectorAll('[data-rv]');
  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add('is-in'));
  } else {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });
    items.forEach(el => io.observe(el));
  }

  // Как проходит: активный этап меняет экран рядом
  document.querySelectorAll('[data-steps]').forEach(sec => {
    const st = [...sec.querySelectorAll('.pr__s')], fr = [...sec.querySelectorAll('.pr__f')], dt = [...sec.querySelectorAll('.pr__dots i')];
    const stage = sec.querySelector('.pr__stage');
    const set = n => { [st, fr, dt].forEach(g => g.forEach((el, k) => el.classList.toggle('is-on', k === n))); if (stage) stage.dataset.step = n; };
    // активный — последний этап, верх которого уже прошёл середину экрана; работает в обе стороны
    let cur = 0, tick = false;
    const upd = () => {
      tick = false;
      const mid = window.innerHeight * 0.5;
      let n = 0;
      st.forEach((el, k) => { if (el.getBoundingClientRect().top <= mid) n = k; });
      if (n !== cur) { cur = n; set(n); }
    };
    window.addEventListener('scroll', () => { if (!tick) { tick = true; requestAnimationFrame(upd); } }, { passive: true });
    window.addEventListener('resize', upd);
    upd();
  });

  // Подбор услуги: вопрос слева — ответ справа
  document.querySelectorAll('[data-pick]').forEach(g => {
    const box = g.closest('section'), bs = [...g.querySelectorAll('button')], ps = [...box.querySelectorAll('.us-ans')];
    bs.forEach(b => b.addEventListener('click', () => {
      bs.forEach(x => { const on = x === b; x.classList.toggle('is-on', on); x.setAttribute('aria-selected', on); });
      ps.forEach(p => p.classList.toggle('is-on', p.dataset.p === b.dataset.p));
    }));
  });

  // Сайт компании: конструктор структуры
  document.querySelectorAll('[data-sitemap]').forEach(box => {
    const cbs = [...box.querySelectorAll('input[type=checkbox]')], kids = box.querySelector('.sm__kids');
    const cnt = box.querySelector('[data-sm-count]'), word = box.querySelector('[data-sm-word]'), rec = box.querySelector('[data-sm-rec]'), btn = box.querySelector('[data-sm-btn]');
    const plural = n => (n % 10 === 1 && n % 100 !== 11) ? 'раздел' : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) ? 'раздела' : 'разделов';
    const upd = () => {
      const on = cbs.filter(c => c.checked).map(c => c.value);
      const have = [...kids.children].map(li => li.dataset.v);
      have.forEach(v => { if (!on.includes(v)) { const li = kids.querySelector('[data-v="' + v + '"]'); li.classList.remove('is-in'); setTimeout(() => li.remove(), 350); } });
      on.forEach(v => { if (!have.includes(v)) { const li = document.createElement('li'); li.dataset.v = v; li.textContent = v; kids.appendChild(li); requestAnimationFrame(() => requestAnimationFrame(() => li.classList.add('is-in'))); } });
      const n = on.length + 1;
      cnt.textContent = n; word.textContent = plural(n);
      rec.textContent = n <= 5 ? 'Обычно хватает сайта-визитки — от 1 500 BYN' : 'Это сайт компании — от 2 500 BYN';
      btn.dataset.msg = 'Нужны разделы: Главная, ' + on.join(', ');
    };
    cbs.forEach(c => c.addEventListener('change', upd));
    upd();
  });

  // Фильтр проектов
  document.querySelectorAll('[data-filter]').forEach(g => {
    const list = document.querySelector('[data-filter-list]'); if (!list) return;
    const bs = [...g.querySelectorAll('button')];
    bs.forEach(b => b.addEventListener('click', () => {
      bs.forEach(x => x.classList.toggle('is-on', x === b));
      list.querySelectorAll('[data-type]').forEach(c => { const show = b.dataset.f === 'all' || c.dataset.type === 'all' || c.dataset.type === b.dataset.f; c.classList.toggle('is-hid', !show); });
    }));
  });

  // Вопросы: плавное раскрытие
  document.querySelectorAll('.faq__i').forEach(d => {
    d.classList.add('is-anim');
    if (d.open) d.classList.add('is-open');
    const sum = d.querySelector('summary');
    const ans = d.querySelector('.faq__a');
    sum.addEventListener('click', e => {
      e.preventDefault();
      if (!d.open) {
        d.open = true;
        void ans.offsetHeight;
        d.classList.add('is-open');
      } else {
        d.classList.remove('is-open');
        const close = () => { if (!d.classList.contains('is-open')) d.open = false; };
        reduce ? close() : setTimeout(close, 400);
      }
    });
  });

  // 404: свет на цифрах следует за курсором, на телефоне медленно гуляет сам
  const nf = document.querySelector('.nf'), nfc = nf && nf.querySelector('.nf__code');
  if (nf && nfc) {
    requestAnimationFrame(() => nf.classList.add('is-on'));
    if (!reduce) {
      let tx = 50, ty = 45, x = 50, y = 45, hand = false, t0 = performance.now();
      nf.addEventListener('pointermove', e => {
        if (e.pointerType !== 'mouse') return;
        const r = nfc.getBoundingClientRect(); hand = true;
        tx = (e.clientX - r.left) / r.width * 100; ty = (e.clientY - r.top) / r.height * 100;
      });
      nf.addEventListener('pointerleave', () => { hand = false; });
      const tick = now => {
        if (!hand) { const k = (now - t0) / 1000; tx = 50 + Math.sin(k * .45) * 34; ty = 45 + Math.cos(k * .6) * 22; }
        x += (tx - x) * .08; y += (ty - y) * .08;
        nfc.style.setProperty('--mx', x.toFixed(2) + '%'); nfc.style.setProperty('--my', y.toFixed(2) + '%');
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
  }

  // 3D-облачко в окне заявки слегка поворачивается за курсором
  document.querySelectorAll('.modal__side').forEach(side => {
    const m = side.querySelector('.m3d'); if (!m || reduce) return;
    side.addEventListener('pointermove', e => {
      const r = side.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      m.style.setProperty('--ry', (-18 + x * 30).toFixed(1) + 'deg');
      m.style.setProperty('--rx', (10 - y * 20).toFixed(1) + 'deg');
    });
    side.addEventListener('pointerleave', () => { m.style.removeProperty('--ry'); m.style.removeProperty('--rx'); });
  });

  // Cookie: спрашиваем один раз; аналитика включается только после согласия
  const ANALYTICS = {
    metrika: '',   // номер счётчика Яндекс Метрики, например '98765432'
    ga: ''         // идентификатор Google Analytics, например 'G-XXXXXXX'
  };
  const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  const loadAnalytics = () => {
    if (window.__clueAnalytics) return; window.__clueAnalytics = true;
    if (ANALYTICS.metrika) {
      (function (m, e, t, r, i, k, a) { m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); }; m[i].l = 1 * new Date(); k = e.createElement(t); a = e.getElementsByTagName(t)[0]; k.async = 1; k.src = r; a.parentNode.insertBefore(k, a); })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
      window.ym(ANALYTICS.metrika, 'init', { clickmap: true, trackLinks: true, accurateTrackBounce: true });
    }
    if (ANALYTICS.ga) {
      const g = document.createElement('script'); g.async = true; g.src = 'https://www.googletagmanager.com/gtag/js?id=' + ANALYTICS.ga; document.head.appendChild(g);
      window.dataLayer = window.dataLayer || []; window.gtag = function () { window.dataLayer.push(arguments); }; window.gtag('js', new Date()); window.gtag('config', ANALYTICS.ga);
    }
  };
  const showCookie = () => {
    if (document.querySelector('.ck')) return;
    const el = document.createElement('div');
    el.className = 'ck'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-live', 'polite'); el.setAttribute('aria-label', 'Cookie');
    const base = (document.querySelector('link[rel=stylesheet][href*="assets/css"]') || {}).getAttribute ? document.querySelector('link[rel=stylesheet][href*="assets/css"]').getAttribute('href').replace('assets/css/style.css', '') : '';
    el.innerHTML = '<div class="ck__ic" aria-hidden="true"><i></i><i></i><i></i></div>'
      + '<div class="ck__tx"><p class="ck__t">Немного статистики?</p><p class="ck__p">Cookie помогают понять, какие страницы полезны, а что улучшить. Без рекламы и слежки. <a href="' + base + 'politika/#p6">Подробнее</a></p></div>'
      + '<div class="ck__btns"><button type="button" class="ck__yes">хорошо</button><button type="button" class="ck__no">только нужные</button></div>';
    body.appendChild(el);
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('is-on')));
    const done = v => { store.set('clue-cookie', v); if (v === 'all') loadAnalytics(); el.classList.remove('is-on'); setTimeout(() => el.remove(), 700); };
    el.querySelector('.ck__yes').addEventListener('click', () => done('all'));
    el.querySelector('.ck__no').addEventListener('click', () => done('need'));
  };
  const ck = store.get('clue-cookie');
  if (ck === 'all') loadAnalytics();
  else if (!ck) setTimeout(showCookie, 1600);
  document.querySelectorAll('[data-cookie-reset]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); showCookie(); }));

  // Контакты: впишите ссылки сюда — они подставятся во все кнопки Telegram и Email на сайте
  const CONTACTS = {
    telegram: 'https://t.me/ClueDesign',
    email: ''       // например 'mailto:hello@clue.by'
  };
  // Форма заявки. Сейчас заявки уходят через Web3Forms на почту аккаунта Web3Forms.
  // Если позже подключите свой обработчик в Yandex Cloud (backend/form-handler/nastroika.md) —
  // впишите endpoint и captchaKey: тогда заявки пойдут туда, а web3formsKey можно оставить.
  const FORM = {
    endpoint: '',   // например 'https://functions.yandexcloud.net/d4e…'
    captchaKey: '', // ключ клиента SmartCaptcha, например 'ysc1_…'
    web3formsKey: '58a15bba-64c8-412c-8cfb-0bf89a8210f4'   // публичный ключ формы Web3Forms
  };
  document.querySelectorAll('[data-todo]').forEach(a => {
    const url = CONTACTS[a.dataset.todo];
    if (url) a.setAttribute('href', url);
    else { const li = a.closest('li'); (li || a).hidden = true; }   // контакта пока нет — не показываем пункт
  });

  // Ссылки, которые ещё не заполнены (Telegram, Email)
  document.querySelectorAll('[data-todo]').forEach(a => {
    if (a.getAttribute('href') === '#') {
      a.addEventListener('click', e => {
        e.preventDefault();
        console.warn('TODO: добавить ссылку для', a.dataset.todo);
      });
    }
  });

  // Формы заявки (на странице и в модальном окне)
  document.querySelectorAll('.form').forEach(form => {
    const contact = form.querySelector('[name="contact"]');
    const agree = form.querySelector('[name="agree"]');
    const status = form.querySelector('.form__status');
    const btn = form.querySelector('.form__submit');
    const lbl = form.querySelector('.form__lbl');
    const setErr = (el, wrap, on) => {
      wrap.classList.toggle('is-err', on);
      el.setAttribute('aria-invalid', String(on));
    };
    const nameEl = form.querySelector('[name="name"]');
    const msgEl = form.querySelector('[name="message"]');
    const contactErr = contact.closest('.field').querySelector('.field__err');
    const hcErr = form.querySelector('.form__hc-err');
    [nameEl, contact, msgEl].forEach(el => el.addEventListener('input', () => setErr(el, el.closest('.field'), false)));
    agree.addEventListener('change', () => setErr(agree, agree.closest('.check'), false));

    // Правила полей. Имя: 2–50 букв (любой алфавит), пробел, дефис, апостроф, точка; цифры и прочие знаки нельзя.
    // Контакт: телефон (7–15 цифр, можно + ( ) - и пробелы), Telegram (@ник: латиница, цифры, _, 5–32 знака; или t.me/ник) или email; до 100 знаков.
    // Сообщение: до 1000 знаков, нельзя < и >.
    const checkName = v => !v || /^\p{L}[\p{L} .'’-]{1,49}$/u.test(v);
    const checkContact = v => {
      if (!v) return 'Укажите, как с вами связаться';
      if (v.length > 100) return 'Слишком длинный контакт — до 100 символов';
      if (/^\+?[\d ()-]+$/.test(v)) {
        const n = v.replace(/\D/g, '').length;
        return n >= 7 && n <= 15 ? '' : 'В номере должно быть от 7 до 15 цифр';
      }
      if (/^(@|(https?:\/\/)?t\.me\/)/i.test(v) || /^[A-Za-z]\w*$/.test(v))
        return /^(@|(https?:\/\/)?t\.me\/)?[A-Za-z]\w{4,31}$/i.test(v) ? '' : 'Ник Telegram — 5–32 символа: латинские буквы, цифры и _';
      if (v.includes('@'))
        return /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(v) ? '' : 'Проверьте адрес почты';
      return 'Укажите телефон, ник Telegram (@ник) или email';
    };
    const checkMsg = v => v.length <= 1000 && !/[<>]/.test(v);

    // hCaptcha через Web3Forms: скрипт грузится при первом касании формы
    const loadHc = () => {
      if (!FORM.web3formsKey || FORM.endpoint || form.dataset.endpoint || window.__hcLoading) return;
      window.__hcLoading = true;
      const s = document.createElement('script');
      s.src = 'https://web3forms.com/client/script.js';
      s.async = true; s.defer = true;
      document.head.appendChild(s);
    };
    const hcToken = () => { const t = form.querySelector('[name="h-captcha-response"]'); return t ? t.value : ''; };
    const hcReset = () => { try { if (window.hcaptcha) window.hcaptcha.reset(); } catch (err) {} };
    form.addEventListener('focusin', loadHc);

    // Таймер заполнения и ленивая загрузка SmartCaptcha — при первом касании формы
    let t0 = 0, capId = null, capWait = null;
    const loadCaptcha = () => {
      if (!FORM.captchaKey || window.__scLoading) return;
      window.__scLoading = true;
      const sc = document.createElement('script');
      sc.src = 'https://smartcaptcha.cloud.yandex.ru/captcha.js?render=onload&onload=__clueSc';
      sc.defer = true;
      window.__clueSc = () => document.dispatchEvent(new Event('clue-sc'));
      document.head.appendChild(sc);
    };
    const initCaptcha = () => {
      if (capId !== null || !window.smartCaptcha) return;
      const box = form.querySelector('.form__cap');
      capId = window.smartCaptcha.render(box, {
        sitekey: FORM.captchaKey, invisible: true, hideShield: true, hl: 'ru',
        callback: tok => { if (capWait) { capWait(tok); capWait = null; } }
      });
      const note = form.querySelector('.form__sc'); if (note) note.hidden = false;
    };
    document.addEventListener('clue-sc', initCaptcha);
    form.addEventListener('focusin', () => { if (!t0) t0 = Date.now(); loadCaptcha(); initCaptcha(); });
    form.addEventListener('reset', () => { t0 = 0; if (capId !== null && window.smartCaptcha) window.smartCaptcha.reset(capId); });
    const getToken = () => new Promise(res => {
      if (capId === null || !window.smartCaptcha) return res('');
      const done = tok => { clearTimeout(tm); res(tok || ''); };
      const tm = setTimeout(() => { capWait = null; res(''); }, 10000);
      capWait = done;
      try { window.smartCaptcha.execute(capId); } catch (err) { done(''); }
    });
    const tgLink = '<a href="' + CONTACTS.telegram + '" target="_blank" rel="noopener">напишите в Telegram</a>';

    form.addEventListener('submit', async e => {
      e.preventDefault();
      status.textContent = '';
      const badName = !checkName(nameEl.value.trim());
      const contactMsg = checkContact(contact.value.trim());
      const badContact = !!contactMsg;
      const badMsg = !checkMsg(msgEl.value);
      const badAgree = !agree.checked;
      if (badContact) contactErr.textContent = contactMsg;
      setErr(nameEl, nameEl.closest('.field'), badName);
      setErr(contact, contact.closest('.field'), badContact);
      setErr(msgEl, msgEl.closest('.field'), badMsg);
      setErr(agree, agree.closest('.check'), badAgree);
      const firstBad = [[badName, nameEl], [badContact, contact], [badMsg, msgEl], [badAgree, agree]].find(x => x[0]);
      if (firstBad) { firstBad[1].focus(); return; }

      const endpoint = form.dataset.endpoint || FORM.endpoint;
      const viaW3F = !endpoint && !!FORM.web3formsKey;
      const hcTok = viaW3F ? hcToken() : '';
      hcErr.classList.toggle('is-on', viaW3F && !hcTok);
      if (viaW3F && !hcTok) { loadHc(); return; }
      if (!endpoint && !viaW3F) {
        status.innerHTML = 'Форма пока не подключена — ' + tgLink + '.';
        console.warn('Форма: впишите адрес обработчика в FORM.endpoint (main.js)');
        return;
      }
      btn.disabled = true;
      lbl.textContent = 'отправляем…';
      try {
        const token = await getToken();
        const fd = new FormData(form);
        const payload = {
          format: fd.get('format') || '', name: fd.get('name') || '', contact: fd.get('contact') || '',
          message: fd.get('message') || '', agree: agree.checked, website: fd.get('website') || '',
          t: t0 ? Date.now() - t0 : 0, token, page: location.pathname
        };
        let res;
        if (viaW3F) {
          // Боты: заполнили скрытое поле или отправили быстрее 3 секунд — показываем «успех», но ничего не отправляем
          const fast = payload.t > 0 && payload.t < 3000;
          if (payload.website || fast) res = { ok: true, status: 200 };
          else {
            const isMail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.contact.trim());
            const body = {
              access_key: FORM.web3formsKey,
              subject: 'Заявка с сайта clue: ' + (payload.format || 'без формата'),
              from_name: 'Сайт clue.by',
              'Формат': payload.format, 'Имя': payload.name, 'Контакт': payload.contact,
              'Сообщение': payload.message, 'Страница': location.href,
              botcheck: '', 'h-captcha-response': hcTok
            };
            if (isMail) body.replyto = payload.contact.trim();
            res = await fetch('https://api.web3forms.com/submit', {
              method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body)
            });
            if (res.ok) { const j = await res.json().catch(() => ({})); if (j && j.success === false) throw new Error('web3forms'); }
          }
        } else {
          res = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        }
        if (res.status === 429) { status.innerHTML = 'Слишком много заявок подряд. Попробуйте через час или ' + tgLink + '.'; return; }
        if (res.status === 400) { status.innerHTML = 'Не удалось подтвердить, что вы не робот. Нажмите «отправить» ещё раз или ' + tgLink + '.'; return; }
        if (!res.ok) throw new Error(res.status);
        form.querySelector('.form__body').hidden = true;
        const ok = form.querySelector('.form__ok');
        ok.hidden = false;
        ok.focus();
      } catch (err) {
        status.innerHTML = 'Не получилось отправить — текст сохранён в форме. Попробуйте ещё раз или ' + tgLink + '.';
      } finally {
        btn.disabled = false;
        lbl.textContent = 'отправить заявку';
        if (capId !== null && window.smartCaptcha) window.smartCaptcha.reset(capId);
        if (viaW3F) hcReset();
      }
    });
  });

  // Модальное окно заявки
  const modal = document.getElementById('m-lead');
  if (modal) {
    const box = modal.querySelector('.modal__box');
    const mform = modal.querySelector('form');
    let lastFocus = null, closeT;
    const focusables = () => [...modal.querySelectorAll('a[href], button:not([disabled]), input, textarea')].filter(el => el.offsetParent !== null);
    const resetForm = () => {
      const ok = mform.querySelector('.form__ok');
      if (!ok.hidden) { ok.hidden = true; mform.querySelector('.form__body').hidden = false; mform.reset(); }
      mform.querySelector('.form__status').textContent = '';
      mform.querySelectorAll('.is-err').forEach(el => el.classList.remove('is-err'));
    };
    const openModal = (fmt, msg) => {
      clearTimeout(closeT);
      lastFocus = document.activeElement;
      resetForm();
      if (fmt) { const r = mform.querySelector('input[name="format"][value="' + fmt + '"]'); if (r) r.checked = true; }
      if (msg) { const m = mform.querySelector('[name="message"]'); if (m) m.value = msg; }
      if (body.classList.contains('menu-open')) setMenu(false);
      const ddEl = document.getElementById('dd');
      if (ddEl) { ddEl.classList.remove('is-open'); }
      modal.hidden = false;
      body.classList.add('modal-open');
      box.scrollTop = 0;
      requestAnimationFrame(() => requestAnimationFrame(() => modal.classList.add('is-open')));
      box.focus({ preventScroll: true });
    };
    const closeModal = () => {
      modal.classList.remove('is-open');
      body.classList.remove('modal-open');
      closeT = setTimeout(() => { modal.hidden = true; }, reduce ? 0 : 650);
      if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
    };
    // кнопки с data-modal открывают окно вместо перехода к форме
    document.addEventListener('click', e => {
      const t = e.target.closest('[data-modal]');
      if (!t) return;
      e.preventDefault();
      e.stopPropagation();
      openModal(t.dataset.format, t.dataset.msg);
    }, true);
    modal.addEventListener('click', e => { if (e.target.closest('[data-close]')) closeModal(); });
    document.addEventListener('keydown', e => {
      if (modal.hidden || !modal.classList.contains('is-open')) return;
      if (e.key === 'Escape') { e.stopImmediatePropagation(); closeModal(); }
      if (e.key === 'Tab') {
        const f = focusables(); if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && (document.activeElement === first || document.activeElement === box)) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    }, true);
  }
})();

/* ===== Плавная прокрутка и эффекты при прокрутке ===== */
(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;
  const root = document.documentElement;
  const body = document.body;
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  let vh = window.innerHeight;
  window.addEventListener('resize', () => { vh = window.innerHeight; });

  /* --- плавная прокрутка колесом мыши (на тачпадах и телефонах — нативная) --- */
  const fine = window.matchMedia('(pointer: fine)').matches;
  let cur = window.scrollY, tgt = cur, running = false, last = 0;
  const maxY = () => root.scrollHeight - vh;
  const step = (t) => {
    const dt = last ? Math.min(64, t - last) : 16.7;
    last = t;
    cur += (tgt - cur) * (1 - Math.pow(1 - 0.042, dt / 16.7));
    if (Math.abs(tgt - cur) < 0.3) { cur = tgt; running = false; last = 0; }
    window.scrollTo(0, cur);
    if (running) requestAnimationFrame(step);
  };
  const go = (y) => {
    if (!running) { cur = window.scrollY; }
    tgt = clamp(y, 0, maxY());
    if (!running) { running = true; requestAnimationFrame(step); }
  };
  if (fine) {
    root.classList.add('smooth');
    window.addEventListener('wheel', (e) => {
      if (e.ctrlKey || body.classList.contains('menu-open') || body.classList.contains('modal-open')) return;
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      if (e.target.closest('textarea, [data-native-scroll]')) return;
      e.preventDefault();
      const k = e.deltaMode === 1 ? 40 : e.deltaMode === 2 ? vh : 1;
      if (!running) tgt = window.scrollY;
      go(tgt + e.deltaY * k * 0.85);
    }, { passive: false });
    // клавиатура и полоса прокрутки сбрасывают цель
    ['keydown', 'mousedown', 'touchstart'].forEach(ev => window.addEventListener(ev, () => { running = false; last = 0; }, { passive: true }));
  }
  // якорные ссылки — плавно
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || a.getAttribute('href').length < 2) return;
    const el = document.querySelector(a.getAttribute('href'));
    if (!el) return;
    e.preventDefault();
    const y = el.getBoundingClientRect().top + window.scrollY - 24;
    if (fine) go(y); else window.scrollTo({ top: y, behavior: 'smooth' });
    history.replaceState(null, '', a.getAttribute('href'));
  });

  /* --- кнопки: перекат текста, смена стрелки, заливка из точки входа курсора --- */
  if (window.matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('.btn, .pill, .tag').forEach(btn => {
      [...btn.childNodes].forEach(n => {
        if (n.nodeType !== 3 || !n.textContent.trim()) return;
        const t = n.textContent.trim();
        const roll = document.createElement('span');
        roll.className = 'roll';
        const inner = document.createElement('span');
        inner.dataset.t = t;
        inner.textContent = t;
        roll.appendChild(inner);
        n.replaceWith(roll);
      });
    });
    document.querySelectorAll('.btn__ar').forEach(ar => {
      ar.classList.add('is-sw');
      ar.innerHTML = '<span>' + ar.textContent + '</span>';
    });
    const setPt = (e) => {
      const b = e.currentTarget, r = b.getBoundingClientRect();
      b.style.setProperty('--x', (e.clientX - r.left) + 'px');
      b.style.setProperty('--y', (e.clientY - r.top) + 'px');
      b.style.setProperty('--d', (Math.hypot(r.width, r.height) * 2.1).toFixed(0) + 'px');
    };
    document.querySelectorAll('.btn').forEach(b => {
      b.addEventListener('pointerenter', setPt);
      b.addEventListener('pointerleave', setPt);
    });
  }

  /* --- элементы --- */
  const par = [...document.querySelectorAll('[data-par]')].map(el => ({ el, k: parseFloat(el.dataset.par) || 0 }));
  const stack = [...document.querySelectorAll('.stack__item')];
  const progs = [...document.querySelectorAll('[data-prog]')].map(el => ({ el, items: [...el.children] }));
  const cta = document.querySelector('.bigcta');
  const ctaC = cta && cta.querySelector('.bigcta__c');
  const ctaT = cta && cta.querySelector('.bigcta__t');
  const pin = cta && cta.querySelector('.bigcta__pin');
  let ctaX = null, ctaY = 0, ctaTx = 0, ctaTy = 0, ctaS = 1, hoverCta = false;
  if (pin && window.matchMedia('(hover: hover)').matches) {
    pin.addEventListener('pointermove', e => {
      const r = pin.getBoundingClientRect();
      hoverCta = true; ctaTx = e.clientX - r.left; ctaTy = e.clientY - r.top - r.height / 2;
    });
    pin.addEventListener('pointerleave', () => { hoverCta = false; });
    // клик в любом месте блока = клик по кругу (курсор и есть круг)
    pin.addEventListener('click', e => { if (!e.target.closest('.bigcta__c')) ctaC.click(); });
  }
  // проекты: синий круг «смотреть кейс» едет за курсором внутри картинки
  const wks = [];
  if (window.matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('.wk__im,[data-cur]').forEach(im => {
      if (!im.querySelector('.wk__cur')) return;   // карточка без ссылки — обычный курсор
      im.classList.add('has-cur');
      const o = { im, x: 0, y: 0, tx: 0, ty: 0, s: 0, on: false, init: false };
      im.addEventListener('pointerenter', e => { const r = im.getBoundingClientRect(); o.tx = e.clientX - r.left; o.ty = e.clientY - r.top; if (!o.on && o.s < 0.05) { o.x = o.tx; o.y = o.ty; } o.on = true; });
      im.addEventListener('pointermove', e => { const r = im.getBoundingClientRect(); o.tx = e.clientX - r.left; o.ty = e.clientY - r.top; });
      im.addEventListener('pointerleave', () => { o.on = false; });
      wks.push(o);
    });
    const wk = document.querySelector('.wk'); if (wk && wks.length) wk.classList.add('wk--cur');
  }
  const rows = [...document.querySelectorAll('.mq__row')].map(row => ({ row, track: row.querySelector('.mq__track'), dir: +row.dataset.dir || 1, x: 0, w: 0 }));
  const measureRows = () => rows.forEach(r => { r.w = r.track.scrollWidth / 3; });
  measureRows();
  window.addEventListener('resize', measureRows);
  if (document.fonts) document.fonts.ready.then(measureRows);

  let prevY = window.scrollY, vel = 0, sdir = 1, prevT = 0;

  const frame = (t) => {
    const y = window.scrollY;
    const dt = prevT ? Math.min(64, t - prevT) : 16.7;
    prevT = t;
    const dy = y - prevY;
    prevY = y;
    if (dy !== 0) sdir = dy > 0 ? 1 : -1;
    vel += (Math.abs(dy) - vel) * 0.1;

    // параллакс
    // сначала все замеры, потом все записи — без лишних пересчётов раскладки
    for (const p of par) {
      const r = p.el.parentElement.getBoundingClientRect();
      p.v = (r.bottom < -200 || r.top > vh + 200) ? null : (r.top + r.height / 2 - vh / 2) * p.k;
    }
    for (const p of par) {
      if (p.v === null) continue;
      const v = Math.round(p.v * 2) / 2;          // полпикселя достаточно, меньше лишних перерисовок
      if (v !== p.last) { p.el.style.setProperty('--py', v + 'px'); p.last = v; }
    }

    // стек карточек: предыдущая уменьшается, когда следующая наезжает
    for (let i = 0; i < stack.length - 1; i++) {
      const next = stack[i + 1].getBoundingClientRect();
      const top = parseFloat(getComputedStyle(stack[i]).top) || 0;
      const sp = clamp(1 - (next.top - top) / (vh * 0.85));
      stack[i].style.setProperty('--sp', sp.toFixed(3));
    }

    // прогресс-линии
    for (const g of progs) {
      const r = g.el.getBoundingClientRect();
      const p = clamp((vh * 0.75 - r.top) / (r.height + vh * 0.15));
      g.el.style.setProperty('--p', p.toFixed(3));
      const n = g.items.length;
      g.items.forEach((li, i) => li.classList.toggle('is-on', p >= (i + 0.25) / n));
    }

    // большой круг: едет за курсором с задержкой
    if (cta && pin) {
      const r = pin.getBoundingClientRect();
      if (r.top < vh && r.bottom > 0) {
        // надпись немного едет влево по ходу прокрутки страницы
        if (ctaT) {
          const pp = clamp((vh - r.top) / (vh + r.height));
          ctaT.style.transform = `translate3d(${((0.5 - pp) * 0.4 * window.innerWidth).toFixed(1)}px,0,0)`;
        }
        if (!hoverCta) { ctaTx = r.width * 0.5; ctaTy = 0; }
        if (ctaX === null) { ctaX = ctaTx; ctaY = ctaTy; }
        const k = 1 - Math.pow(1 - 0.09, dt / 16.7);
        ctaX += (ctaTx - ctaX) * k; ctaY += (ctaTy - ctaY) * k;
        ctaS += ((hoverCta ? 1.08 : 1) - ctaS) * k;
        cta.style.setProperty('--cx', ctaX.toFixed(1) + 'px');
        cta.style.setProperty('--cy', ctaY.toFixed(1) + 'px');
        cta.style.setProperty('--s', ctaS.toFixed(3));
      }
    }

    for (const o of wks) {
      if (!o.on && o.s < 0.002) continue;
      const k = 1 - Math.pow(1 - 0.12, dt / 16.7);
      o.x += (o.tx - o.x) * k; o.y += (o.ty - o.y) * k;
      o.s += ((o.on ? 1 : 0) - o.s) * k;
      o.im.style.setProperty('--mx', o.x.toFixed(1) + 'px');
      o.im.style.setProperty('--my', o.y.toFixed(1) + 'px');
      o.im.style.setProperty('--ms', o.s.toFixed(3));
    }

    // бегущие строки: ровная скорость, направление не зависит от прокрутки
    for (const r of rows) {
      if (!r.w) continue;
      r.x -= r.dir * 0.6 * (dt / 16.7);
      if (r.x <= -r.w) r.x += r.w;
      if (r.x > 0) r.x -= r.w;
      r.track.style.transform = `translate3d(${r.x.toFixed(2)}px,0,0)`;
    }

    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
})();
