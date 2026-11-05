(() => {
  'use strict';

  const root = document.documentElement;
  const plate = document.getElementById('plate');
  const aperture = document.querySelector('.aperture');
  const reticle = document.getElementById('reticle');
  const readoutX = document.getElementById('rd-x');
  const readoutY = document.getElementById('rd-y');
  const readoutR = document.getElementById('rd-r');
  const fixLabel = document.getElementById('fix-label');
  const status = document.getElementById('selection-status');
  const work = document.getElementById('work');
  const pings = document.getElementById('pings');
  const themeButton = document.getElementById('theme');
  const themeValue = document.getElementById('theme-value');
  const metaTheme = document.querySelector('meta[name="theme-color"]');

  const rootStyle = plate ? plate.style : null;
  const THEME_KEY = 'field-report-theme';
  const DEFAULT_LABEL = 'Pointer fix';
  const PROJECTS = ['raiwall', 'document-verification-backend', 'code-compass-backend'];
  const PROJECT_NAMES = {
    raiwall: 'raiwall',
    'document-verification-backend': 'Document verification',
    'code-compass-backend': 'CodeCompass'
  };

  const reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  const fineQuery = window.matchMedia('(pointer: fine)');
  const schemeQuery = window.matchMedia('(prefers-color-scheme: dark)');

  let reduce = reduceQuery.matches;
  let fine = fineQuery.matches;
  let pointerX = window.innerWidth / 2;
  let pointerY = window.innerHeight / 2;
  let hasPointer = false;
  let frameRequested = 0;

  const nodes = Array.from(document.querySelectorAll('.node'));
  const entries = Array.from(document.querySelectorAll('.entry'));
  const details = Array.from(document.querySelectorAll('.detail'));

  function onMediaChange(query, handler) {
    if (typeof query.addEventListener === 'function') {
      query.addEventListener('change', handler);
    } else if (typeof query.addListener === 'function') {
      query.addListener(handler);
    }
  }

  function storedTheme() {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch (error) {
      return null;
    }
  }

  function padCoordinate(value) {
    return String(Math.max(0, Math.round(value))).padStart(4, '0');
  }

  /* ---------- theme ---------- */

  function setTheme(theme, persist) {
    const dark = theme === 'dark';
    root.dataset.theme = dark ? 'dark' : 'light';

    if (themeButton) {
      themeButton.setAttribute('aria-pressed', String(dark));
      themeButton.setAttribute(
        'aria-label',
        dark ? 'Theme Dark. Switch to light theme.' : 'Theme Light. Switch to dark theme.'
      );
    }
    if (themeValue) {
      themeValue.textContent = dark ? 'Dark' : 'Light';
    }
    if (metaTheme) {
      metaTheme.setAttribute('content', dark ? '#12161B' : '#E7E4DC');
    }
    if (persist) {
      try {
        localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light');
      } catch (error) {
        /* storage can be unavailable; the theme still changes for this visit */
      }
    }
  }

  setTheme(root.dataset.theme === 'dark' ? 'dark' : 'light', false);

  if (themeButton) {
    themeButton.addEventListener('click', () => {
      setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark', true);
    });
  }

  onMediaChange(schemeQuery, (event) => {
    if (!storedTheme()) {
      setTheme(event.matches ? 'dark' : 'light', false);
    }
  });

  /* ---------- pointer instrument ---------- */

  function renderPointer() {
    frameRequested = 0;
    let rect = aperture ? aperture.getBoundingClientRect() : null;

    // Before the first fix, rest the readout on the aperture's centre so the
    // idle instrument still describes its home position honestly.
    if (!hasPointer && rect) {
      pointerX = rect.left + rect.width / 2;
      pointerY = rect.top + rect.height / 2;
    }

    if (hasPointer && rootStyle && fine && !reduce) {
      const nx = (pointerX / window.innerWidth) * 2 - 1;
      const ny = (pointerY / window.innerHeight) * 2 - 1;
      rootStyle.setProperty('--mx', nx.toFixed(4));
      rootStyle.setProperty('--my', ny.toFixed(4));

      // Read the box again so the reticle lands on the layer after its
      // parallax translation, not one frame behind it.
      if (aperture) rect = aperture.getBoundingClientRect();
    }

    let localX = 0;
    let localY = 0;
    let radius = 0;

    if (rect) {
      const scale = rect.width / 440 || 1;
      const rawX = (pointerX - (rect.left + rect.width / 2)) / scale;
      const rawY = (pointerY - (rect.top + rect.height / 2)) / scale;
      const distance = Math.hypot(rawX, rawY);
      const limit = 178;

      radius = Math.min(1, distance / limit);
      localX = distance > limit ? (rawX / distance) * limit : rawX;
      localY = distance > limit ? (rawY / distance) * limit : rawY;
    }

    if (reticle) {
      reticle.setAttribute(
        'transform',
        `translate(${(220 + localX).toFixed(2)} ${(220 + localY).toFixed(2)})`
      );
      if (hasPointer) {
        reticle.style.opacity = '1';
      }
    }

    if (readoutX) readoutX.textContent = padCoordinate(pointerX);
    if (readoutY) readoutY.textContent = padCoordinate(pointerY);
    if (readoutR) readoutR.textContent = radius.toFixed(3);
  }

  function schedulePointer() {
    if (!frameRequested) {
      frameRequested = window.requestAnimationFrame(renderPointer);
    }
  }

  function updatePointer(event) {
    if (event.pointerType === 'touch' && event.isPrimary === false) return;
    pointerX = event.clientX;
    pointerY = event.clientY;
    hasPointer = true;
    schedulePointer();
  }

  window.addEventListener('pointermove', updatePointer, { passive: true });
  window.addEventListener('pointerdown', updatePointer, { passive: true });

  window.addEventListener('resize', () => {
    schedulePointer();
  }, { passive: true });

  window.addEventListener('scroll', schedulePointer, { passive: true });

  function clearParallax() {
    if (rootStyle) {
      rootStyle.setProperty('--mx', '0');
      rootStyle.setProperty('--my', '0');
    }
  }

  onMediaChange(reduceQuery, () => {
    reduce = reduceQuery.matches;
    if (reduce) clearParallax();
    schedulePointer();
  });

  onMediaChange(fineQuery, (event) => {
    fine = event.matches;
    if (!fine) clearParallax();
  });

  /* ---------- project selection ---------- */

  function selectionVisible() {
    if (!work) return true;
    const rect = work.getBoundingClientRect();
    return rect.top < window.innerHeight * 0.74 && rect.bottom > 0;
  }

  function selectProject(key, options) {
    if (!PROJECTS.includes(key)) return;
    const settings = options || {};
    const index = PROJECTS.indexOf(key) + 1;

    nodes.forEach((node) => {
      node.setAttribute('aria-pressed', String(node.dataset.project === key));
    });

    entries.forEach((entry) => {
      entry.setAttribute('aria-pressed', String(entry.dataset.project === key));
    });

    details.forEach((detail) => {
      detail.classList.toggle('is-active', detail.dataset.project === key);
    });

    if (settings.announce !== false && status) {
      status.textContent = `Selected ${PROJECT_NAMES[key]}, entry ${String(index).padStart(2, '0')} of 03.`;
    }

    if (settings.scroll && !selectionVisible() && work) {
      work.scrollIntoView({
        behavior: reduce ? 'auto' : 'smooth',
        block: 'start'
      });
    }

    if (settings.hash !== false) {
      try {
        history.replaceState(null, '', `#${key}`);
      } catch (error) {
        /* the selection still works without a URL update */
      }
    }
  }

  function nodeLabel(key) {
    return PROJECT_NAMES[key];
  }

  nodes.forEach((node) => {
    const key = node.dataset.project;
    if (!PROJECTS.includes(key)) return;

    node.addEventListener('pointerenter', () => {
      if (fixLabel) fixLabel.textContent = nodeLabel(key);
    });

    node.addEventListener('pointerleave', () => {
      if (fixLabel) fixLabel.textContent = DEFAULT_LABEL;
    });

    node.addEventListener('focus', () => {
      if (fixLabel) fixLabel.textContent = nodeLabel(key);
    });

    node.addEventListener('blur', () => {
      if (fixLabel) fixLabel.textContent = DEFAULT_LABEL;
    });

    node.addEventListener('click', (event) => {
      selectProject(key, { scroll: event.detail !== 0 });
    });
  });

  entries.forEach((entry) => {
    const key = entry.dataset.project;
    if (!PROJECTS.includes(key)) return;

    entry.addEventListener('click', () => {
      selectProject(key, { scroll: false });
    });
  });

  window.addEventListener('hashchange', () => {
    const key = decodeURIComponent(window.location.hash.slice(1));
    if (PROJECTS.includes(key)) {
      selectProject(key, { scroll: false });
    }
  });

  const initialKey = decodeURIComponent(window.location.hash.slice(1));
  selectProject(PROJECTS.includes(initialKey) ? initialKey : PROJECTS[0], {
    scroll: false,
    announce: false,
    hash: false
  });


  /* ---------- hero raking light ---------- */

  function initHeroShine() {
    const h1 = document.querySelector('.identity h1');
    if (!h1 || reduceQuery.matches) return;

    const supportsMask = typeof CSS !== 'undefined' && CSS.supports &&
      (CSS.supports('mask-image', 'linear-gradient(#000, #000)') ||
       CSS.supports('-webkit-mask-image', 'linear-gradient(#000, #000)'));
    if (!supportsMask) return;
    if (h1.parentElement.querySelector('.h1-shine')) return;

    const shine = h1.cloneNode(true);
    shine.classList.add('h1-shine');
    shine.setAttribute('aria-hidden', 'true');
    h1.parentNode.insertBefore(shine, h1.nextSibling);
  }

  /* ---------- activity field log ---------- */

  const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

  function pad2(value) {
    return String(value).padStart(2, '0');
  }

  function activityStamp(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return 'Synced';
    return `Synced ${pad2(date.getUTCDate())} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()} / ` +
      `${pad2(date.getUTCHours())}:${pad2(date.getUTCMinutes())} UTC`;
  }

  function shortDate(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return '';
    return `${pad2(date.getUTCDate())} ${MONTHS[date.getUTCMonth()]}`;
  }

  function heatLevel(count) {
    if (count <= 0) return 0.07;
    if (count <= 2) return 0.18;
    if (count <= 5) return 0.34;
    if (count <= 9) return 0.55;
    return 0.82;
  }

  function loadActivity() {
    const body = document.getElementById('activity-body');
    const empty = document.getElementById('activity-empty');
    const sync = document.getElementById('activity-sync');
    const heatmap = document.getElementById('heatmap');
    const months = document.getElementById('heatmap-months');
    const readout = document.getElementById('heatmap-readout');
    const languageBar = document.getElementById('language-bar');
    const languageList = document.getElementById('language-list');
    const recentBlock = document.getElementById('recent-block');
    const recentList = document.getElementById('recent-list');

    if (!body || !heatmap || !months) return;

    fetch('data/activity.json', { cache: 'no-store' })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => {
        const totals = data.totals || {};
        const weeks = (data.calendar && data.calendar.weeks) || [];
        const finalWeek = weeks[weeks.length - 1];
        const finalDay = finalWeek && finalWeek.days && finalWeek.days[finalWeek.days.length - 1];
        const finalDate = finalDay ? finalDay.date : '';

        const total = document.getElementById('act-total');
        const streak = document.getElementById('act-streak');
        const repos = document.getElementById('act-repos');
        const stars = document.getElementById('act-stars');

        if (total) total.textContent = Number(totals.contributions || 0).toLocaleString('en-US');
        if (streak) streak.textContent = String(totals.currentStreak || 0);
        if (repos) repos.textContent = String(totals.publicProjects || 0);
        if (stars) stars.textContent = String(totals.stars || 0);

        if (sync) {
          const generated = new Date(data.generatedAt);
          const stale = !Number.isNaN(generated.getTime()) &&
            Date.now() - generated.getTime() > 72 * 3600 * 1000;
          sync.textContent = stale
            ? `Stale / ${activityStamp(data.generatedAt).replace('Synced ', '')}`
            : activityStamp(data.generatedAt);
          sync.classList.toggle('is-stale', stale);
        }

        months.textContent = '';
        let lastMonth = '';
        weeks.forEach((week, index) => {
          const first = week.days && week.days[0];
          if (!first) return;
          const month = first.date.slice(0, 7);
          if (month === lastMonth) return;
          const monthNumber = Number(month.slice(5, 7));
          if (monthNumber % 2 === 1) {
            const span = document.createElement('span');
            span.textContent = MONTHS[monthNumber - 1];
            span.style.gridColumn = `${Math.min(index + 1, 50)} / span 3`;
            months.appendChild(span);
          }
          lastMonth = month;
        });

        heatmap.textContent = '';
        const fragment = document.createDocumentFragment();
        for (let weekIndex = 0; weekIndex < 53; weekIndex += 1) {
          const week = weeks[weekIndex] || { days: [] };
          const byDay = new Map((week.days || []).map((day) => [day.weekday, day]));
          for (let weekday = 0; weekday < 7; weekday += 1) {
            const cell = document.createElement('span');
            cell.className = 'heatmap-cell';
            const day = byDay.get(weekday);
            if (!day) {
              cell.classList.add('is-empty');
            } else {
              cell.style.setProperty('--l', String(heatLevel(day.count)));
              cell.dataset.date = day.date;
              cell.dataset.count = String(day.count);
              cell.title = `${day.date} / ${day.count}`;
              if (day.date === finalDate) cell.classList.add('is-today');
            }
            fragment.appendChild(cell);
          }
        }
        heatmap.appendChild(fragment);

        const defaultReadout = finalDay
          ? `Latest fix / ${finalDay.date} / ${finalDay.count}`
          : 'Latest fix / no signal';
        if (readout) readout.textContent = defaultReadout;

        heatmap.setAttribute(
          'aria-label',
          `${Number(totals.contributions || 0).toLocaleString('en-US')} public contributions in the last 12 months. ` +
          `${Number(totals.activeDays || 0).toLocaleString('en-US')} active days. ` +
          `Current streak ${totals.currentStreak || 0} days.`
        );

        heatmap.addEventListener('pointerover', (event) => {
          const cell = event.target.closest('.heatmap-cell');
          if (!cell || !cell.dataset.date || !readout) return;
          readout.textContent = `Fix / ${cell.dataset.date} / ${cell.dataset.count} contributions`;
        });

        heatmap.addEventListener('pointerleave', () => {
          if (readout) readout.textContent = defaultReadout;
        });

        if (languageBar && languageList) {
          languageBar.textContent = '';
          languageList.textContent = '';
          (data.languages || []).forEach((language, index) => {
            const opacity = index === 0 ? 1 : Math.max(0.16, 0.55 - index * 0.1);
            const segment = document.createElement('span');
            segment.className = 'lang-seg';
            segment.style.width = `calc(${language.percent}% - 2px)`;
            segment.style.setProperty('--o', String(opacity));
            languageBar.appendChild(segment);

            const item = document.createElement('li');
            item.className = 'language-item';

            const swatch = document.createElement('span');
            swatch.className = 'lang-swatch';
            swatch.style.setProperty('--o', String(opacity));

            const name = document.createElement('span');
            name.textContent = `${language.name} `;

            const percent = document.createElement('span');
            percent.className = 'lang-pct';
            percent.textContent = `${language.percent}%`;

            const detail = document.createElement('span');
            detail.className = 'sr-only';
            detail.textContent = `, ${language.repos} projects`;

            item.append(swatch, name, percent, detail);
            languageList.appendChild(item);
          });
        }

        if (recentBlock && recentList) {
          recentList.textContent = '';
          const recent = data.recent || [];
          recentBlock.hidden = recent.length === 0;
          recent.slice(0, 4).forEach((event) => {
            const item = document.createElement('li');
            item.className = 'recent-item';

            const link = document.createElement('a');
            link.className = 'recent-link';
            link.href = event.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';

            const text = document.createElement('span');
            text.className = 'recent-label';
            text.textContent = event.label;

            const time = document.createElement('time');
            time.className = 'recent-date';
            time.dateTime = event.date;
            time.textContent = shortDate(event.date);

            const repo = document.createElement('span');
            repo.className = 'recent-repo';
            repo.textContent = event.repo;

            link.append(text, time, repo);
            item.append(link);
            recentList.appendChild(item);
          });
        }

        body.hidden = false;
        if (empty) empty.hidden = true;
      })
      .catch(() => {
        if (sync) sync.textContent = 'No signal';
        if (empty) empty.hidden = false;
      });
  }

  /* ---------- click pings ---------- */

  if (plate && pings) {
    plate.addEventListener('click', (event) => {
      if (event.button !== 0 || event.detail === 0) return;

      const ping = document.createElement('span');
      ping.className = reduce ? 'ping ping--static' : 'ping';
      ping.style.left = `${event.clientX}px`;
      ping.style.top = `${event.clientY}px`;
      pings.appendChild(ping);

      window.setTimeout(() => {
        ping.remove();
      }, reduce ? 650 : 1000);
    });
  }

  initHeroShine();
  loadActivity();
  renderPointer();
})();
