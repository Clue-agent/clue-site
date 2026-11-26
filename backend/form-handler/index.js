'use strict';
/*
 * Обработчик формы заявки сайта clue — функция Yandex Cloud Functions (Node.js 22).
 *
 * Порядок работы:
 *   1. Принимает заявку только с разрешённых адресов сайта (CORS) и только методом POST.
 *   2. Антиспам: поле-ловушка, проверка времени заполнения, лимит частоты с одного адреса,
 *      обязательная Yandex SmartCaptcha (без неё заявка не принимается), фильтр повторов
 *      и подозрительного содержимого (ссылки, текст без кириллицы, типичные спам-фразы).
 *   3. Сохраняет копию заявки в Object Storage — заявка не теряется, даже если почта и Telegram недоступны.
 *   4. Отправляет заявку на почту (основной канал) и в Telegram (дополнительный).
 *
 * Все ключи — в переменных окружения, которые подставляются из Yandex Lockbox. В коде секретов нет.
 */

const crypto = require('crypto');
const nodemailer = require('nodemailer');

const env = (k, d = '') => (process.env[k] || d).trim();
const CFG = {
  origins: env('ALLOWED_ORIGINS').split(',').map(s => s.trim()).filter(Boolean),
  bucket: env('BUCKET'),
  salt: env('IP_SALT', 'clue'),
  captchaSecret: env('CAPTCHA_SECRET'),
  tgToken: env('TG_BOT_TOKEN'),
  tgChat: env('TG_CHAT_ID'),
  mailUser: env('MAIL_USER'),
  mailPass: env('MAIL_PASSWORD'),
  mailTo: env('MAIL_TO') || env('MAIL_USER'),
  smtpHost: env('SMTP_HOST', 'smtp.yandex.ru'),
  rateLimit: Number(env('RATE_LIMIT_PER_HOUR', '5')),
  minFillMs: Number(env('MIN_FILL_MS', '3000')),
  // 1 — без пройденной капчи заявка не принимается (посетитель увидит просьбу повторить или написать в Telegram);
  // 0 — такая заявка принимается, но помечается и приходит только на почту
  captchaStrict: env('CAPTCHA_STRICT', '1') !== '0',
  // свои стоп-фразы через запятую, дополняют встроенный список
  spamWords: env('SPAM_WORDS').split(',').map(s => s.trim().toLowerCase()).filter(Boolean)
};

const LIMITS = { name: 80, contact: 120, message: 3000, format: 40, page: 200 };
const FORMATS = ['Лендинг', 'Сайт компании', 'Редизайн', 'Дизайн', 'Пока не знаю'];

/* ---------- ответы ---------- */
const cors = origin => ({
  'Access-Control-Allow-Origin': origin,
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
  Vary: 'Origin'
});
const reply = (code, data, origin) => ({
  statusCode: code,
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'X-Content-Type-Options': 'nosniff', ...(origin ? cors(origin) : {}) },
  body: JSON.stringify(data)
});

/* ---------- очистка данных ---------- */
const clean = (v, max) => String(v == null ? '' : v)
  .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u200B-\u200F\u2028-\u202E\u2060-\u206F]/g, '')
  .trim()
  .slice(0, max);
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const looksLikeContact = c => /(\+?\d[\d\s()-]{6,}\d)|(^@?[a-z0-9_]{5,32}$)|(t\.me\/)|([^\s@]+@[^\s@]+\.[^\s@]+)/i.test(c);
// Типичные фразы рекламных рассылок. Совпадение не удаляет заявку, а только помечает её.
const SPAM_WORDS = ['casino', 'crypto', 'bitcoin', 'forex', 'viagra', 'backlink', 'guest post', 'seo service', 'rank your website',
  'web traffic', 'loan', 'betting', 'казино', 'ставки на спорт', 'букмекер', 'криптовалют', 'бинарн', 'заработок в интернете',
  'прогон', 'обратные ссылки', 'база email', 'рассылка по базе', 'кредит без'];
