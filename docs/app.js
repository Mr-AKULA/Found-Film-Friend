/* ═══════════════════════════════════════════════════════
   Found Film Friend — Web App
   Supabase + Vanilla JS

   SETUP:
   1. Create a project at https://supabase.com
   2. Run docs/supabase.sql in the SQL Editor
   3. Replace SUPABASE_URL and SUPABASE_ANON_KEY below
   4. Push to GitHub, enable GitHub Pages from /docs folder
   ═══════════════════════════════════════════════════════ */

const SUPABASE_URL     = 'https://swgvbagncvbkoyztrimz.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_0NHWJrnl1boP_Ma0hLH9Ew_m684L-5J';

/* ─── Telegram Mini App ─── */
const TG    = window.Telegram?.WebApp;
const IS_TG = !!(TG?.initDataUnsafe?.user);
if (IS_TG) {
  TG.expand();
  TG.disableVerticalSwipes?.();
  TG.setHeaderColor?.('#0a0a0f');
  TG.setBackgroundColor?.('#0a0a0f');
}


/* ─── Supabase client ─── */
/* persistSession:false keeps session in JS memory only — avoids 401 errors
   caused by Firefox/Edge Tracking Prevention silently blocking localStorage */
const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/* ─── App state ─── */
const state = {
  user:           null,
  profile:        null,
  currentMovie:   null,
  pendingFriend:  null,   // from invite link
  pendingMovieId: null,   // ?movie=ID — open after login
  currentFriend:  null,   // { id, name } — open friend panel
  genres:         [],     // all genres from DB
  selectedGenres: [],     // genre IDs to include (p_genre_ids)
  excludeGenres:  [],     // genre IDs to exclude (p_exclude_genre_ids)
  quickFilter:    null,   // 'films' | 'mults' | null
  lastAction:     null,   // { movie, type } — for undo
  sharingMovie:   null,   // movie being shared
  theme:          'dark', // active theme id
  lang:           'ru',   // 'ru' | 'en'
  merging:        false,  // true during account merge — suppresses onAuthStateChange
};

/* ─── Init theme, lang & hints from localStorage ─── */
(function initPrefs() {
  try {
    const savedTheme = localStorage.getItem('fff_theme') || 'dark';
    const savedLang  = localStorage.getItem('fff_lang') || (navigator.language?.startsWith('en') ? 'en' : 'ru');
    state.theme = savedTheme;
    state.lang  = savedLang;
    if (savedTheme && savedTheme !== 'dark') {
      document.documentElement.dataset.theme = savedTheme;
    }
    if (localStorage.getItem('fff_hints') === 'true') {
      document.documentElement.classList.add('show-hints');
    }
  } catch {}
})();

