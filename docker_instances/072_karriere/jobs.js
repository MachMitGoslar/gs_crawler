  const CONFIG = window.KARRIERE_JOBS_CONFIG || {};
  const DEFAULT_LOCATION = CONFIG.defaultLocation || 'Goslar';
  const APP_BASE_PATH = CONFIG.appBasePath || '';
  const JOBS_DATA_URL = CONFIG.jobsDataUrl || '072_jobs.json';
  const EMBEDDED_JOBS_DATA = CONFIG.jobsData || null;
  const STATIC_INDEX_URL = CONFIG.staticIndexUrl || '072_karriere_index.html';
  let SEARCH_PARAMS = new URLSearchParams(location.search);
  const LIST_STATE_KEY = 'karriere:list-state:v1';
  const FILTER_MODAL = new bootstrap.Modal(document.getElementById('filter-modal'));
  const state = {
    allJobs: [],
    calendarMonth: startOfMonth(new Date()),
    typeaheadBuffer: {},
    typeaheadTimer: {},
    apiParamsKey: '',
    restoreScrollY: null,
  };

  document.getElementById('jobs-title').textContent = 'Karriere Goslar';

  initToolbar();
  initScrollTopButton();
  load();

  async function load() {
    const apiParams = buildApiParamsFromUrl();
    state.apiParamsKey = apiParams.toString();
    const cachedState = readListState();
    if (!isPageReload() && cachedState && cachedState.apiParamsKey === state.apiParamsKey) {
      state.restoreScrollY = cachedState.scrollY || 0;
      applyJobsPayload(cachedState.payload);
      return;
    }

    try {
      showLoading();
      const payload = await loadJobsPayload();
      applyJobsPayload(payload);
      writeListState({ payload, scrollY: 0 });
    } catch (e) {
      hideLoading();
      showError('Daten konnten nicht geladen werden: ' + e.message);
    }
  }

  async function loadJobsPayload() {
    if (EMBEDDED_JOBS_DATA && Array.isArray(EMBEDDED_JOBS_DATA.results)) {
      return EMBEDDED_JOBS_DATA;
    }
    const res = await fetch(JOBS_DATA_URL, { cache: 'no-cache' });
    if (!res.ok && res.status !== 207) throw new Error('HTTP ' + res.status);
    return res.json();
  }

  function applyJobsPayload(payload) {
    hideLoading();

    if (payload.errors && payload.errors.length) {
      showError(payload.errors.map(x => x.source + ': ' + x.message).join(' | '));
    } else {
      hideError();
    }

    const jobs = payload.results || [];
    state.allJobs = jobs;
    populateDynamicMultiSelect('employer', collectEmployerOptions(jobs));
    populateDynamicMultiSelect('berufsfeld', collectBerufsfeldOptions(jobs));
    renderJobs();
    restoreListPosition();
  }

  function initToolbar() {
    const searchText = SEARCH_PARAMS.get('was') || '';
    document.getElementById('search-input').value = searchText;

    document.getElementById('search-input').addEventListener('input', debounce(applySearchFromToolbar, 250));

    document.getElementById('filter-button').addEventListener('click', openModal);
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('save-filters').addEventListener('click', saveFilters);
    document.getElementById('reset-button').addEventListener('click', resetFilters);
    document.getElementById('filter-modal').addEventListener('click', event => {
      if (event.target.id === 'filter-modal') closeModal();
    });

    bindMultiSelects();
    bindMultiSelectTypeahead('categories');
    bindMultiSelectTypeahead('employer');
    bindMultiSelectTypeahead('berufsfeld');
    initSortPicker();
    initPublishedPicker();
    hydrateModalFromUrl();
  }

  function buildApiParamsFromUrl() {
    const params = new URLSearchParams();
    params.set('location', DEFAULT_LOCATION);
    params.set('wo', DEFAULT_LOCATION);
    return params;
  }

  function hydrateModalFromUrl() {
    setMultiSelectValues('employer', getMultiParam('arbeitgeber'));
    setMultiSelectValues('berufsfeld', getMultiParam('berufsfeld'));
    setMultiSelectValues('arbeitszeit', getMultiParam('arbeitszeit'));
    setMultiSelectValues('befristung', getMultiParam('befristung'));
    document.getElementById('filter-published').value = convertDaysParamToDate(SEARCH_PARAMS.get('veroeffentlichtseit'));
    syncPublishedPicker();
    setMultiSelectValues('categories', getMultiParam('categories'));
    setSortValue(SEARCH_PARAMS.get('sort') || 'title');
  }

  function applySearchFromToolbar() {
    const params = new URLSearchParams(location.search);
    const searchValue = document.getElementById('search-input').value.trim();
    if (searchValue) params.set('was', searchValue);
    else params.delete('was');
    navigateWithParams(params, { replace: true, keepScroll: true });
  }

  function debounce(fn, delay) {
    let timer = null;
    return (...args) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => fn(...args), delay);
    };
  }

  function openModal() {
    FILTER_MODAL.show();
  }

  function closeModal() {
    FILTER_MODAL.hide();
  }

  function saveFilters() {
    const params = new URLSearchParams(location.search);
    setOrDelete(params, 'wo', DEFAULT_LOCATION);
    setOrDelete(params, 'location', DEFAULT_LOCATION);
    setOrDelete(params, 'was', document.getElementById('search-input').value.trim());
    setOrDelete(params, 'arbeitgeber', getMultiSelectValue('employer'));
    setOrDelete(params, 'berufsfeld', getMultiSelectValue('berufsfeld'));
    setOrDelete(params, 'arbeitszeit', getMultiSelectValue('arbeitszeit'));
    setOrDelete(params, 'befristung', getMultiSelectValue('befristung'));
    setOrDelete(params, 'veroeffentlichtseit', convertDateToDaysParam(document.getElementById('filter-published').value));
    setOrDelete(params, 'categories', getMultiSelectValue('categories'));
    setOrDelete(params, 'sort', document.getElementById('filter-sort').value);
    closeModal();
    navigateWithParams(params);
  }

  function resetFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('filter-published').value = '';
    setMultiSelectValues('employer', []);
    setMultiSelectValues('berufsfeld', []);
    setMultiSelectValues('arbeitszeit', []);
    setMultiSelectValues('befristung', []);
    setMultiSelectValues('categories', []);
    setSortValue('title');
    syncPublishedPicker();
    navigateWithParams(new URLSearchParams('location=' + encodeURIComponent(DEFAULT_LOCATION) + '&wo=' + encodeURIComponent(DEFAULT_LOCATION)));
  }

  function navigateWithParams(params, options = {}) {
    const query = params.toString();
    const nextUrl = staticIndexPath() + (query ? '?' + query : '');
    if (options.replace) history.replaceState(null, '', nextUrl);
    else history.pushState(null, '', nextUrl);
    SEARCH_PARAMS = new URLSearchParams(location.search);
    document.getElementById('search-input').value = SEARCH_PARAMS.get('was') || '';
    hydrateModalFromUrl();
    renderJobs();
    writeListState({ scrollY: options.keepScroll ? window.scrollY : 0 });
    if (!options.keepScroll) window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
  }

  function appPath(path) {
    const normalizedPath = '/' + String(path || '').replace(/^\/+/, '');
    return APP_BASE_PATH ? APP_BASE_PATH + normalizedPath : normalizedPath;
  }

  function staticIndexPath() {
    if (APP_BASE_PATH) return appPath('/');
    const current = location.pathname.split('/').pop();
    return current || STATIC_INDEX_URL;
  }

  function setOrDelete(params, key, value) {
    if (value) params.set(key, value);
    else params.delete(key);
  }

  function renderJobs() {
    let jobs = [...state.allJobs];
    const text = (SEARCH_PARAMS.get('was') || '').trim();
    const categories = getMultiParam('categories');
    const employers = getMultiParam('arbeitgeber');
    const berufsfelder = getMultiParam('berufsfeld');
    const arbeitszeiten = getMultiParam('arbeitszeit');
    const befristungen = getMultiParam('befristung');
    const publishedSinceDays = SEARCH_PARAMS.get('veroeffentlichtseit');
    const sort = SEARCH_PARAMS.get('sort') || 'title';

    if (text) jobs = jobs.filter(job => matchesText(job, text));
    if (categories.length) jobs = jobs.filter(job => categories.includes(job.category));
    if (employers.length) jobs = jobs.filter(job => employers.includes(String(job.employer || '').trim()));
    if (berufsfelder.length) jobs = jobs.filter(job => berufsfelder.includes(getBerufsfeldValue(job)));
    if (arbeitszeiten.length) jobs = jobs.filter(job => matchesAnyRawText(job, arbeitszeiten));
    if (befristungen.length) jobs = jobs.filter(job => matchesAnyRawText(job, befristungen));
    if (publishedSinceDays) jobs = jobs.filter(job => isPublishedWithinDays(job, Number(publishedSinceDays)));

    jobs.sort((a, b) => sortValue(a, sort).localeCompare(sortValue(b, sort), 'de'));
    if (sort === 'published') jobs.reverse();

    updateCount(jobs.length, state.allJobs.length);
    updateFilterSummary(jobs.length, state.allJobs.length);

    const grid = document.getElementById('grid');
    grid.innerHTML = '';

    if (!jobs.length) {
      showEmptyState();
      return;
    }

    hideError();

    for (const job of jobs) {
      const card = document.createElement(job.click_url ? 'a' : 'div');
      card.className = 'gs-list-widget';
      if (job.click_url) {
        card.href = job.click_url;
        if (isExternalUrl(job.click_url)) {
          card.target = '_blank';
          card.rel = 'noopener noreferrer';
        }
        card.addEventListener('click', () => writeListState({ scrollY: window.scrollY }));
      }

      const meta = [job.category_label, buildLocation(job)].filter(Boolean).join(' · ');
      card.innerHTML = '<div class="gs-list-widget__content">'
        + '<div class="gs-list-widget__title">' + esc(job.title || 'Ohne Titel') + '</div>'
        + '<div class="gs-list-widget__subtitle">' + esc(job.employer || 'Kein Arbeitgeber hinterlegt') + '</div>'
        + '<div class="gs-list-widget__meta">' + esc(meta) + '</div>'
        + '<div class="gs-list-widget__cta">' + (job.click_url ? 'Öffnen →' : 'Kein Link verfügbar') + '</div>'
        + '</div>';
      grid.appendChild(card);
    }
  }

  function updateCount(visible, total) {
    const countEl = document.getElementById('count');
    countEl.style.display = 'block';
    countEl.textContent = visible + ' von ' + total + ' ' + (total === 1 ? 'Angebot' : 'Angeboten');
  }

  function updateFilterSummary(visible, total) {
    const active = ['Gebiet: Landkreis Goslar'];
    for (const key of ['was', 'arbeitgeber', 'berufsfeld', 'arbeitszeit', 'befristung', 'veroeffentlichtseit', 'categories']) {
      const value = SEARCH_PARAMS.get(key);
      if (value) active.push(formatFilterSummaryItem(key, value));
    }
    active.push('Sortierung: ' + (SEARCH_PARAMS.get('sort') || 'title'));
    document.getElementById('filter-summary').textContent = visible + '/' + total + ' sichtbar | ' + active.join(' | ');
  }

  function formatFilterSummaryItem(key, value) {
    if (key === 'veroeffentlichtseit') {
      const date = parseInputDate(convertDaysParamToDate(value));
      return 'Veröffentlicht seit: ' + (date ? formatDateForDisplay(date) : value);
    }
    return key + ': ' + value;
  }

  function showLoading() {
    const el = document.getElementById('loading');
    el.style.display = 'block';
  }

  function hideLoading() {
    document.getElementById('loading').style.display = 'none';
  }

  function showError(message) {
    const el = document.getElementById('error');
    el.textContent = message;
    el.style.display = 'block';
  }

  function hideError() {
    document.getElementById('error').style.display = 'none';
  }

  function showEmptyState() {
    const categories = getMultiParam('categories');
    const noResults = getNoResultCategoryLabels(categories);

    if (!categories.length) {
      showError('Keine Angebote passen zu den gewählten Filtern.');
      return;
    }

    const parts = [];
    if (noResults.length) {
      parts.push('Für ' + noResults.join(', ') + ' gibt es aktuell keine Treffer im Landkreis Goslar.');
    }
    showError(parts.join(' '));
  }

  function getNoResultCategoryLabels(categories) {
    const mapping = {
      studium: 'Studium',
      ausbildung: 'Ausbildungsstellen',
      selbststaendigkeit: 'Selbständigkeit',
      praktikum: 'Praktikum/Trainee/Werkstudent',
      jobs: 'Jobs',
    };
    return categories
      .filter(category => mapping[category] && !state.allJobs.some(job => job.category === category))
      .map(category => mapping[category]);
  }

  function sortValue(job, sort) {
    if (sort === 'employer') return String(job.employer || '').toLowerCase();
    if (sort === 'location') return buildLocation(job).toLowerCase();
    if (sort === 'published') return String(job.published_at || '');
    return String(job.title || '').toLowerCase();
  }

  function buildLocation(job) {
    const location = job.location || {};
    return [location.postal_code, location.city].filter(Boolean).join(' · ');
  }

  function matchesText(job, query) {
    return normalizeSearchText(buildSearchHaystack(job)).includes(normalizeSearchText(query));
  }

  function matchesAnyRawText(job, values) {
    const haystack = normalizeSearchText(buildSearchHaystack(job));
    return values.some(value => haystack.includes(normalizeSearchText(value)));
  }

  function buildSearchHaystack(job) {
    return [
      job.title,
      job.employer,
      job.category_label,
      job.source_label,
      buildLocation(job),
      getBerufsfeldValue(job),
      JSON.stringify(job.raw || {}),
    ].filter(Boolean).join(' ');
  }

  function normalizeSearchText(value) {
    return String(value || '')
      .toLocaleLowerCase('de-DE')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/ß/g, 'ss')
      .trim();
  }

  function isPublishedWithinDays(job, days) {
    if (!Number.isFinite(days) || days <= 0 || !job.published_at) return true;
    const published = new Date(job.published_at);
    if (Number.isNaN(published.getTime())) return true;
    const threshold = new Date();
    threshold.setDate(threshold.getDate() - days);
    threshold.setHours(0, 0, 0, 0);
    return published >= threshold;
  }

  function isExternalUrl(url) {
    return /^https?:\/\//i.test(String(url || ''));
  }

  function esc(str) {
    return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function getMultiParam(key) {
    const value = SEARCH_PARAMS.get(key) || '';
    return value ? value.split(';').filter(Boolean) : [];
  }

  function getMultiSelectValue(name) {
    return [...document.querySelectorAll('[data-multi-select="' + name + '"]')]
      .filter(input => input.checked)
      .map(input => input.value)
      .join(';');
  }

  function populateDynamicMultiSelect(name, values) {
    const menu = document.getElementById('filter-' + name + '-menu');
    if (!menu) return;

    if (!values.length) {
      menu.innerHTML = '<div class="multi-select-option dropdown-option">Keine Optionen verfügbar</div>';
      updateMultiSelectSummary(name);
      return;
    }

    menu.innerHTML = values.map(value =>
      '<label class="multi-select-option dropdown-option">'
      + '<input type="checkbox" value="' + esc(value) + '" data-multi-select="' + name + '" /> '
      + esc(value)
      + '</label>'
    ).join('');

    for (const input of menu.querySelectorAll('[data-multi-select]')) {
      input.addEventListener('change', () => updateMultiSelectSummary(input.dataset.multiSelect));
    }

    const paramName = name === 'employer' ? 'arbeitgeber' : name;
    setMultiSelectValues(name, getMultiParam(paramName));
  }

  function setMultiSelectValues(name, values) {
    const selected = new Set(values);
    for (const input of document.querySelectorAll('[data-multi-select="' + name + '"]')) {
      input.checked = selected.has(input.value);
    }
    updateMultiSelectSummary(name);
  }

  function bindMultiSelects() {
    for (const input of document.querySelectorAll('[data-multi-select]')) {
      input.addEventListener('change', () => updateMultiSelectSummary(input.dataset.multiSelect));
    }
  }

  function bindMultiSelectTypeahead(name) {
    const button = document.getElementById('filter-' + name);
    const menu = button ? button.nextElementSibling : null;
    if (!button || !menu) return;

    const handler = event => {
      if (event.key.length !== 1 || event.ctrlKey || event.metaKey || event.altKey) return;
      const char = event.key.toLocaleLowerCase('de-DE');
      if (!/[a-zA-ZäöüÄÖÜß]/.test(char)) return;

      event.preventDefault();
      bootstrap.Dropdown.getOrCreateInstance(button).show();
      queueMultiSelectTypeahead(name, char, menu);
    };

    button.addEventListener('keydown', handler);
    menu.addEventListener('keydown', handler);
  }

  function queueMultiSelectTypeahead(name, char, menu) {
    clearTimeout(state.typeaheadTimer[name]);
    state.typeaheadBuffer[name] = (state.typeaheadBuffer[name] || '') + char;
    jumpToMultiSelectOption(name, state.typeaheadBuffer[name], menu);
    state.typeaheadTimer[name] = setTimeout(() => {
      state.typeaheadBuffer[name] = '';
    }, 650);
  }

  function jumpToMultiSelectOption(name, query, menu) {
    const options = [...menu.querySelectorAll('.multi-select-option')];
    if (!options.length) return;

    const normalizedQuery = normalizeTypeaheadText(query);
    const match = options.find(option =>
      normalizeTypeaheadText(option.textContent).startsWith(normalizedQuery)
    );
    if (!match) return;

    for (const option of options) option.classList.remove('is-typeahead-target');
    match.classList.add('is-typeahead-target');
    match.scrollIntoView({ block: 'nearest' });

    const input = match.querySelector('input');
    if (input) input.focus();

    setTimeout(() => match.classList.remove('is-typeahead-target'), 700);
  }

  function normalizeTypeaheadText(value) {
    return String(value || '')
      .toLocaleLowerCase('de-DE')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/ß/g, 'ss')
      .trim();
  }

  function initSortPicker() {
    for (const option of document.querySelectorAll('[data-sort-option]')) {
      option.addEventListener('click', () => {
        setSortValue(option.dataset.sortOption || 'title');
        bootstrap.Dropdown.getOrCreateInstance(document.getElementById('filter-sort-toggle')).hide();
      });
    }
  }

  function setSortValue(value) {
    const normalized = ['title', 'employer', 'location', 'published'].includes(value) ? value : 'title';
    document.getElementById('filter-sort').value = normalized;

    for (const option of document.querySelectorAll('[data-sort-option]')) {
      option.classList.toggle('is-selected-option', option.dataset.sortOption === normalized);
    }

    document.getElementById('filter-sort-summary').textContent = sortLabel(normalized);
  }

  function sortLabel(value) {
    if (value === 'employer') return 'Arbeitgeber A-Z';
    if (value === 'location') return 'Ort A-Z';
    if (value === 'published') return 'Neueste zuerst';
    return 'Titel A-Z';
  }

  function updateMultiSelectSummary(name) {
    const labels = [...document.querySelectorAll('[data-multi-select="' + name + '"]:checked')]
      .map(input => input.parentElement.textContent.trim());
    const button = document.getElementById('filter-' + name);
    if (!button) return;
    const target = button.querySelector('.multi-select-summary');
    if (!target) return;
    if (!labels.length) {
      target.textContent = defaultMultiSelectSummary(name);
      return;
    }
    target.textContent = labels.length === 1 ? labels[0] : labels.length + ' ausgewählt';
  }

  function defaultMultiSelectSummary(name) {
    if (name === 'categories') return 'Alle Kategorien';
    if (name === 'employer') return 'Alle Arbeitgeber';
    if (name === 'berufsfeld') return 'Alle Berufsfelder';
    return 'Beliebig';
  }

  function collectEmployerOptions(jobs) {
    return uniqueSortedValues(jobs.map(job => String(job.employer || '').trim()).filter(Boolean));
  }

  function collectBerufsfeldOptions(jobs) {
    return uniqueSortedValues(jobs.map(getBerufsfeldValue).filter(Boolean));
  }

  function readListState() {
    try {
      const raw = sessionStorage.getItem(LIST_STATE_KEY);
      if (!raw) return null;
      const saved = JSON.parse(raw);
      if (!saved) return null;
      if (!saved.payload || !Array.isArray(saved.payload.results)) return null;
      return saved;
    } catch {
      clearListState();
      return null;
    }
  }

  function writeListState(overrides = {}) {
    const previous = readListState() || {};
    const payload = overrides.payload || previous.payload;
    if (!payload) return;
    sessionStorage.setItem(LIST_STATE_KEY, JSON.stringify({
      payload,
      listUrl: location.href,
      apiParamsKey: state.apiParamsKey || buildApiParamsFromUrl().toString(),
      scrollY: Number.isFinite(overrides.scrollY) ? overrides.scrollY : window.scrollY,
      savedAt: Date.now(),
    }));
  }

  function clearListState() {
    sessionStorage.removeItem(LIST_STATE_KEY);
  }

  function restoreListPosition() {
    if (state.restoreScrollY === null) return;
    const scrollY = state.restoreScrollY;
    state.restoreScrollY = null;
    requestAnimationFrame(() => window.scrollTo({ top: scrollY, left: 0, behavior: 'auto' }));
  }

  function initScrollTopButton() {
    const button = document.getElementById('scroll-top-button');
    if (!button) return;
    const syncVisibility = () => {
      button.classList.toggle('is-visible', window.scrollY > 420);
    };
    button.addEventListener('click', () => window.scrollTo({ top: 0, left: 0, behavior: 'smooth' }));
    window.addEventListener('scroll', syncVisibility, { passive: true });
    syncVisibility();
  }

  window.addEventListener('pagehide', () => writeListState({ scrollY: window.scrollY }));
  window.addEventListener('popstate', () => {
    SEARCH_PARAMS = new URLSearchParams(location.search);
    document.getElementById('search-input').value = SEARCH_PARAMS.get('was') || '';
    hydrateModalFromUrl();
    renderJobs();
    restoreListPosition();
  });

  function isPageReload() {
    const navigation = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    return navigation && navigation.type === 'reload';
  }

  function uniqueSortedValues(values) {
    return [...new Set(values)].sort((left, right) => left.localeCompare(right, 'de'));
  }

  function getBerufsfeldValue(job) {
    return String((job.raw && job.raw.beruf) || '').trim();
  }

  function initPublishedPicker() {
    document.getElementById('calendar-prev').addEventListener('click', () => {
      state.calendarMonth = addMonths(state.calendarMonth, -1);
      renderPublishedCalendar();
    });
    document.getElementById('calendar-next').addEventListener('click', () => {
      state.calendarMonth = addMonths(state.calendarMonth, 1);
      renderPublishedCalendar();
    });

    for (const button of document.querySelectorAll('[data-calendar-preset]')) {
      button.addEventListener('click', () => {
        const days = Number(button.dataset.calendarPreset);
        const date = new Date();
        date.setHours(0, 0, 0, 0);
        date.setDate(date.getDate() - days);
        setPublishedDate(formatDateForInput(date), true);
      });
    }

    for (const button of document.querySelectorAll('[data-calendar-action="clear"]')) {
      button.addEventListener('click', () => setPublishedDate('', true));
    }
  }

  function syncPublishedPicker() {
    const value = document.getElementById('filter-published').value;
    const selectedDate = parseInputDate(value);
    state.calendarMonth = startOfMonth(selectedDate || new Date());
    updatePublishedSummary();
    renderPublishedCalendar();
  }

  function updatePublishedSummary() {
    const value = document.getElementById('filter-published').value;
    const target = document.getElementById('filter-published-summary');
    if (!value) {
      target.textContent = 'Beliebiger Zeitraum';
      return;
    }
    const date = parseInputDate(value);
    target.textContent = date ? formatDateForDisplay(date) : 'Beliebiger Zeitraum';
  }

  function renderPublishedCalendar() {
    const month = state.calendarMonth;
    const monthLabel = document.getElementById('calendar-month-label');
    const grid = document.getElementById('calendar-grid');
    const selectedValue = document.getElementById('filter-published').value;
    const selectedDate = selectedValue ? parseInputDate(selectedValue) : null;
    const today = startOfDay(new Date());

    monthLabel.textContent = month.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
    grid.innerHTML = '';

    const firstDayOffset = (month.getDay() + 6) % 7;
    for (let i = 0; i < firstDayOffset; i += 1) {
      const empty = document.createElement('div');
      empty.className = 'calendar-day-empty';
      grid.appendChild(empty);
    }

    const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
    for (let day = 1; day <= daysInMonth; day += 1) {
      const date = new Date(month.getFullYear(), month.getMonth(), day);
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'calendar-day';
      button.textContent = String(day);

      if (isSameDate(date, today)) button.classList.add('is-today');
      if (selectedDate && isSameDate(date, selectedDate)) button.classList.add('is-selected');

      button.addEventListener('click', () => setPublishedDate(formatDateForInput(date), true));
      grid.appendChild(button);
    }
  }

  function setPublishedDate(value, shouldClose) {
    document.getElementById('filter-published').value = value;
    const selectedDate = parseInputDate(value);
    if (selectedDate) state.calendarMonth = startOfMonth(selectedDate);
    updatePublishedSummary();
    renderPublishedCalendar();
    if (shouldClose) {
      bootstrap.Dropdown.getOrCreateInstance(document.getElementById('filter-published-toggle')).hide();
    }
  }

  function startOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1);
  }

  function startOfDay(date) {
    const copy = new Date(date);
    copy.setHours(0, 0, 0, 0);
    return copy;
  }

  function addMonths(date, offset) {
    return new Date(date.getFullYear(), date.getMonth() + offset, 1);
  }

  function parseInputDate(value) {
    if (!value) return null;
    const date = new Date(value + 'T00:00:00');
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return year + '-' + month + '-' + day;
  }

  function formatDateForDisplay(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return day + '.' + month + '.' + date.getFullYear();
  }

  function isSameDate(left, right) {
    return left.getFullYear() === right.getFullYear()
      && left.getMonth() === right.getMonth()
      && left.getDate() === right.getDate();
  }

  function convertDateToDaysParam(dateString) {
    if (!dateString) return '';
    const selected = new Date(dateString + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffMs = today.getTime() - selected.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    return diffDays >= 0 ? String(diffDays) : '0';
  }

  function convertDaysParamToDate(daysValue) {
    if (!daysValue) return '';
    const days = Number(daysValue);
    if (Number.isNaN(days)) return '';
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - days);
    return date.toISOString().slice(0, 10);
  }