const spamWord = s => { const t = s.toLowerCase(); return [...SPAM_WORDS, ...CFG.spamWords].find(w => t.includes(w)) || ''; };
// Длинный текст без единой русской буквы — почти всегда зарубежная рассылка
const noCyrillic = s => s.replace(/[^a-zа-яё]/gi, '').length >= 20 && !/[а-яё]/i.test(s);
const hasLinks = s => /(https?:\/\/|www\.|\b[a-z0-9-]+\.(ru|com|net|org|by|io|xyz|top|info|biz|site|online)\b)/i.test(s);

/* ---------- Object Storage (доступ по IAM-токену сервисного аккаунта функции) ---------- */
const s3 = async (token, method, key, body, query = '') => {
  const url = `https://storage.yandexcloud.net/${CFG.bucket}/${key ? encodeURI(key) : ''}${query}`;
  const res = await fetch(url, {
    method,
    headers: { 'X-YaCloud-SubjectToken': token, ...(body ? { 'Content-Type': 'application/json; charset=utf-8' } : {}) },
    body
  });
  if (!res.ok) throw new Error(`storage ${method} ${res.status}`);
  return res;
};

const exists = async (token, key) => {
  const res = await fetch(`https://storage.yandexcloud.net/${CFG.bucket}/${encodeURI(key)}`, { method: 'HEAD', headers: { 'X-YaCloud-SubjectToken': token } });
  if (res.status === 404) return false;
  if (!res.ok) throw new Error(`storage HEAD ${res.status}`);
  return true;
};

const countRecent = async (token, ipHash) => {
  const res = await s3(token, 'GET', '', null, `?list-type=2&max-keys=100&prefix=${encodeURIComponent(`rl/${ipHash}/`)}`);
  const xml = await res.text();
  const hourAgo = Date.now() - 3600e3;
  return [...xml.matchAll(/<Key>rl\/[^/]+\/(\d+)-[^<]*<\/Key>/g)].filter(m => Number(m[1]) > hourAgo).length;
};

/* ---------- SmartCaptcha ---------- */
const checkCaptcha = async (token, ip) => {
  if (!CFG.captchaSecret) return 'off';
  if (!token) return 'missing';
  try {
    const body = new URLSearchParams({ secret: CFG.captchaSecret, token, ip });
    const res = await fetch('https://smartcaptcha.cloud.yandex.ru/validate', { method: 'POST', body, signal: AbortSignal.timeout(4000) });
    if (res.status !== 200) return 'error'; // по рекомендации Яндекса сбой сервиса не считается провалом
    const data = await res.json();
    return data.status === 'ok' ? 'ok' : 'fail';
  } catch (e) {
    console.error('captcha check error', e.message);
    return 'error'; // сервис проверки недоступен — заявку не теряем, помечаем для проверки
  }
};

/* ---------- доставка ---------- */
const sendMail = async (lead, flagged) => {
  if (!CFG.mailUser || !CFG.mailPass) throw new Error('mail not configured');
  const t = nodemailer.createTransport({ host: CFG.smtpHost, port: 465, secure: true, auth: { user: CFG.mailUser, pass: CFG.mailPass } });
  const lines = [
    ['Формат', lead.format], ['Имя', lead.name || '—'], ['Контакт', lead.contact],
    ['Задача', lead.message || '—'], ['Страница', lead.page || '—'], ['Время', lead.time], ['Номер', lead.id]
  ];
  const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(lead.contact);
  await t.sendMail({
    from: `"Сайт clue" <${CFG.mailUser}>`,
    to: CFG.mailTo,
    ...(isEmail ? { replyTo: lead.contact } : {}),
    subject: `${flagged ? '[проверить] ' : ''}Заявка: ${lead.format} — ${lead.name || lead.contact}`,
    text: lines.map(([k, v]) => `${k}: ${v}`).join('\n') + (flagged ? `\n\nПомечена как подозрительная: ${lead.flags.join(', ')}` : ''),
    html: `<table cellpadding="6" style="font:15px/1.45 Arial,sans-serif;border-collapse:collapse">${lines.map(([k, v]) =>
      `<tr><td style="color:#777;vertical-align:top">${k}</td><td style="white-space:pre-wrap">${esc(String(v))}</td></tr>`).join('')}</table>` +
      (flagged ? `<p style="color:#b00;font:14px Arial,sans-serif">Помечена как подозрительная: ${esc(lead.flags.join(', '))}</p>` : '')
  });
};

