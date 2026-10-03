const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const safeText = value => String(value ?? '—');
const escapeHtml = value => safeText(value).replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));

let currentDay = null;
let recentDays = [];
let archiveLoaded = false;

function weatherLabel(code) {
  const value = Number(code);
  if (value === 0) return 'Clear';
  if ([45, 48].includes(value)) return 'Fog';
  if ((value >= 71 && value <= 77) || [85, 86].includes(value)) return 'Snow';
  if ((value >= 51 && value <= 67) || (value >= 80 && value <= 82)) return 'Rain';
  if (value >= 1 && value <= 3) return 'Cloud';
  if (value >= 95) return 'Storm';
  return 'Variable';
}

function compass(degrees) {
  const points = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  return points[Math.round(((Number(degrees) % 360) / 45)) % 8];
}

function seedNumber(text) {
  let value = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    value ^= text.charCodeAt(index);
    value = Math.imul(value, 16777619);
  }
  return value >>> 0;
}

function randomGenerator(seed) {
  let state = seedNumber(seed);
  return () => {
    state += 0x6D2B79F5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function minutesFromClock(value) {
  const match = String(value || '').match(/(\d{1,2}):(\d{2})/);
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

function sunPosition(recipe) {
  const now = minutesFromClock(recipe.local_time);
  const sunrise = minutesFromClock(recipe.sunrise);
  const sunset = minutesFromClock(recipe.sunset);
  if (now === null || sunrise === null || sunset === null || sunset <= sunrise) {
    return { progress: Number(recipe.genome.light_x), daylight: true };
  }
  const progress = Math.max(0, Math.min(1, (now - sunrise) / (sunset - sunrise)));
  return { progress, daylight: now >= sunrise && now <= sunset };
}

function renderRecipe(canvas, recipe, thumbnail = false) {
  const size = thumbnail ? 360 : 896;
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  const genome = recipe.genome;
  const palette = recipe.palette;
  const weather = recipe.weather;
  const random = randomGenerator(recipe.seed);
  const temperature = Number(recipe.temperature_c);
  const cloud = Math.max(0, Math.min(100, Number(weather.cloud_cover ?? 50)));
  const wind = Math.max(0, Number(weather.wind_kph || 0));
  const sun = sunPosition(recipe);

  const sky = context.createLinearGradient(0, 0, 0, size);
  sky.addColorStop(0, palette[0]);
  sky.addColorStop(Number(genome.horizon), palette[1]);
  sky.addColorStop(1, palette[2]);
  context.fillStyle = sky;
  context.fillRect(0, 0, size, size);

  context.globalCompositeOperation = 'soft-light';
  context.fillStyle = temperature >= 22
    ? `rgba(244,113,55,${Math.min(.24, (temperature - 18) / 70)})`
    : `rgba(75,143,212,${Math.min(.24, (18 - temperature) / 70)})`;
  context.fillRect(0, 0, size, size);
  context.globalCompositeOperation = 'source-over';

  const lightX = (.14 + sun.progress * .72) * size;
  const arc = Math.sin(Math.PI * sun.progress);
  const lightY = (sun.daylight ? .62 - arc * .42 : .68) * size;
  const glow = context.createRadialGradient(lightX, lightY, 2, lightX, lightY, size * .25);
  glow.addColorStop(0, `${palette[3]}ee`);
  glow.addColorStop(1, `${palette[3]}00`);
  context.fillStyle = glow;
  context.fillRect(0, 0, size, size);

  const baseCount = thumbnail ? Math.min(Number(genome.stroke_count), 320) : Number(genome.stroke_count);
  const count = Math.round(baseCount * (.7 + cloud / 200));
  const horizonY = Number(genome.horizon) * size;
  const windAngle = (Number(weather.wind_direction || 0) - 90) * Math.PI / 180;
  const windPull = Math.min(.45, .12 + wind / 125);
  context.lineCap = 'round';
  for (let index = 0; index < count; index += 1) {
    let x = -40 + random() * (size + 80);
    let y = horizonY * .32 + random() * (size + 30 - horizonY * .32);
    const phase = random() * Math.PI * 2;
    context.beginPath();
    context.moveTo(x, y);
    for (let step = 0; step < Number(genome.steps); step += 1) {
      const scale = Number(genome.flow_scale);
      const field = Math.sin((x + phase * 40) * scale * 1.7)
        + Math.cos((y - phase * 25) * scale * 1.15)
        + .55 * Math.sin((x + y) * scale * .62 + phase);
      const lightPull = Math.atan2(lightY - y, lightX - x) * .07;
      const angle = field * Number(genome.curl) * (1 + wind / 80) + lightPull + windAngle * windPull;
      const stride = Number(genome.step_length) * (.82 + random() * .35);
      x += Math.cos(angle) * stride;
      y += Math.sin(angle) * stride;
      context.lineTo(x, y);
    }
    context.strokeStyle = palette[1 + (index % 3)];
    context.lineWidth = Number(genome.stroke_width) * (.72 + random() * .63);
    context.globalAlpha = Number(genome.opacity) * (.65 + cloud / 250) * (.72 + random() * .36);
    context.stroke();
  }
  context.globalAlpha = 1;
  renderPrecipitation(context, weather, palette, random, size);
}

function renderPrecipitation(context, weather, palette, random, size) {
  const code = Number(weather.weather_code);
  if ((code >= 71 && code <= 77) || [85, 86].includes(code)) {
    context.fillStyle = palette[3];
    for (let index = 0; index < 90; index += 1) {
      context.globalAlpha = .5;
      context.beginPath();
      context.arc(random() * size, random() * size, .8 + random() * 2.6, 0, Math.PI * 2);
      context.fill();
    }
  } else if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
    const angle = (Number(weather.wind_direction) - 90) * Math.PI / 180;
    context.strokeStyle = palette[3];
    context.lineWidth = Math.max(1, size / 750);
    context.globalAlpha = .28;
    for (let index = 0; index < 115; index += 1) {
      const x = random() * size;
      const y = random() * size;
      const length = size * (.01 + random() * .022);
      context.beginPath();
      context.moveTo(x, y);
      context.lineTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length);
      context.stroke();
    }
  } else if ([45, 48].includes(code)) {
    context.fillStyle = '#dbe3e6';
    context.globalAlpha = .2;
    context.fillRect(0, 0, size, size);
  }
  context.globalAlpha = 1;
}

function formatDate(date) {
  const parsed = new Date(`${date}T12:00:00`);
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(parsed).toUpperCase();
}

function setLink(selector, url) {
  const element = $(selector);
  try {
    const parsed = new URL(url);
    element.href = parsed.protocol === 'https:' ? parsed.href : 'https://en.wikipedia.org/';
  } catch (_) {
    element.href = 'https://en.wikipedia.org/';
  }
}

function coordinateLabel(coordinates) {
  const lat = Number(coordinates?.latitude || 0);
  const lon = Number(coordinates?.longitude || 0);
  return `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}  /  ${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`;
}

function readableClock(value) {
  const match = String(value || '').match(/(\d{2}):(\d{2})/);
  if (!match) return '—';
  const hour = Number(match[1]);
  return `${hour % 12 || 12}:${match[2]} ${hour < 12 ? 'AM' : 'PM'}`;
}

function daylightLabel(minutes) {
  const value = Number(minutes || 0);
  return `${Math.floor(value / 60)}H ${value % 60}M`;
}

function setPortraitAsset(kind, asset, city) {
  const link = $(`#${kind}-link`);
  const image = $(`#${kind}-image`);
  const name = $(`#${kind}-name`);
  name.textContent = asset?.name || 'Source pending';
  image.alt = asset?.name ? `${asset.name}, associated with ${city}` : '';
  image.src = asset?.image || '';
  link.classList.toggle('no-image', !asset?.image);
  setLink(`#${kind}-link`, asset?.source);
  image.onerror = () => link.classList.add('no-image');
}

function showDay(day) {
  currentDay = day;
  renderRecipe($('#portrait-canvas'), day);
  const weather = day.weather;
  const context = day.city_context || {};
  const country = context.country_name || day.country_name || day.country;
  const temperature = Number(day.temperature_c);
  const temperatureMood = temperature >= 24 ? 'warm color' : temperature <= 10 ? 'cool color' : 'balanced color';
  $('#portrait-date').textContent = `${day.sample ? 'ARCHIVE SAMPLE' : "TODAY'S CITY"} · ${formatDate(day.date)}`;
  $('#portrait-title').textContent = `${day.city}, ${country}`;
  $('#portrait-explainer').textContent = `${temperature.toFixed(0)}°C gives the background its ${temperatureMood}; ${context.landmark?.name || 'a landmark'} and ${context.person?.name || 'a notable person'} bring ${day.city} into the foreground.`;
  $('#generation-state').textContent = `GEN ${day.date.replaceAll('-', '.')}`;
  $('#city-country').textContent = country;
  $('#city-name').textContent = day.city;
  $('#brief-country').textContent = country;
  $('#known-for').textContent = `${day.city} is known for ${context.known_for || 'its distinct history and culture'}.`;
  $('#note-landmark').textContent = context.landmark?.name || '—';
  $('#note-person').textContent = context.person?.name || '—';
  $('#note-region').textContent = context.continent || '—';
  setPortraitAsset('landmark', context.landmark, day.city);
  setPortraitAsset('person', context.person, day.city);
  $('#temperature').textContent = `${Number(day.temperature_c).toFixed(1)}°`;
  $('#feels-like').textContent = `FEELS ${Number(day.apparent_temperature_c ?? day.temperature_c).toFixed(1)}°C`;
  $('#wind-value').textContent = `${Number(weather.wind_kph).toFixed(0)} km/h`;
  $('#wind-direction').textContent = `${compass(weather.wind_direction)} / ${Math.round(Number(weather.wind_direction))}°`;
  $('#humidity').textContent = `${Math.round(Number(day.relative_humidity ?? 0))}%`;
  $('#weather-state').textContent = weatherLabel(weather.weather_code);
  $('#daylight').textContent = daylightLabel(day.daylight_minutes);

  $('#city-fact').textContent = context.fact || 'A verified city fact will appear on the next generation.';
  $('#city-brief').textContent = context.brief || `${day.city} is today’s selected Skyloom city.`;
  setLink('#fact-source', context.fact_source || context.source);
  setLink('#city-source', context.source);

  $('#canvas-wind').textContent = `${Number(weather.wind_kph).toFixed(0)} KM/H`;
  $('#canvas-cloud').textContent = `${Math.round(Number(weather.cloud_cover ?? 0))}%`;
  $('#canvas-light').textContent = `${Math.round(Number(day.daylight_minutes || 0) / 60)} HRS`;
  $('#decode-temperature').textContent = `${Number(day.temperature_c).toFixed(1)}°C`;
  $('#decode-wind').textContent = `${compass(weather.wind_direction)} ${Math.round(Number(weather.wind_kph))} KM/H`;
  $('#decode-cloud').textContent = `${Math.round(Number(weather.cloud_cover ?? 0))}% COVER`;
  $('#decode-sun').textContent = `${daylightLabel(day.daylight_minutes)} OF LIGHT`;
  $('#decode-rain').textContent = `${Number(weather.precipitation_mm || 0).toFixed(1)} MM`;
  $('#selection-note').textContent = `Four candidate systems rendered. ${safeText(day.winner).toUpperCase()} scored ${Number(day.score).toFixed(2)}/10 and became today’s portrait.`;
  const bytes = new Blob([JSON.stringify(day)]).size;
  $('#recipe-size').textContent = `${(bytes / 1024).toFixed(1)} KB`;
  $('#fitness').textContent = `${Number(day.score).toFixed(2)} / 10`;
  renderMap(day).catch(() => renderFallbackMap(day));
}

const LAND = [
  [[-168,72],[-128,72],[-102,58],[-82,50],[-52,49],[-59,24],[-83,10],[-105,20],[-123,39],[-143,57]],
  [[-82,12],[-67,8],[-48,-2],[-35,-22],[-52,-56],[-70,-50],[-80,-18]],
  [[-10,72],[32,72],[45,58],[74,54],[104,72],[150,62],[178,50],[145,26],[113,16],[88,7],[54,23],[32,36],[8,37],[-10,55]],
  [[-17,36],[12,37],[36,28],[52,10],[39,-35],[18,-35],[2,-25],[-12,4]],
  [[112,-11],[154,-10],[153,-39],[128,-44],[113,-26]],
  [[-52,83],[-18,80],[-26,63],[-48,60]],
  [[44,-13],[51,-16],[49,-26],[43,-24]],
  [[130,34],[145,43],[142,27]]
];
let worldMapPromise;

function projectPoint([longitude, latitude]) {
  return [((longitude + 180) / 360) * 800, ((90 - latitude) / 180) * 380];
}

function polygonPath(rings) {
  return rings.map(ring => ring.map((point, index) => {
    const [x, y] = projectPoint(point);
    return `${index ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join('') + 'Z').join('');
}

function geometryPath(geometry) {
  if (geometry.type === 'Polygon') return polygonPath(geometry.coordinates);
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.map(polygonPath).join('');
  return '';
}

function countryMatches(mapName, requested) {
  const aliases = {
    'United States': 'United States of America',
    'South Korea': 'Republic of Korea',
  };
  return mapName === requested || mapName === aliases[requested];
}

async function renderMap(day) {
  const grid = $('#map-grid');
  const land = $('#map-land');
  const marker = $('#map-marker');
  const country = day.city_context?.country_name || day.country_name || day.country;
  grid.innerHTML = [...Array(7)].map((_, index) => `<line x1="${(index + 1) * 100}" y1="0" x2="${(index + 1) * 100}" y2="380"/>`).join('')
    + [...Array(3)].map((_, index) => `<line x1="0" y1="${(index + 1) * 95}" x2="800" y2="${(index + 1) * 95}"/>`).join('');
  worldMapPromise ||= fetch('data/world-countries.geojson', { cache: 'force-cache' }).then(response => {
    if (!response.ok) throw new Error('Map unavailable');
    return response.json();
  });
  const geojson = await worldMapPromise;
  land.innerHTML = geojson.features.map(feature => {
    const selected = countryMatches(feature.properties.name, country);
    return `<path class="${selected ? 'selected-country' : ''}" d="${geometryPath(feature.geometry)}"/>`;
  }).join('');
  const [x, y] = projectPoint([Number(day.coordinates.longitude), Number(day.coordinates.latitude)]);
  marker.innerHTML = `<circle class="marker-halo" cx="${x}" cy="${y}" r="12"><animate attributeName="r" values="8;17;8" dur="3s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;.15;.8" dur="3s" repeatCount="indefinite"/></circle><circle class="marker-core" cx="${x}" cy="${y}" r="3.5"/>`;
  $('#map-label').textContent = `${day.city}, ${country}`;
}

function renderFallbackMap(day) {
  $('#map-land').innerHTML = LAND.map(polygon => `<polygon points="${polygon.map(point => projectPoint(point).join(',')).join(' ')}"/>`).join('');
  const [x, y] = projectPoint([Number(day.coordinates.longitude), Number(day.coordinates.latitude)]);
  $('#map-marker').innerHTML = `<circle class="marker-halo" cx="${x}" cy="${y}" r="12"/><circle class="marker-core" cx="${x}" cy="${y}" r="3.5"/>`;
  $('#map-label').textContent = `${day.city}, ${day.country_name || day.country}`;
}

function activateTab(name, focus = false) {
  $$('.tabs button').forEach(button => {
    const active = button.dataset.tab === name;
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
    const panel = $(`#${button.dataset.tab}-panel`);
    panel.hidden = !active;
    panel.classList.toggle('active', active);
    if (active && focus) button.focus();
  });
}

function openArchive() {
  $('#archive-drawer').classList.add('open');
  $('#archive-drawer').setAttribute('aria-hidden', 'false');
  $('#drawer-scrim').hidden = false;
  document.body.style.overflow = 'hidden';
  if (!archiveLoaded) loadArchive();
}

function closeArchive() {
  $('#archive-drawer').classList.remove('open');
  $('#archive-drawer').setAttribute('aria-hidden', 'true');
  $('#drawer-scrim').hidden = true;
  document.body.style.overflow = '';
}

function archiveCard(day) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'archive-item';
  const country = day.city_context?.country_name || day.country_name || day.country;
  button.innerHTML = `<canvas aria-hidden="true"></canvas><span><strong>${escapeHtml(day.city)}, ${escapeHtml(country)}</strong>${day.sample ? '<em>SAMPLE</em>' : ''}${escapeHtml(formatDate(day.date))}</span>`;
  renderRecipe(button.querySelector('canvas'), day, true);
  button.addEventListener('click', () => {
    showDay(day);
    activateTab('today');
    closeArchive();
  });
  return button;
}

async function loadArchive() {
  const list = $('#archive-list');
  list.textContent = 'Loading the recipe archive…';
  try {
    const monthsResponse = await fetch('data/archive-index.json', { cache: 'no-store' });
    if (!monthsResponse.ok) throw new Error('Archive index unavailable');
    const months = await monthsResponse.json();
    const pages = await Promise.all(months.map(async month => {
      const response = await fetch(`data/archive/${month}.json`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Archive ${month} unavailable`);
      return response.json();
    }));
    const unique = new Map();
    [...recentDays, ...pages.flat()].forEach(day => unique.set(day.date, day));
    list.textContent = '';
    [...unique.values()].sort((a, b) => b.date.localeCompare(a.date)).forEach(day => list.appendChild(archiveCard(day)));
    if (!list.children.length) list.textContent = 'The first portrait will appear after Skyloom runs.';
    archiveLoaded = true;
  } catch (error) {
    list.textContent = `Archive unavailable: ${error.message}`;
  }
}

function downloadPortrait() {
  if (!currentDay) return;
  const canvas = $('#portrait-canvas');
  canvas.toBlob(blob => {
    const link = document.createElement('a');
    link.download = `skyloom-${currentDay.city.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${currentDay.date}.png`;
    link.href = URL.createObjectURL(blob);
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }, 'image/png');
}

function bindInteractions() {
  $$('.tabs button').forEach((button, index, buttons) => {
    button.addEventListener('click', () => activateTab(button.dataset.tab));
    button.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'ArrowRight' ? (index + 1) % buttons.length : (index + buttons.length - 1) % buttons.length;
      activateTab(buttons[next].dataset.tab, true);
    });
  });
  $('#inspect-button').addEventListener('click', () => activateTab('decode', true));
  $('#portrait-canvas').addEventListener('dblclick', () => activateTab('decode', true));
  $('#guide-button').addEventListener('click', () => $('#guide-dialog').showModal());
  $('#archive-button').addEventListener('click', openArchive);
  $('#archive-close').addEventListener('click', closeArchive);
  $('#drawer-scrim').addEventListener('click', closeArchive);
  $('#download-button').addEventListener('click', downloadPortrait);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && $('#archive-drawer').classList.contains('open')) closeArchive();
  });
}

async function initialise() {
  bindInteractions();
  if (!sessionStorage.getItem('skyloom-guide-seen')) {
    $('#guide-dialog').showModal();
    sessionStorage.setItem('skyloom-guide-seen', 'true');
  }
  try {
    const response = await fetch('data/recent.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Daily signal unavailable');
    recentDays = await response.json();
    if (!recentDays.length) throw new Error('No portraits yet');
    showDay(recentDays[0]);
  } catch (error) {
    $('#portrait-title').textContent = 'Signal offline';
    $('#portrait-date').textContent = error.message.toUpperCase();
    $('#portrait-explainer').textContent = 'Run Skyloom once to create the first city portrait.';
  }
}

initialise();