/* Force HTTPS so HTTP images aren't blocked on the HTTPS page */
function safeImgUrl(url) {
  return url ? url.replace(/^http:\/\//i, 'https://') : url;
}

/* ══════════════════════════════════════════════
   DOM HELPERS
══════════════════════════════════════════════ */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function show(el)  { el?.classList.remove('hidden'); }
function hide(el)  { el?.classList.add('hidden'); }
function toggle(el, cond) { cond ? show(el) : hide(el); }

function showToast(msg, duration = 2500) {
  const t = $('#toast');
  t.textContent = msg;
  show(t);
  clearTimeout(t._timer);
  t._timer = setTimeout(() => hide(t), duration);
}

/* ══════════════════════════════════════════════
   AUTH
══════════════════════════════════════════════ */

async function signInWithTelegram(tgUser) {
  const tgEmail    = `tg_${tgUser.id}@fff.app`;
  const tgPassword = btoa(`fff_tg_${tgUser.id}_v1`).replace(/=/g, '');

  /* Check if this telegram_id is linked to a browser account after merge */
  const { data: linked } = await sb.from('profiles')
    .select('auth_email')
    .eq('telegram_id', String(tgUser.id))
    .maybeSingle();

  const loginEmail = linked?.auth_email || tgEmail;

  /* Try sign in (works for both native TG accounts and linked browser accounts) */
  const { data, error } = await sb.auth.signInWithPassword({ email: loginEmail, password: tgPassword });
  if (!error && data.session) {
    const displayName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ')
                        || tgUser.username || null;
    sb.from('profiles').update({
      ...(displayName ? { display_name: displayName } : {}),
      telegram_id:       String(tgUser.id),
      telegram_username: tgUser.username || null,
    }).eq('id', data.user.id).then(() => {});
    return;
  }

  /* New user — first time */
  const displayName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ')
                      || tgUser.username || 'Пользователь';

  const { data: up, error: upErr } = await sb.auth.signUp({ email: tgEmail, password: tgPassword });
  if (upErr) {
    console.error('[TG] signup:', upErr.message);
    showToast('Ошибка входа: ' + upErr.message, 4000);
    return;
  }

  if (up.user) {
    await sb.from('profiles').upsert({
      id:                up.user.id,
      display_name:      displayName,
      telegram_id:       String(tgUser.id),
      telegram_username: tgUser.username || null,
    }, { onConflict: 'id' });
    if (!up.session) {
      showToast('Отключи "Confirm email" в Supabase Auth → Settings', 6000);
    }
  }
}

function mergeStatus(msg, isError = false) {
  const el = $('#tg-merge-status');
  if (!el) return;
  el.style.display = 'block';
  el.style.background = isError ? 'rgba(244,63,94,0.15)' : 'rgba(167,139,250,0.12)';
  el.style.border = isError ? '1px solid rgba(244,63,94,0.3)' : '1px solid rgba(167,139,250,0.25)';
  el.style.color = isError ? '#f87171' : '#c4b5fd';
  el.textContent = msg;
}

async function mergeAccounts(browserEmail, browserPassword) {
  const tgUser     = TG.initDataUnsafe.user;
  const tgPassword = btoa(`fff_tg_${tgUser.id}_v1`).replace(/=/g, '');
  const tgUserId   = state.user.id;

  state.merging = true;

  mergeStatus('Шаг 1/3: проверяю данные...');
  const { data, error } = await sb.auth.signInWithPassword({
    email: browserEmail, password: browserPassword,
  });
  if (error) {
    state.merging = false;
    mergeStatus('Ошибка: ' + error.message, true);
    await sb.auth.signInWithPassword({ email: `tg_${tgUser.id}@fff.app`, password: tgPassword });
    return false;
  }

  const browserUserId = data.user.id;
  if (browserUserId === tgUserId) {
    state.merging = false;
    mergeStatus('Это уже один и тот же аккаунт', true);
    return false;
  }

  mergeStatus('Шаг 2/3: объединяю данные...');
  const { error: mergeErr } = await sb.rpc('merge_accounts', {
    from_user_id:        tgUserId,
    to_user_id:          browserUserId,
    p_telegram_id:       String(tgUser.id),
    p_telegram_username: tgUser.username || null,
    p_tg_password:       tgPassword,
  });

  if (mergeErr) {
    state.merging = false;
    mergeStatus('Ошибка RPC: ' + mergeErr.message, true);
    await sb.auth.signInWithPassword({ email: `tg_${tgUser.id}@fff.app`, password: tgPassword });
    return false;
  }

  mergeStatus('Шаг 3/3: вхожу в объединённый аккаунт...');
  /* Update browser account password to TG-derived so auto-login works next time */
  await sb.auth.updateUser({ password: tgPassword });
  state.merging = false;
  /* We're already signed in as the browser account — use that session directly */
  await onSignedIn(data.user);
  return true;
}

async function initAuth() {
  /* Check for invite param ?invite=UUID — also persist in sessionStorage
     so it survives email-confirmation redirects that lose the URL params */
  const params = new URLSearchParams(location.search);
  const inviteId = params.get('invite');
  if (inviteId) {
    state.pendingFriend = inviteId;
    try { sessionStorage.setItem('fff_invite', inviteId); } catch {}
  } else {
    try {
      const stored = sessionStorage.getItem('fff_invite');
      if (stored) state.pendingFriend = stored;
    } catch {}
  }

  const movieParam = params.get('movie');
  if (movieParam) {
    state.pendingMovieId = parseInt(movieParam);
    try { sessionStorage.setItem('fff_movie', movieParam); } catch {}
  } else {
    try {
      const stored = sessionStorage.getItem('fff_movie');
      if (stored) state.pendingMovieId = parseInt(stored);
    } catch {}
  }

  /* Detect password recovery from URL hash — Supabase adds #type=recovery
     after the user clicks the reset link in the email.
     We handle this BEFORE getSession() to prevent auto-login:
     manually call setSession() with the tokens so updateUser() works,
     then show the newpass form and return early. */
  const hashParams = new URLSearchParams(location.hash.replace(/^#/, ''));
  if (hashParams.get('type') === 'recovery') {
    showScreen('auth');
    showAuthForm('newpass');

    /* Manually establish the recovery session so updateUser() can run.
       detectSessionInUrl would eventually do this but fires SIGNED_IN
       which would navigate away from the newpass form. */
    const accessToken  = hashParams.get('access_token');
    const refreshToken = hashParams.get('refresh_token');
    if (accessToken && refreshToken) {
      await sb.auth.setSession({ access_token: accessToken, refresh_token: refreshToken });
    }

    /* Clear the hash so the tokens don't linger in the URL */
    history.replaceState(null, '', location.pathname);

    sb.auth.onAuthStateChange(async (_event, _session) => {
      /* Ignore SIGNED_IN that fires after setSession — stay on newpass form.
         Only react to explicit signOut (no session) → back to login. */
      if (_event === 'SIGNED_OUT') showScreen('auth');
    });
    return;
  }

  /* Telegram Mini App — отдельный поток авторизации, return в конце */
  if (IS_TG && TG.initDataUnsafe?.user) {
    TG.ready();
    sb.auth.onAuthStateChange(async (_event, session) => {
      if (state.merging) return; // skip intermediate sessions during account merge
      if (session) await onSignedIn(session.user);
    });
    await signInWithTelegram(TG.initDataUnsafe.user);
    return;
  }

  /* Обычный веб-флоу */
  const { data: { session } } = await sb.auth.getSession();
  if (session) {
    await onSignedIn(session.user);
  } else {
    showScreen('auth');
  }

  sb.auth.onAuthStateChange(async (_event, session) => {
    if (_event === 'PASSWORD_RECOVERY') {
      showScreen('auth');
      showAuthForm('newpass');
      return;
    }
    if (session) await onSignedIn(session.user);
    else         showScreen('auth');
  });
}

async function onSignedIn(user) {
  state.user = user;

  /* Load or create profile */
  let { data: profile } = await sb.from('profiles').select('*').eq('id', user.id).single();
  if (!profile) {
    /* First time — profile created by DB trigger, just reload */
    await new Promise(r => setTimeout(r, 500));
    const res = await sb.from('profiles').select('*').eq('id', user.id).single();
    profile = res.data;
  }
  state.profile = profile;

  /* Handle pending friend invite */
  if (state.pendingFriend && state.pendingFriend !== user.id) {
    showFriendBanner(state.pendingFriend);
  }

  /* Set up invite link */
  const link = `${location.origin}${location.pathname}?invite=${user.id}`;
  $('#invite-link').textContent = link;

  showScreen('app');
  App.navigate('browse');
  loadGenres().then(() => checkOnboarding());
  App.loadNextMovie();

  /* Check unread recommendations count for badge */
  sb.from('recommendations')
    .select('id', { count: 'exact', head: true })
    .eq('to_user', user.id)
    .eq('seen', false)
    .then(({ count }) => updateRecBadge(count || 0));

  /* Open shared movie if came via ?movie=ID link */
  if (state.pendingMovieId) {
    openSharedMovie(state.pendingMovieId);
    state.pendingMovieId = null;
    try { sessionStorage.removeItem('fff_movie'); } catch {}
    history.replaceState({}, '', location.pathname);
  }
}

/* ══════════════════════════════════════════════
   ONBOARDING
══════════════════════════════════════════════ */
async function checkOnboarding() {
  const { count } = await sb
    .from('actions')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', state.user.id);
  if (count === 0 && state.genres.length > 0) showOnboarding();
}

function showOnboarding() {
  const container = $('#onboarding-genres');
  container.innerHTML = '';
  state.genres.forEach(g => {
    const btn = document.createElement('button');
    btn.className = 'onboarding-genre';
    btn.textContent = g.name;
    btn.dataset.id = g.id;
    btn.addEventListener('click', () => btn.classList.toggle('active'));
    container.appendChild(btn);
  });
  show($('#onboarding'));
}

/* ══════════════════════════════════════════════
   STATS
══════════════════════════════════════════════ */
async function openStats() {
  const uid = state.user.id;
  $('#stats-content').innerHTML = '<div class="spinner" style="margin:24px auto"></div>';
  show($('#stats-modal'));

  const [{ data: actions }, { data: friends }] = await Promise.all([
    sb.from('actions').select('movie_id, want_to_watch, watched').eq('user_id', uid),
    sb.from('friends').select('id').or(`user_one.eq.${uid},user_two.eq.${uid}`).eq('status', 1),
  ]);

  const total   = (actions || []).length;
  const liked   = (actions || []).filter(a => a.want_to_watch === true).length;
  const watched = (actions || []).filter(a => a.watched === true).length;
  const skipped = total - liked - watched;

  let topGenresHtml = '';
  const likedIds = (actions || []).filter(a => a.want_to_watch).map(a => a.movie_id);
  if (likedIds.length > 0) {
    const { data: mg } = await sb
      .from('movie_genres')
      .select('genre_id, genres(name)')
      .in('movie_id', likedIds);

    const counts = {};
    (mg || []).forEach(r => {
      const n = r.genres?.name;
      if (n) counts[n] = (counts[n] || 0) + 1;
    });
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const max = top[0]?.[1] || 1;
    topGenresHtml = top.map(([name, cnt]) => `
      <div class="stat-genre-row">
        <span class="stat-genre-name">${escHtml(name)}</span>
        <div class="stat-genre-bar-wrap">
          <div class="stat-genre-bar" style="width:${Math.round(cnt/max*100)}%"></div>
        </div>
        <span class="stat-genre-cnt">${cnt}</span>
      </div>`).join('');
  }

  $('#stats-content').innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-num">${total}</div><div class="stat-lbl">Оценено</div></div>
      <div class="stat-card stat-card-like"><div class="stat-num">${liked}</div><div class="stat-lbl">❤️ Хочу</div></div>
      <div class="stat-card stat-card-watch"><div class="stat-num">${watched}</div><div class="stat-lbl">👁 Смотрел</div></div>
      <div class="stat-card"><div class="stat-num">${(friends||[]).length}</div><div class="stat-lbl">Друзей</div></div>
    </div>
    ${total > 0 ? `<p class="stat-pct">❤️ нравится <b>${Math.round(liked/total*100)}%</b> фильмов</p>` : ''}
    ${topGenresHtml ? `<div class="stats-genres-section"><p class="stats-section-lbl">Любимые жанры</p>${topGenresHtml}</div>` : ''}
  `;
}

async function loadGenres() {
  const { data } = await sb.from('genres').select('id, name').order('name');
  if (!data) return;
  state.genres = data;
  renderGenrePills();
}

function renderGenrePills() {
  const container = $('#genre-pills');
  if (!container) return;
  container.innerHTML = '';

  const multGenre = state.genres.find(g => g.name.toLowerCase().includes('мульт'));

  const ANIM_WORDS = ['мульт', 'аниме', 'anime', 'animation'];
  const animIds = state.genres
    .filter(g => ANIM_WORDS.some(w => g.name.toLowerCase().includes(w)))
    .map(g => g.id);

  function applyFilter({ include = [], exclude = [], qf = null } = {}) {
    state.selectedGenres = include;
    state.excludeGenres  = exclude;
    state.quickFilter    = qf;
    renderGenrePills();
    state.currentMovie = null;
    App.loadNextMovie();
  }

  /* ── Все ── */
  const allBtn = document.createElement('button');
  allBtn.className = 'genre-pill' + (state.quickFilter === null && state.selectedGenres.length === 0 ? ' active' : '');
  allBtn.textContent = 'Все';
  allBtn.addEventListener('click', () => applyFilter());
  container.appendChild(allBtn);

  /* ── 🎬 Фильмы (exclude мульт+аниме) ── */
  const filmsBtn = document.createElement('button');
  filmsBtn.className = 'genre-pill genre-pill-special' + (state.quickFilter === 'films' ? ' active' : '');
  filmsBtn.textContent = '🎬 Фильмы';
  filmsBtn.addEventListener('click', () => applyFilter({ exclude: animIds, qf: 'films' }));
  container.appendChild(filmsBtn);

  /* ── 🎨 Мульты (include мульт+аниме) ── */
  const multBtn = document.createElement('button');
  multBtn.className = 'genre-pill genre-pill-special' + (state.quickFilter === 'mults' ? ' active' : '');
  multBtn.textContent = '🎨 Мульты';
  multBtn.addEventListener('click', () => applyFilter({ include: animIds, qf: 'mults' }));
  container.appendChild(multBtn);

  /* ── Отдельные жанры ── */
  state.genres.forEach(g => {
    const btn = document.createElement('button');
    btn.className = 'genre-pill' + (state.quickFilter === null && state.selectedGenres.includes(g.id) ? ' active' : '');
    btn.textContent = g.name;
    btn.addEventListener('click', () => {
      if (state.quickFilter !== null || state.excludeGenres.length > 0) {
        /* Was in quick-filter mode — start fresh with just this genre */
        state.quickFilter   = null;
        state.excludeGenres = [];
        state.selectedGenres = [g.id];
      } else {
        const idx = state.selectedGenres.indexOf(g.id);
        if (idx === -1) state.selectedGenres.push(g.id);
        else            state.selectedGenres.splice(idx, 1);
      }
      renderGenrePills();
      state.currentMovie = null;
      App.loadNextMovie();
    });
    container.appendChild(btn);
  });
}

/* ══════════════════════════════════════════════
   UNDO
══════════════════════════════════════════════ */
let _undoTimer = null;

function showUndo() {
  const btn = $('#undo-btn');
  if (!btn) return;
  btn.classList.remove('hidden');
  clearTimeout(_undoTimer);
  _undoTimer = setTimeout(() => btn.classList.add('hidden'), 3500);
}

async function undoLastAction() {
  if (!state.lastAction) return;
  const { movie, type } = state.lastAction;
  state.lastAction = null;
  $('#undo-btn')?.classList.add('hidden');
  clearTimeout(_undoTimer);

  await sb.from('actions')
    .delete()
    .eq('user_id', state.user.id)
    .eq('movie_id', movie.id);

  /* Restore the card immediately */
  state.currentMovie = movie;
  renderMovieCard(movie);
  show($('#browse-main'));
  hide($('#browse-loading'));
  hide($('#browse-empty'));
  showToast('Отменено ↩');
}

/* ══════════════════════════════════════════════
   I18N (INTERNATIONALIZATION)
══════════════════════════════════════════════ */
const I18N = {
  ru: {
    nav_browse:   'Смотреть',
    nav_watchlist:'Список',
    nav_friends:  'Друзья',
    save:         'Сохранить',
    cancel:       'Отмена',
    settings_appearance: 'Оформление',
    settings_language:   'Язык',
    settings_more:       'Скоро',
    settings_notifs:     'Уведомления',
    settings_genres_default: 'Жанры по умолчанию',
    settings_privacy:    'Приватность',
    settings_soon:       'Скоро',
    sign_out:            'Выйти из аккаунта',
    settings_name_ph:    'Ваше имя',
    swipe_hint:          '← скип · 👁 смотрел · ❤️ хочу →',
    browse_empty_title:  'Вы всё оценили!',
    browse_empty_sub:    'Скоро добавим новые фильмы',
    watchlist_title:     'Мой список',
    watchlist_search_ph: 'Поиск по названию...',
    friends_title:       'Друзья',
    share_to_friend:     'Другу в FFF',
    share_copy:          'Скопировать ссылку',
    share_native:        'Поделиться…',
  },
  en: {
    nav_browse:   'Browse',
    nav_watchlist:'Watchlist',
    nav_friends:  'Friends',
    save:         'Save',
    cancel:       'Cancel',
    settings_appearance: 'Appearance',
    settings_language:   'Language',
    settings_more:       'Coming soon',
    settings_notifs:     'Notifications',
    settings_genres_default: 'Default genres',
    settings_privacy:    'Privacy',
    settings_soon:       'Soon',
    sign_out:            'Sign out',
    settings_name_ph:    'Your name',
    swipe_hint:          '← skip · 👁 watched · ❤️ like →',
    browse_empty_title:  'You rated everything!',
    browse_empty_sub:    'New movies coming soon',
    watchlist_title:     'My List',
    watchlist_search_ph: 'Search by title...',
    friends_title:       'Friends',
    share_to_friend:     'Friend in FFF',
    share_copy:          'Copy link',
    share_native:        'Share…',
  },
};

function t(key) {
  return I18N[state.lang]?.[key] ?? I18N.ru[key] ?? key;
}

function applyLang() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPh);
  });
  /* Update dynamic search placeholder */
  const srch = $('#watchlist-search');
  if (srch) srch.placeholder = t('watchlist_search_ph');
  /* Update swipe hint */
  const hint = $('.swipe-hint');
  if (hint) hint.textContent = t('swipe_hint');
  /* Update page titles */
  const wlTitle = $('#page-watchlist .page-title');
  if (wlTitle) wlTitle.textContent = t('watchlist_title');
  const frTitle = $('#page-friends .page-title');
  if (frTitle) frTitle.textContent = t('friends_title');
}

/* ══════════════════════════════════════════════
   THEMES
══════════════════════════════════════════════ */
const THEMES = [
  { id: 'dark',     nameRu: 'Тёмная',   nameEn: 'Dark',     colors: ['#080810','#7c3aed'] },
  { id: 'midnight', nameRu: 'Полночь',  nameEn: 'Midnight', colors: ['#03030f','#3b82f6'] },
  { id: 'sunset',   nameRu: 'Закат',    nameEn: 'Sunset',   colors: ['#0d0806','#f97316'] },
  { id: 'forest',   nameRu: 'Лес',      nameEn: 'Forest',   colors: ['#030d06','#10b981'] },
  { id: 'rose',     nameRu: 'Алый',     nameEn: 'Rose',     colors: ['#0d0609','#e11d48'] },
  { id: 'light',    nameRu: 'Светлая',  nameEn: 'Light',    colors: ['#f0f0f8','#7c3aed'] },
];

function applyTheme(id) {
  document.documentElement.dataset.theme = id === 'dark' ? '' : id;
  state.theme = id;
  try { localStorage.setItem('fff_theme', id); } catch {}
  renderThemeGrid();
}

function renderThemeGrid() {
  const grid = $('#theme-grid');
  if (!grid) return;
  grid.innerHTML = '';
  THEMES.forEach(th => {
    const btn = document.createElement('button');
    btn.className = 'theme-swatch' + (state.theme === th.id ? ' active' : '');
    btn.title = state.lang === 'en' ? th.nameEn : th.nameRu;
    btn.innerHTML = `
      <div class="theme-color" style="background:linear-gradient(135deg,${th.colors[0]} 0%,${th.colors[1]} 100%)"></div>
      <div class="theme-name">${state.lang === 'en' ? th.nameEn : th.nameRu}</div>`;
    btn.addEventListener('click', () => applyTheme(th.id));
    grid.appendChild(btn);
  });
}

/* ══════════════════════════════════════════════
   SETTINGS PANEL
══════════════════════════════════════════════ */
function openSettings() {
  const profile = state.profile;
  const user    = state.user;
  const name    = profile?.display_name || profile?.email_username || '?';

  $('#settings-avatar').textContent = name[0]?.toUpperCase() || '?';
  $('#settings-display-name').textContent = name;
  $('#settings-email-label').textContent  = user?.email || '';

  hide($('#settings-name-form'));
  renderThemeGrid();
  applyLang();

  /* Highlight active lang */
  $$('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === state.lang));

  /* Sync hints toggle */
  const hintsOn = document.documentElement.classList.contains('show-hints');
  $('#hints-toggle')?.classList.toggle('on', hintsOn);

  /* "Вход с браузера" — для всех TG пользователей (merged или нет) */
  const tgSection = $('#settings-tg-browser');
  if (tgSection) {
    if (IS_TG) {
      show(tgSection);
      $('#tg-browser-email').textContent = user?.email || '—';
    } else {
      hide(tgSection);
    }
  }

  /* "Объединить аккаунты" — только для нативных tg_ аккаунтов (не смерженных) */
  const mergeSection = $('#settings-tg-merge');
  if (mergeSection) {
    if (IS_TG && user?.email?.startsWith('tg_')) {
      show(mergeSection);
    } else {
      hide(mergeSection);
    }
  }

  /* В TG Mini App выйти невозможно — аккаунт привязан к Telegram */
  const logoutSection = $('.settings-section-danger');
  if (logoutSection) IS_TG ? hide(logoutSection) : show(logoutSection);

  show($('#settings-panel'));
  document.body.classList.add('modal-open');
}

function closeSettings() {
  hide($('#settings-panel'));
  document.body.classList.remove('modal-open');
}

/* ══════════════════════════════════════════════
   RECOMMENDATIONS & SHARING
══════════════════════════════════════════════ */

function getMovieShareUrl(movieId) {
  return `${location.origin}${location.pathname}?movie=${movieId}`;
}

function openShareSheet(movie) {
  if (!movie) return;
  state.sharingMovie = movie;
  const nameEl = $('#share-movie-name');
  if (nameEl) nameEl.textContent = `«${movie.name}»`;
  /* Show native share button only if API available */
  toggle($('#share-native-btn'), !!navigator.share);
  show($('#share-sheet'));
}

function closeShareSheet() {
  hide($('#share-sheet'));
}

async function openSharedMovie(movieId) {
  /* Load and show movie in modal when opened via ?movie=ID */
  const [{ data: movie }, { data: posters }] = await Promise.all([
    sb.from('movies').select('id,name,slogan,description,year,age_rating,duration_minutes,kp_type').eq('id', movieId).single(),
    sb.from('posters').select('preview_url').eq('movie_id', movieId).limit(1),
  ]);
  if (!movie) return;
  const posterUrl = posters?.[0]?.preview_url || '';
  openMovieModal(movie, posterUrl, false);
}

async function openFriendPicker() {
  const list  = $('#picker-list');
  const empty = $('#picker-empty');
  list.innerHTML = '';
  hide(empty);
  show($('#friend-picker'));

  const uid = state.user.id;
  const { data: rows } = await sb.from('friends')
    .select('user_one,user_two')
    .or(`user_one.eq.${uid},user_two.eq.${uid}`)
    .eq('status', 1);

  if (!rows || rows.length === 0) { show(empty); return; }

  const friendIds = rows.map(f => f.user_one === uid ? f.user_two : f.user_one);
  const { data: profiles } = await sb.from('profiles')
    .select('id,display_name,email_username')
    .in('id', friendIds);

  if (!profiles || profiles.length === 0) { show(empty); return; }

  profiles.forEach(p => {
    const name = p.display_name || p.email_username || 'Друг';
    const btn = document.createElement('button');
    btn.className = 'picker-friend-item';
    btn.innerHTML = `
      <div class="friend-avatar">${escHtml(name[0]?.toUpperCase() || '?')}</div>
      <div class="friend-name">${escHtml(name)}</div>
      <svg class="picker-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
      </svg>`;
    btn.addEventListener('click', () => sendRecommendation(p.id, name));
    list.appendChild(btn);
  });
}

async function sendRecommendation(toUserId, toUserName) {
  const movie = state.sharingMovie;
  hide($('#friend-picker'));
  if (!movie) return;

  const { error } = await sb.from('recommendations').upsert(
    { from_user: state.user.id, to_user: toUserId, movie_id: movie.id, seen: false },
    { onConflict: 'from_user,to_user,movie_id', ignoreDuplicates: true }
  );

  state.sharingMovie = null;
  if (error) { showToast('Ошибка: ' + error.message, 4000); return; }
  showToast(`Рекомендовано ${toUserName} 🎬`);
}

async function loadRecommendations() {
  const uid = state.user.id;

  const { data: recs } = await sb.from('recommendations')
    .select('id,from_user,movie_id,seen')
    .eq('to_user', uid)
    .eq('seen', false)
    .order('created_at', { ascending: false })
    .limit(20);

  const section = $('#rec-section');
  const grid    = $('#rec-grid');
  if (!recs || recs.length === 0) { hide(section); updateRecBadge(0); return; }

  const unread = recs.filter(r => !r.seen).length;
  updateRecBadge(unread);

  /* Load movie data */
  const movieIds   = [...new Set(recs.map(r => r.movie_id))];
  const fromIds    = [...new Set(recs.map(r => r.from_user))];

  const [{ data: movies }, { data: posters }, { data: senders }] = await Promise.all([
    sb.from('movies').select('id,name,year').in('id', movieIds),
    sb.from('posters').select('movie_id,preview_url').in('movie_id', movieIds),
    sb.from('profiles').select('id,display_name,email_username').in('id', fromIds),
  ]);

  const movieMap  = Object.fromEntries((movies  || []).map(m => [m.id, m]));
  const posterMap = Object.fromEntries((posters || []).map(p => [p.movie_id, p.preview_url]));
  const senderMap = Object.fromEntries((senders || []).map(s => [s.id, s.display_name || s.email_username || 'Друг']));

  grid.innerHTML = '';
  recs.forEach(rec => {
    const m = movieMap[rec.movie_id];
    if (!m) return;
    const poster = posterMap[rec.movie_id];
    const sender = senderMap[rec.from_user] || 'Друг';
    const el = createRecItem(m, poster, sender, rec.seen);
    el.addEventListener('click', () => {
      openMovieModal(m, poster || '', false, rec.id);
    });
    grid.appendChild(el);
  });

  show(section);

  /* Badge cleared only when user rates a recommended movie */
}

function createRecItem(movie, posterUrl, senderName, seen) {
  const el = document.createElement('div');
  el.className = 'rec-item' + (seen ? ' rec-seen' : '');
  const safeUrl = posterUrl ? safeImgUrl(posterUrl) : '';
  el.innerHTML = `
    ${safeUrl
      ? `<img class="rec-poster" src="${safeUrl}" alt="${escHtml(movie.name)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'">`
      : `<div class="rec-poster rec-poster-empty">🎬</div>`}
    <div class="rec-info">
      <div class="rec-title">${escHtml(movie.name)}</div>
      <div class="rec-from">от ${escHtml(senderName)}</div>
    </div>
    ${!seen ? '<div class="rec-dot"></div>' : ''}`;
  return el;
}

function updateRecBadge(count) {
  const badge = $('#rec-badge');
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count > 9 ? '9+' : count;
    show(badge);
  } else {
    hide(badge);
  }
}

async function handleLogin() {
  const email = $('#login-email').value.trim();
  const pass  = $('#login-password').value;
  if (!email || !pass) return showAuthMsg('Заполните все поля', 'error');

  showAuthMsg('Входим...', '');
  const { error } = await sb.auth.signInWithPassword({ email, password: pass });
  if (error) showAuthMsg(error.message, 'error');
}

async function handleRegister() {
  const email  = $('#reg-email').value.trim();
  const pass   = $('#reg-password').value;
  const birth  = $('#reg-birthdate').value;

  if (!email || !pass || !birth) return showAuthMsg('Заполните все поля', 'error');
  if (pass.length < 6)           return showAuthMsg('Пароль минимум 6 символов', 'error');

  showAuthMsg('Создаём аккаунт...', '');
  const { data, error } = await sb.auth.signUp({
    email, password: pass,
    options: { data: { birth_date: birth } }
  });
  if (error) return showAuthMsg(error.message, 'error');

  /* Insert profile with birth_date */
  if (data.user) {
    await sb.from('profiles').upsert({ id: data.user.id, birth_date: birth });
  }

  showAuthMsg('Аккаунт создан! Проверьте почту для подтверждения.', 'success');
}

function showAuthMsg(text, type) {
  const el = $('#auth-msg');
  el.textContent = text;
  el.className = 'auth-msg' + (type ? ` ${type}` : '');
  show(el);
}

function showAuthForm(name) {
  ['login-form', 'register-form', 'forgot-form', 'newpass-form']
    .forEach(id => hide($(`#${id}`)));
  show($(`#${name}-form`));
  hide($('#auth-msg'));
}

function showScreen(name) {
  hide($('#auth-screen'));
  hide($('#app-screen'));
  if (name === 'auth') show($('#auth-screen'));
  if (name === 'app')  show($('#app-screen'));
}

async function handleForgotPassword() {
  const email = $('#forgot-email').value.trim();
  if (!email) return showAuthMsg('Введите email', 'error');
  showAuthMsg('Отправляем...', '');
  const { error } = await sb.auth.resetPasswordForEmail(email, {
    redirectTo: `${location.origin}${location.pathname}`,
  });
  if (error) return showAuthMsg(error.message, 'error');
  showAuthMsg('Ссылка отправлена! Проверьте почту.', 'success');
}

async function handleNewPassword() {
  const pass    = $('#newpass-password').value;
  const confirm = $('#newpass-confirm').value;
  if (!pass || !confirm) return showAuthMsg('Заполните все поля', 'error');
  if (pass.length < 6)   return showAuthMsg('Пароль минимум 6 символов', 'error');
  if (pass !== confirm)  return showAuthMsg('Пароли не совпадают', 'error');
  showAuthMsg('Сохраняем...', '');
  const { error } = await sb.auth.updateUser({ password: pass });
  if (error) return showAuthMsg(error.message, 'error');
  showAuthMsg('Пароль изменён! Войдите с новым паролем.', 'success');
  await sb.auth.signOut();
  setTimeout(() => showAuthForm('login'), 2000);
}

/* ══════════════════════════════════════════════
   NAVIGATION
══════════════════════════════════════════════ */
const App = {
  navigate(page) {
    $$('.page').forEach(p => p.classList.remove('active'));
    $$('.nav-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.page === page);
    });
    const el = $(`#page-${page}`);
    if (el) el.classList.add('active');

    if (page === 'watchlist') App.loadWatchlist();
    if (page === 'friends')   App.loadFriends();
    if (page === 'browse' && !state.currentMovie) App.loadNextMovie();
  },

  /* ─── BROWSE ─── */
  async loadNextMovie() {
    hide($('#browse-main'));
    hide($('#browse-empty'));
    show($('#browse-loading'));

    try {
      let movie = null;

      /* Try the RPC function first */
      const rpcParams = { p_user_id: state.user.id };
      if (state.selectedGenres.length > 0) rpcParams.p_genre_ids         = state.selectedGenres;
      if (state.excludeGenres.length  > 0) rpcParams.p_exclude_genre_ids = state.excludeGenres;
      const { data: rpcData, error: rpcError } = await sb.rpc('get_next_movie', rpcParams);

      if (!rpcError && rpcData && rpcData.length > 0) {
        movie = rpcData[0];
      } else {
        /* RPC failed — log and use direct query as fallback */
        if (rpcError) console.error('[FFF] RPC get_next_movie error:', rpcError.message, rpcError);

        const { data: rated } = await sb
          .from('actions')
          .select('movie_id')
          .eq('user_id', state.user.id);

        const ratedIds = (rated || []).map(r => r.movie_id);

        let q = sb
          .from('movies')
          .select('id, name, slogan, description, year, age_rating, priority, posters(preview_url)')
          .order('priority', { ascending: false })
          .limit(50);

        if (ratedIds.length > 0) {
          q = q.not('id', 'in', `(${ratedIds.join(',')})`);
        }

        const { data: movies, error: mErr } = await q;
        if (mErr) console.error('[FFF] Movies fallback error:', mErr.message);

        if (movies && movies.length > 0) {
          const withPoster = movies.filter(m => m.posters?.[0]?.preview_url);
          if (withPoster.length > 0) {
            const m = withPoster[Math.floor(Math.random() * withPoster.length)];
            movie = { ...m, preview_url: m.posters[0].preview_url };
          }
        }
      }

      hide($('#browse-loading'));

      if (!movie) {
        show($('#browse-empty'));
        return;
      }

      state.currentMovie = movie;
      renderMovieCard(movie);
      show($('#browse-main'));
    } catch (e) {
      console.error('[FFF] loadNextMovie exception:', e);
      hide($('#browse-loading'));
      show($('#browse-empty'));
    }
  },

  async rateMovie(liked) {
    if (!state.currentMovie) return;
    const movie = state.currentMovie;
    const card  = $('#movie-card');

    TG?.HapticFeedback?.impactOccurred(liked ? 'medium' : 'light');
    card.classList.add(liked ? 'swipe-out-right' : 'swipe-out-left');
    state.lastAction  = { movie, type: liked ? 'like' : 'dislike' };
    state.currentMovie = null;
    showUndo();

    await sb.from('actions').upsert({
      user_id: state.user.id, movie_id: movie.id,
      want_to_watch: liked, watched: false,
    }, { onConflict: 'user_id,movie_id' });

    setTimeout(() => {
      card.classList.remove('swipe-out-right', 'swipe-out-left');
      App.loadNextMovie();
    }, 380);
  },

  async markWatched() {
    if (!state.currentMovie) return;
    const movie = state.currentMovie;
    const card  = $('#movie-card');

    TG?.HapticFeedback?.notificationOccurred('success');
    card.classList.add('swipe-out-up');
    state.lastAction  = { movie, type: 'watched' };
    state.currentMovie = null;
    showUndo();

    await sb.from('actions').upsert({
      user_id: state.user.id, movie_id: movie.id,
      want_to_watch: false, watched: true,
    }, { onConflict: 'user_id,movie_id' });

    setTimeout(() => {
      card.classList.remove('swipe-out-up');
      App.loadNextMovie();
    }, 380);
  },

  /* ─── WATCHLIST ─── */
  async loadWatchlist() {
    const grid = $('#watchlist-grid');
    const empty = $('#watchlist-empty');
    const loading = $('#watchlist-loading');
    grid.innerHTML = '';
    hide(empty);
    show(loading);

    /* Step 1: liked movie IDs */
    const { data: actions, error: aErr } = await sb
      .from('actions')
      .select('movie_id')
      .eq('user_id', state.user.id)
      .eq('want_to_watch', true)
      .order('id', { ascending: false });

    if (aErr) { console.error('[FFF] watchlist:', aErr.message); showToast('Ошибка списка: ' + aErr.message, 4000); }
    if (aErr || !actions || actions.length === 0) { hide(loading); show(empty); return; }

    const ids = actions.map(a => a.movie_id);

    /* Step 2: movie details */
    const { data: movies, error: mErr } = await sb
      .from('movies')
      .select('id, name, year, age_rating, description, slogan')
      .in('id', ids);

    if (mErr) console.error('[FFF] watchlist movies error:', mErr.message);

    /* Step 3: posters (separate query — no ambiguous FK) */
    const { data: posters } = await sb
      .from('posters')
      .select('movie_id, preview_url')
      .in('movie_id', ids);

    hide(loading);

    if (!movies || movies.length === 0) { show(empty); return; }

    const movieMap  = Object.fromEntries((movies  || []).map(m => [m.id, m]));
    const posterMap = Object.fromEntries((posters || []).map(p => [p.movie_id, p.preview_url]));

    let rendered = 0;
    ids.forEach(id => {
      const m = movieMap[id];
      if (!m) return;
      const poster = posterMap[id];
      if (!poster) return; /* skip movies with no poster */
      rendered++;
      const el = createMovieMini(m, poster);
      el.addEventListener('click', () => openMovieModal(m, poster, true));
      grid.appendChild(el);
    });
    if (rendered === 0) show(empty);
  },

  /* ─── FRIENDS ─── */
  async loadFriends() {
    const list = $('#friends-list');
    const empty = $('#friends-empty');
    const loading = $('#friends-loading');
    list.innerHTML = '';
    hide(empty);
    hide($('#common-panel'));
    show(loading);
    loadRecommendations();

    const uid = state.user.id;

    /* Step 1: my friendships */
    const { data: rows, error } = await sb
      .from('friends')
      .select('user_one, user_two')
      .or(`user_one.eq.${uid},user_two.eq.${uid}`)
      .eq('status', 1);

    if (error) { console.error('[FFF] friends:', error.message); showToast('Ошибка друзей: ' + error.message, 4000); }
    if (error || !rows || rows.length === 0) { hide(loading); show(empty); return; }

    /* Step 2: friend profile IDs */
    const friendIds = rows.map(f => f.user_one === uid ? f.user_two : f.user_one);

    const { data: profiles, error: pErr } = await sb
      .from('profiles')
      .select('id, display_name, email_username')
      .in('id', friendIds);

    if (pErr) console.error('[FFF] friends profiles error:', pErr.message);

    hide(loading);

    if (!profiles || profiles.length === 0) { show(empty); return; }

    profiles.forEach(p => {
      const item = createFriendItem(p);
      list.appendChild(item);
    });
  },

  async loadCommonMovies(friendId, friendName) {
    state.currentFriend = { id: friendId, name: friendName };
    const panel   = $('#common-panel');
    const grid    = $('#common-grid');
    const empty   = $('#common-empty');
    const loading = $('#common-loading');
    $('#common-friend-name').textContent = friendName;
    grid.innerHTML = '';
    hide(empty);
    show(loading);
    show(panel);

    /* Switch active tab */
    $$('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === 'common'));

    const uid = state.user.id;

    const [{ data: mine }, { data: theirs }] = await Promise.all([
      sb.from('actions').select('movie_id').eq('user_id', uid).eq('want_to_watch', true),
      sb.from('actions').select('movie_id').eq('user_id', friendId).eq('want_to_watch', true),
    ]);

    const mySet     = new Set((mine   || []).map(a => a.movie_id));
    const theirSet  = new Set((theirs || []).map(a => a.movie_id));
    const commonIds = [...mySet].filter(id => theirSet.has(id));

    if (commonIds.length === 0) {
      hide(loading);
      $('#common-empty-text').textContent = 'Нет общих фильмов';
      $('#common-empty-sub').textContent  = 'Оценивайте больше фильмов — появятся совпадения!';
      show(empty);
      return;
    }

    const [{ data: movies }, { data: posters }] = await Promise.all([
      sb.from('movies').select('id, name, year, description, slogan, age_rating, kp_type').in('id', commonIds),
      sb.from('posters').select('movie_id, preview_url').in('movie_id', commonIds),
    ]);

    hide(loading);

    const posterMap = Object.fromEntries((posters || []).map(p => [p.movie_id, p.preview_url]));
    (movies || []).forEach(m => {
      if (!posterMap[m.id]) return;
      const el = createMovieMini(m, posterMap[m.id]);
      el.addEventListener('click', () => openMovieModal(m, posterMap[m.id], false));
      grid.appendChild(el);
    });
  },

  async loadFriendWatchlist(friendId, friendName) {
    state.currentFriend = { id: friendId, name: friendName };
    const grid    = $('#common-grid');
    const empty   = $('#common-empty');
    const loading = $('#common-loading');
    grid.innerHTML = '';
    hide(empty);
    show(loading);

    /* Switch active tab */
    $$('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === 'friend'));

    const { data: actions } = await sb
      .from('actions')
      .select('movie_id')
      .eq('user_id', friendId)
      .eq('want_to_watch', true)
      .order('id', { ascending: false });

    if (!actions || actions.length === 0) {
      hide(loading);
      $('#common-empty-text').textContent = 'Пустой список';
      $('#common-empty-sub').textContent  = `${friendName} ещё ничего не лайкнул`;
      show(empty);
      return;
    }

    const ids = actions.map(a => a.movie_id);
    const [{ data: movies }, { data: posters }] = await Promise.all([
      sb.from('movies').select('id, name, year, description, slogan, age_rating, kp_type').in('id', ids),
      sb.from('posters').select('movie_id, preview_url').in('movie_id', ids),
    ]);

    hide(loading);

    const posterMap = Object.fromEntries((posters || []).map(p => [p.movie_id, p.preview_url]));
    const movieMap  = Object.fromEntries((movies  || []).map(m => [m.id, m]));

    let rendered = 0;
    ids.forEach(id => {
      const m = movieMap[id];
      if (!m || !posterMap[id]) return;
      rendered++;
      const el = createMovieMini(m, posterMap[id]);
      el.addEventListener('click', () => openMovieModal(m, posterMap[id], false));
      grid.appendChild(el);
    });

    if (rendered === 0) {
      $('#common-empty-text').textContent = 'Нет фильмов с постерами';
      $('#common-empty-sub').textContent  = `Постеры ещё загружаются`;
      show(empty);
    }
  },
};

/* ══════════════════════════════════════════════
   FRIEND INVITE FLOW
══════════════════════════════════════════════ */
async function showFriendBanner(friendId) {
  /* Get friend's name */
  const { data: profile } = await sb
    .from('profiles')
    .select('display_name, email_username')
    .eq('id', friendId)
    .single();

  const name = profile?.display_name || profile?.email_username || 'пользователь';
  $('#friend-banner-text').textContent = `Добавить ${name} в друзья?`;
  show($('#friend-banner'));
  state.pendingFriend = friendId;
}

async function addFriend(friendId) {
  const uid = state.user.id;
  const { error } = await sb.from('friends').upsert(
    { user_one: uid, user_two: friendId, status: 1 },
    { onConflict: 'user_one,user_two' }
  );
  hide($('#friend-banner'));
  state.pendingFriend = null;
  try { sessionStorage.removeItem('fff_invite'); } catch {}
  if (error) {
    console.error('[FFF] addFriend error:', error);
    showToast('Ошибка: ' + error.message, 5000);
    return;
  }
  showToast('Друг добавлен! 👥');
  history.replaceState({}, '', location.pathname);
  App.navigate('friends');
}

/* ══════════════════════════════════════════════
   MOVIE CARD RENDERING
══════════════════════════════════════════════ */
function renderMovieCard(movie) {
  const card = $('#movie-card');
  card.classList.remove('swipe-out-right', 'swipe-out-left', 'swiping-right', 'swiping-left');

  /* Poster */
  const posterEl = $('#card-poster');
  if (movie.preview_url) {
    posterEl.src = safeImgUrl(movie.preview_url);
    posterEl.style.display = 'block';
    posterEl.onerror = () => { posterEl.style.display = 'none'; };
  } else {
    posterEl.src = '';
    posterEl.style.display = 'none';
  }

  $('#card-year').textContent     = movie.year || '';
  $('#card-age').textContent      = movie.age_rating ? `${movie.age_rating}+` : '';
  $('#card-title').textContent    = movie.name || '';
  $('#card-tagline').textContent  = movie.slogan || '';
  $('#card-desc').textContent     = movie.description || '';

  toggle($('#card-age'), !!movie.age_rating);
  toggle($('#card-tagline'), !!movie.slogan);

  card.classList.add('card-enter');
  card.addEventListener('animationend', () => card.classList.remove('card-enter'), { once: true });
}

function createMovieMini(movie, posterUrl) {
  const el = document.createElement('div');
  el.className = 'movie-mini';

  const safeUrl = posterUrl ? safeImgUrl(posterUrl) : '';
  if (safeUrl) {
    el.innerHTML = `
      <img class="movie-mini-poster" src="${safeUrl}" alt="${escHtml(movie.name)}"
           loading="lazy" referrerpolicy="no-referrer"
           onerror="this.outerHTML='<div class=movie-mini-poster-placeholder>🎬</div>'">
      <div class="movie-mini-info">
        <div class="movie-mini-title">${escHtml(movie.name)}</div>
        <div class="movie-mini-year">${movie.year || ''}</div>
      </div>`;
  } else {
    el.innerHTML = `
      <div class="movie-mini-poster-placeholder">🎬</div>
      <div class="movie-mini-info">
        <div class="movie-mini-title">${escHtml(movie.name)}</div>
        <div class="movie-mini-year">${movie.year || ''}</div>
      </div>`;
  }
  return el;
}

function createFriendItem(profile) {
  const name = profile.display_name || profile.email_username || 'Друг';
  const initial = name[0]?.toUpperCase() || '?';
  const el = document.createElement('div');
  el.className = 'friend-item';
  el.innerHTML = `
    <div class="friend-avatar">${initial}</div>
    <div class="friend-info">
      <div class="friend-name">${escHtml(name)}</div>
      <div class="friend-sub">Общие фильмы и список</div>
    </div>
    <span class="friend-arrow">›</span>`;
  el.addEventListener('click', () => App.loadCommonMovies(profile.id, name));
  return el;
}

/* ══════════════════════════════════════════════
   MOVIE MODAL
══════════════════════════════════════════════ */
async function openMovieModal(movie, posterUrl, showRemove, recId = null) {
  const modalImg = $('#modal-poster');
  modalImg.src = posterUrl ? safeImgUrl(posterUrl) : '';
  modalImg.onerror = () => hide(modalImg);
  toggle(modalImg, !!posterUrl);

  $('#modal-year').textContent     = movie.year || '';
  $('#modal-age').textContent      = movie.age_rating ? `${movie.age_rating}+` : '';
  $('#modal-title').textContent    = movie.name || '';
  $('#modal-tagline').textContent  = movie.slogan || '';
  $('#modal-desc').textContent     = movie.description || '';

  toggle($('#modal-age'),     !!movie.age_rating);
  toggle($('#modal-tagline'), !!movie.slogan);
  toggle($('#modal-remove-btn'), showRemove);

  /* Rate row — shown only when opened from a recommendation */
  const rateRow = $('#modal-rate-row');
  toggle(rateRow, recId !== null);
  if (recId !== null) {
    const doRate = async (wantToWatch, watched) => {
      await sb.from('actions').upsert(
        { user_id: state.user.id, movie_id: movie.id, want_to_watch: wantToWatch, watched },
        { onConflict: 'user_id,movie_id' }
      );
      await sb.from('recommendations').update({ seen: true }).eq('id', recId);
      closeModal();
      loadRecommendations();
    };
    $('#modal-rate-like').onclick    = () => doRate(true,  false);
    $('#modal-rate-watched').onclick  = () => doRate(false, true);
    $('#modal-rate-dislike').onclick  = () => doRate(false, false);
  }

  /* Duration */
  const durEl = $('#modal-duration');
  hide(durEl);

  /* Where to watch */
  const watchSection = $('#modal-watch');
  const watchLinks   = $('#modal-watch-links');
  watchLinks.innerHTML = '';

  /* kinokino.vip — free streaming, opens in inline player */
  const kpPath = (movie.kp_type === 'tv-series' || movie.kp_type === 'animated-series')
    ? 'series' : 'film';
  const kkUrl  = `https://www.kinokino.vip/${kpPath}/${movie.id}/`;
  const kkBtn  = document.createElement('button');
  kkBtn.className = 'watch-link-btn watch-link-free';
  kkBtn.innerHTML = '<span class="watch-link-icon">▶</span> Смотреть бесплатно';
  kkBtn.addEventListener('click', () => openPlayer(kkUrl, movie.name));
  watchLinks.appendChild(kkBtn);

  const { data: links } = await sb
    .from('watchability')
    .select('service_name, link')
    .eq('movie_id', movie.id);

  if (links && links.length > 0) {
    links.forEach(({ service_name, link }) => {
      const a = document.createElement('a');
      a.className = 'watch-link-btn';
      a.href = link;
      a.target = '_blank';
      a.rel = 'noopener';
      a.innerHTML = `<span class="watch-link-icon">▶</span> ${escHtml(service_name)}`;
      watchLinks.appendChild(a);
    });
  }
  show(watchSection);

  /* Share button handler */
  const shareBtn = $('#modal-share-btn');
  if (shareBtn) shareBtn.onclick = () => openShareSheet(movie);

  /* Remove button handler */
  const removeBtn = $('#modal-remove-btn');
  removeBtn.onclick = async () => {
    await sb.from('actions')
      .update({ want_to_watch: false })
      .eq('user_id', state.user.id)
      .eq('movie_id', movie.id);
    closeModal();
    App.loadWatchlist();
    showToast('Убрано из списка');
  };

  show($('#movie-modal'));
  document.body.classList.add('modal-open');
}

function closeModal() {
  hide($('#movie-modal'));
  document.body.classList.remove('modal-open');
}

/* ══════════════════════════════════════════════
   INLINE PLAYER
══════════════════════════════════════════════ */
function openPlayer(url, title = '') {
  if (IS_TG) {
    /* Telegram Mini App — open in Telegram's built-in browser */
    TG.openLink(url);
    return;
  }
  /* Web browser — inline iframe player */
  $('#player-iframe').src = url;
  $('#player-title').textContent = title;
  show($('#player-modal'));
}

function closePlayer() {
  hide($('#player-modal'));
  $('#player-iframe').src = '';
  TG?.exitFullscreen?.();
}

/* ══════════════════════════════════════════════
   SWIPE GESTURE
══════════════════════════════════════════════ */
(function initSwipe() {
  const card = () => $('#movie-card');
  let startX = 0, startY = 0, currentX = 0, currentY = 0, dragging = false;

  function onStart(x, y) {
    if (!state.currentMovie) return;
    startX = x; startY = y; currentX = 0; currentY = 0; dragging = true;
  }
  function onMove(x, y) {
    if (!dragging) return;
    currentX = x - startX;
    currentY = y - startY;
    const absX = Math.abs(currentX), absY = Math.abs(currentY);
    /* Shrink actions while dragging */
    if (absX > 10 || absY > 10) document.body.classList.add('card-dragging');

    if (currentY < -20 && absY > absX) {
      /* Swipe up — "уже смотрел" */
      card().style.transform = `translateY(${currentY}px)`;
      card().classList.add('swiping-up');
      card().classList.remove('swiping-right', 'swiping-left', 'swiping-down');
    } else if (currentY > 20 && absY > absX) {
      /* Swipe down — share */
      card().style.transform = `translateY(${Math.min(currentY * 0.35, 36)}px)`;
      card().classList.add('swiping-down');
      card().classList.remove('swiping-right', 'swiping-left', 'swiping-up');
    } else if (absX > absY) {
      /* Horizontal swipe */
      const rotate = currentX / 18;
      card().style.transform = `translateX(${currentX}px) rotate(${rotate}deg)`;
      card().classList.toggle('swiping-right', currentX > 30);
      card().classList.toggle('swiping-left',  currentX < -30);
      card().classList.remove('swiping-up', 'swiping-down');
    }
  }
  function onEnd() {
    if (!dragging) return;
    dragging = false;
    card().style.transform = '';
    card().classList.remove('swiping-right', 'swiping-left', 'swiping-up', 'swiping-down');
    document.body.classList.remove('card-dragging');
    if      (currentX > 80)                               App.rateMovie(true);
    else if (currentX < -80)                              App.rateMovie(false);
    else if (currentY < -80)                              App.markWatched();
    else if (currentY > 80 && Math.abs(currentY) > Math.abs(currentX)) openShareSheet(state.currentMovie);
  }

  document.addEventListener('touchstart', e => {
    if (!e.target.closest('#movie-card')) return;
    onStart(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  document.addEventListener('touchmove', e => {
    if (!dragging) return;
    onMove(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  document.addEventListener('touchend', onEnd);

  document.addEventListener('mousedown', e => {
    if (!e.target.closest('#movie-card')) return;
    onStart(e.clientX, e.clientY);
  });
  document.addEventListener('mousemove', e => { if (dragging) onMove(e.clientX, e.clientY); });
  document.addEventListener('mouseup', onEnd);
})();

/* ══════════════════════════════════════════════
   GENRE PILLS DRAG-TO-SCROLL (mouse)
══════════════════════════════════════════════ */
(function initPillsDrag() {
  document.addEventListener('DOMContentLoaded', () => {
    const el = $('#genre-pills');
    if (!el) return;
    let isDown = false, startX = 0, scrollLeft = 0;
    el.addEventListener('mousedown', e => {
      isDown = true;
      startX = e.pageX - el.offsetLeft;
      scrollLeft = el.scrollLeft;
      el.style.userSelect = 'none';
    });
    document.addEventListener('mouseup',   () => { isDown = false; el.style.userSelect = ''; });
    document.addEventListener('mousemove', e => {
      if (!isDown) return;
      e.preventDefault();
      el.scrollLeft = scrollLeft - (e.pageX - el.offsetLeft - startX);
    });
  });
})();

/* ══════════════════════════════════════════════
   EVENT LISTENERS
══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  /* Auth */
  $('#login-btn').addEventListener('click', handleLogin);
  $('#register-btn').addEventListener('click', handleRegister);
  $('#show-register').addEventListener('click', e => {
    e.preventDefault();
    hide($('#login-form'));
    show($('#register-form'));
    hide($('#auth-msg'));
  });
  $('#show-login').addEventListener('click', e => {
    e.preventDefault();
    hide($('#register-form'));
    show($('#login-form'));
    hide($('#auth-msg'));
  });

  /* Forgot / Reset password */
  $('#show-forgot').addEventListener('click',   e => { e.preventDefault(); showAuthForm('forgot'); });
  $('#show-login-2').addEventListener('click',  e => { e.preventDefault(); showAuthForm('login'); });
  $('#forgot-btn').addEventListener('click',    handleForgotPassword);
  $('#newpass-btn').addEventListener('click',   handleNewPassword);
  $('#forgot-email').addEventListener('keydown', e => { if (e.key === 'Enter') handleForgotPassword(); });
  $('#newpass-confirm').addEventListener('keydown', e => { if (e.key === 'Enter') handleNewPassword(); });

  /* Enter key in forms */
  $('#login-password').addEventListener('keydown', e => { if (e.key === 'Enter') handleLogin(); });
  $('#reg-birthdate').addEventListener('keydown',  e => { if (e.key === 'Enter') handleRegister(); });

  /* Logout */
  $('#logout-btn').addEventListener('click', async () => {
    await sb.auth.signOut();
    state.user = null;
    state.profile = null;
    state.currentMovie = null;
  });

  /* Navigation */
  $$('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => App.navigate(btn.dataset.page));
  });

  /* Rate buttons */
  $('#like-btn').addEventListener('click',     () => App.rateMovie(true));
  $('#dislike-btn').addEventListener('click',  () => App.rateMovie(false));
  $('#watched-btn').addEventListener('click',  () => App.markWatched());

  /* Modal */
  $('#modal-close').addEventListener('click', closeModal);
  $('#modal-overlay').addEventListener('click', closeModal);

  /* Copy invite link */
  $('#copy-btn').addEventListener('click', () => {
    const link = $('#invite-link').textContent;
    navigator.clipboard.writeText(link).then(() => showToast('Ссылка скопирована! 🔗'));
  });

  /* Friend banner */
  $('#friend-add-btn').addEventListener('click', () => {
    if (state.pendingFriend) addFriend(state.pendingFriend);
  });
  $('#friend-skip-btn').addEventListener('click', () => {
    hide($('#friend-banner'));
    state.pendingFriend = null;
    try { sessionStorage.removeItem('fff_invite'); } catch {}
    history.replaceState({}, '', location.pathname);
  });

  /* Common movies back */
  $('#common-back').addEventListener('click', () => hide($('#common-panel')));

  /* Friend panel tabs */
  $$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!state.currentFriend) return;
      if (btn.dataset.tab === 'common') {
        App.loadCommonMovies(state.currentFriend.id, state.currentFriend.name);
      } else {
        App.loadFriendWatchlist(state.currentFriend.id, state.currentFriend.name);
      }
    });
  });

  /* Undo */
  $('#undo-btn')?.addEventListener('click', undoLastAction);

  /* Stats */
  $('#stats-btn')?.addEventListener('click', openStats);
  $('#stats-close')?.addEventListener('click', () => hide($('#stats-modal')));
  $('#stats-overlay')?.addEventListener('click', () => hide($('#stats-modal')));

  /* Onboarding */
  $('#onboarding-done')?.addEventListener('click', async () => {
    hide($('#onboarding'));
    const selected = $$('#onboarding-genres .onboarding-genre.active').map(b => parseInt(b.dataset.id));
    if (selected.length > 0) {
      state.selectedGenres = selected;
      renderGenrePills();
      state.currentMovie = null;
      App.loadNextMovie();
    }
  });

  /* Logo → settings panel */
  $('#logo-btn')?.addEventListener('click', openSettings);
  $('#settings-close')?.addEventListener('click', closeSettings);
  $('#settings-overlay')?.addEventListener('click', closeSettings);

  /* Sign out from settings */
  $('#settings-logout-btn')?.addEventListener('click', async () => {
    closeSettings();
    await sb.auth.signOut();
    state.user = null; state.profile = null; state.currentMovie = null;
  });

  /* Edit name */
  $('#settings-edit-name-btn')?.addEventListener('click', () => {
    const form = $('#settings-name-form');
    const isHidden = form.classList.contains('hidden');
    if (isHidden) {
      $('#settings-name-input').value = state.profile?.display_name || '';
      show(form);
      $('#settings-name-input').focus();
    } else {
      hide(form);
    }
  });
  $('#settings-name-cancel')?.addEventListener('click', () => hide($('#settings-name-form')));
  $('#settings-name-save')?.addEventListener('click', async () => {
    const name = $('#settings-name-input').value.trim();
    if (!name) return;
    const { error } = await sb.from('profiles')
      .update({ display_name: name })
      .eq('id', state.user.id);
    if (error) { showToast('Ошибка: ' + error.message); return; }
    state.profile.display_name = name;
    $('#settings-display-name').textContent = name;
    $('#settings-avatar').textContent = name[0]?.toUpperCase() || '?';
    hide($('#settings-name-form'));
    showToast('Имя сохранено ✓');
  });
  $('#settings-name-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') $('#settings-name-save').click();
    if (e.key === 'Escape') hide($('#settings-name-form'));
  });

  /* Language buttons */
  $$('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.lang = btn.dataset.lang;
      try { localStorage.setItem('fff_lang', state.lang); } catch {}
      $$('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === state.lang));
      applyLang();
      renderThemeGrid(); // refresh theme names in selected language
    });
  });

  /* TG users — merge with browser account */
  $('#tg-merge-btn')?.addEventListener('click', async () => {
    const email = $('#tg-merge-email')?.value?.trim();
    const pass  = $('#tg-merge-pass')?.value?.trim();
    if (!email || !pass) { showToast('Введи email и пароль', 2500); return; }
    const btn = $('#tg-merge-btn');
    btn.disabled = true; btn.textContent = '...';
    await mergeAccounts(email, pass);
    btn.disabled = false; btn.textContent = 'Объединить';
  });

  /* TG users — set browser password */
  $('#tg-browser-save')?.addEventListener('click', async () => {
    const pass = $('#tg-browser-pass')?.value?.trim();
    if (!pass || pass.length < 6) { showToast('Минимум 6 символов', 2500); return; }
    const { error } = await sb.auth.updateUser({ password: pass });
    if (error) { showToast('Ошибка: ' + error.message, 3500); return; }
    showToast('Пароль сохранён! Теперь можешь войти с браузера', 3500);
    $('#tg-browser-pass').value = '';
  });

  /* Hints toggle in settings */
  $('#hints-toggle')?.addEventListener('click', () => {
    const nowOn = !document.documentElement.classList.contains('show-hints');
    document.documentElement.classList.toggle('show-hints', nowOn);
    $('#hints-toggle')?.classList.toggle('on', nowOn);
    try { localStorage.setItem('fff_hints', nowOn); } catch {}
  });

  /* Share sheet */
  $('#share-overlay')?.addEventListener('click', closeShareSheet);
  $('#share-friend-btn')?.addEventListener('click', () => {
    closeShareSheet();
    openFriendPicker();
  });
  $('#share-copy-btn')?.addEventListener('click', () => {
    if (!state.sharingMovie) return;
    const url = getMovieShareUrl(state.sharingMovie.id);
    navigator.clipboard.writeText(url)
      .then(() => { showToast('Ссылка скопирована 🔗'); closeShareSheet(); })
      .catch(() => { showToast(url); closeShareSheet(); });
  });
  $('#share-native-btn')?.addEventListener('click', async () => {
    const movie = state.sharingMovie;
    if (!movie) return;
    try {
      await navigator.share({
        title: movie.name,
        text: `Рекомендую фильм «${movie.name}»${movie.year ? ` (${movie.year})` : ''} 🎬`,
        url: getMovieShareUrl(movie.id),
      });
      closeShareSheet();
    } catch {}
  });

  /* Player */
  $('#player-close')?.addEventListener('click', closePlayer);

  /* Friend picker */
  $('#picker-close')?.addEventListener('click',   () => hide($('#friend-picker')));
  $('#picker-overlay')?.addEventListener('click', () => hide($('#friend-picker')));

  /* Watchlist search */
  $('#watchlist-search')?.addEventListener('input', e => {
    const q = e.target.value.trim().toLowerCase();
    $$('#watchlist-grid .movie-mini').forEach(el => {
      const title = el.querySelector('.movie-mini-title')?.textContent.toLowerCase() || '';
      el.style.display = (!q || title.includes(q)) ? '' : 'none';
    });
  });

  /* Keyboard shortcuts */
  document.addEventListener('keydown', e => {
    if ($('#page-browse').classList.contains('active')) {
      if (e.key === 'ArrowRight' || e.key === 'l') App.rateMovie(true);
      if (e.key === 'ArrowLeft'  || e.key === 'j') App.rateMovie(false);
      if (e.key === 'ArrowUp'    || e.key === 'k') App.markWatched();
      if (e.key === 'z' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); undoLastAction(); }
    }
    if (e.key === 'Escape') {
      closeModal();
      hide($('#stats-modal'));
    }
  });

  /* Apply language on start */
  applyLang();

  /* Boot */
  initAuth();

  /* Register service worker */
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }
});

/* ══════════════════════════════════════════════
   UTILS
══════════════════════════════════════════════ */
function escHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