const sendTelegram = async text => {
  if (!CFG.tgToken || !CFG.tgChat) throw new Error('telegram not configured');
  const res = await fetch(`https://api.telegram.org/bot${CFG.tgToken}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: CFG.tgChat, text, parse_mode: 'HTML', disable_web_page_preview: true }),
    signal: AbortSignal.timeout(6000)
  });
  if (!res.ok) throw new Error(`telegram ${res.status}`);
};
const tgLead = (lead, note = '') =>
  `<b>Новая заявка · ${esc(lead.format)}</b>\n\n` +
  `<b>Имя:</b> ${esc(lead.name || '—')}\n<b>Контакт:</b> ${esc(lead.contact)}\n` +
  (lead.message ? `<b>Задача:</b>\n${esc(lead.message.slice(0, 1500))}\n` : '') +
  `\n<i>${esc(lead.page || '')}</i>${note ? `\n\n${esc(note)}` : ''}`;

/* ---------- основной обработчик ---------- */
module.exports.handler = async (event, context) => {
  const headers = Object.fromEntries(Object.entries(event.headers || {}).map(([k, v]) => [k.toLowerCase(), v]));
  const origin = headers.origin || '';
  const allowed = CFG.origins.includes(origin) ? origin : '';

  if (event.httpMethod === 'OPTIONS') return reply(allowed ? 204 : 403, {}, allowed);
  if (!allowed) return reply(403, { ok: false, error: 'origin' });
  if (event.httpMethod !== 'POST') return reply(405, { ok: false, error: 'method' }, allowed);

  let raw = event.body || '';
  if (event.isBase64Encoded) raw = Buffer.from(raw, 'base64').toString('utf8');
  if (raw.length > 20000) return reply(413, { ok: false, error: 'size' }, allowed);
  let d;
  try { d = JSON.parse(raw); } catch (e) { return reply(400, { ok: false, error: 'json' }, allowed); }

  const ip = (event.requestContext && event.requestContext.identity && event.requestContext.identity.sourceIp) || headers['x-forwarded-for'] || '0.0.0.0';
  const ipHash = crypto.createHash('sha256').update(CFG.salt + ip).digest('hex').slice(0, 24);
  const now = new Date();
  const lead = {
    id: now.getTime().toString(36) + crypto.randomBytes(3).toString('hex'),
    time: now.toISOString(),
    format: FORMATS.includes(clean(d.format, LIMITS.format)) ? clean(d.format, LIMITS.format) : 'Не указан',
    name: clean(d.name, LIMITS.name),
    contact: clean(d.contact, LIMITS.contact),
    message: clean(d.message, LIMITS.message),
    page: clean(d.page, LIMITS.page),
    agree: d.agree === true,
    ip: ipHash, // сам IP не храним — только необратимый отпечаток для лимита частоты
    flags: []
  };

  if (lead.contact.length < 3 || !lead.agree) return reply(422, { ok: false, error: 'fields' }, allowed);

  const token = context && context.token && context.token.access_token;
  if (!token || !CFG.bucket) {
    console.error('storage is not configured: add a service account to the function and set BUCKET');
    return reply(500, { ok: false, error: 'config' }, allowed);
  }

  // 1. Ловушка и время: бот получает «успех», но заявка уходит только в папку spam/
  const fillMs = Number(d.t) || 0;
  if (clean(d.website, 200)) lead.flags.push('ловушка');
  if (fillMs < CFG.minFillMs) lead.flags.push(`заполнено за ${Math.round(fillMs / 100) / 10} с`);
  if (lead.flags.length) {
    await s3(token, 'PUT', `spam/${lead.time.slice(0, 10)}/${lead.id}.json`, JSON.stringify(lead)).catch(e => console.error(e.message));
    return reply(200, { ok: true }, allowed);
  }

  // 2. Лимит частоты с одного адреса
  try {
    if (await countRecent(token, ipHash) >= CFG.rateLimit) return reply(429, { ok: false, error: 'rate' }, allowed);
    await s3(token, 'PUT', `rl/${ipHash}/${now.getTime()}-${lead.id}`, '{}');
  } catch (e) { console.error('rate limit check failed', e.message); }

  // 3. Капча: без неё заявка не принимается. Так отсекаются боты, которые шлют запросы
  //    напрямую в функцию, минуя форму (им ничего не стоит подделать время заполнения).
  //    Живой человек при сбое увидит просьбу повторить или написать в Telegram — заявка не теряется молча.
  const cap = await checkCaptcha(clean(d.token, 4000), ip);
  if ((cap === 'fail' || cap === 'missing') && CFG.captchaStrict) {
    lead.flags.push(`капча: ${cap === 'fail' ? 'не пройдена' : 'нет'}`);
    await s3(token, 'PUT', `spam/${lead.time.slice(0, 10)}/${lead.id}.json`, JSON.stringify(lead)).catch(e => console.error(e.message));
    return reply(400, { ok: false, error: 'captcha' }, allowed);
  }
  if (cap === 'fail' || cap === 'missing') lead.flags.push(`капча: ${cap === 'fail' ? 'не пройдена' : 'нет'}`);
  if (cap === 'error') lead.flags.push('капча: сервис недоступен');

  // 4. Содержимое и повторы: подозрительные не отбрасываем, а помечаем (приходят только на почту)
  const text = `${lead.name} ${lead.message}`;
  if (!looksLikeContact(lead.contact)) lead.flags.push('контакт не похож на телефон, ник или почту');
  if (hasLinks(lead.message) || hasLinks(lead.name)) lead.flags.push('ссылки в тексте');
  const sw = spamWord(`${text} ${lead.contact}`);
  if (sw) lead.flags.push(`спам-фраза: «${sw}»`);
  if (noCyrillic(lead.message)) lead.flags.push('текст без русских букв');
  try {
    const sum = crypto.createHash('sha256').update(`${lead.contact.toLowerCase()}|${lead.message.toLowerCase()}`).digest('hex').slice(0, 24);
    const dupKey = `dup/${lead.time.slice(0, 10)}/${sum}`;
    if (await exists(token, dupKey)) lead.flags.push('повтор: такая заявка сегодня уже была');
    else await s3(token, 'PUT', dupKey, '{}');
  } catch (e) { console.error('duplicate check failed', e.message); }
  const flagged = lead.flags.length > 0;

  // 5. Сохраняем копию — до любой отправки
  let saved = false;
  try {
    await s3(token, 'PUT', `${flagged ? 'check' : 'leads'}/${lead.time.slice(0, 10)}/${lead.id}.json`, JSON.stringify(lead, null, 2));
    saved = true;
  } catch (e) { console.error('save failed', e.message); }

  // 6. Доставка: почта и Telegram параллельно; подозрительные — только на почту с пометкой
  const [mail, tg] = await Promise.allSettled([
    sendMail(lead, flagged),
    flagged ? Promise.resolve('skip') : sendTelegram(tgLead(lead))
  ]);
  if (mail.status === 'rejected') {
    console.error('mail failed', mail.reason && mail.reason.message);
    if (!flagged) await sendTelegram(`⚠️ Письмо о заявке ${lead.id} не отправилось${saved ? ', копия сохранена в хранилище' : ''}.`).catch(() => {});
  }
  if (tg.status === 'rejected') console.error('telegram failed', tg.reason && tg.reason.message);

  const delivered = mail.status === 'fulfilled' || (tg.status === 'fulfilled' && tg.value !== 'skip');
  if (!saved && !delivered) {
    console.error('LEAD LOST RISK', JSON.stringify({ id: lead.id, format: lead.format }));
    return reply(502, { ok: false, error: 'delivery' }, allowed);
  }
  return reply(200, { ok: true, id: lead.id }, allowed);
};
