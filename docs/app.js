const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, ch => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[ch]));

function weatherLabel(code) {
  if ([45, 48].includes(code)) return 'Fog';
  if ((code >= 71 && code <= 77) || [85, 86].includes(code)) return 'Snow';
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return 'Rain';
  if (code >= 1 && code <= 3) return 'Cloud';
  return 'Clear';
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

function renderRecipe(canvas, recipe, thumbnail = false) {
  const size = 896;
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  const genome = recipe.genome;
  const palette = recipe.palette;
  const weather = recipe.weather;
  const random = randomGenerator(recipe.seed);

  const sky = context.createLinearGradient(0, 0, 0, size);
  sky.addColorStop(0, palette[0]);
  sky.addColorStop(Number(genome.horizon), palette[1]);
  sky.addColorStop(1, palette[2]);
  context.fillStyle = sky;
  context.fillRect(0, 0, size, size);

  const lightX = Number(genome.light_x) * size;
  const lightY = Number(genome.light_y) * size;
  const glow = context.createRadialGradient(lightX, lightY, 2, lightX, lightY, 210);
  glow.addColorStop(0, `${palette[3]}ee`);
  glow.addColorStop(1, `${palette[3]}00`);
  context.fillStyle = glow;
  context.fillRect(0, 0, size, size);

  const count = thumbnail ? Math.min(Number(genome.stroke_count), 320) : Number(genome.stroke_count);
  const horizonY = Number(genome.horizon) * size;
  context.lineCap = 'round';
  for (let index = 0; index < count; index += 1) {
    let x = -40 + random() * (size + 80);
    let y = horizonY * 0.32 + random() * (size + 30 - horizonY * 0.32);
    const phase = random() * Math.PI * 2;
    context.beginPath();
    context.moveTo(x, y);
    for (let step = 0; step < Number(genome.steps); step += 1) {
      const scale = Number(genome.flow_scale);
      const field = Math.sin((x + phase * 40) * scale * 1.7)
        + Math.cos((y - phase * 25) * scale * 1.15)
        + 0.55 * Math.sin((x + y) * scale * 0.62 + phase);
      const pull = Math.atan2(lightY - y, lightX - x) * 0.075;
      const angle = field * Number(genome.curl) + pull - 0.42;
      const stride = Number(genome.step_length) * (0.82 + random() * 0.35);
      x += Math.cos(angle) * stride;
      y += Math.sin(angle) * stride;
      context.lineTo(x, y);
    }
    context.strokeStyle = palette[1 + (index % 3)];
    context.lineWidth = Number(genome.stroke_width) * (0.72 + random() * 0.63);
    context.globalAlpha = Number(genome.opacity) * (0.72 + random() * 0.36);
    context.stroke();
  }
  context.globalAlpha = 1;
  renderWeather(context, weather, palette, random, size);
}

function renderWeather(context, weather, palette, random, size) {
  const code = Number(weather.weather_code);
  if ((code >= 71 && code <= 77) || [85, 86].includes(code)) {
    context.fillStyle = palette[3];
    for (let i = 0; i < 90; i += 1) {
      context.globalAlpha = 0.5;
      context.beginPath();
      context.arc(random() * size, random() * size, 0.8 + random() * 2.6, 0, Math.PI * 2);
      context.fill();
    }
  } else if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
    const angle = (Number(weather.wind_direction) - 90) * Math.PI / 180;
    context.strokeStyle = palette[3];
    context.lineWidth = 1.2;
    context.globalAlpha = 0.25;
    for (let i = 0; i < 115; i += 1) {
      const x = random() * size;
      const y = random() * size;
      const length = 9 + random() * 19;
      context.beginPath();
      context.moveTo(x, y);
      context.lineTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length);
      context.stroke();
    }
  } else if ([45, 48].includes(code)) {
    context.fillStyle = '#dbe3e6';
    context.globalAlpha = 0.22;
    context.fillRect(0, 0, size, size);
  }
  context.globalAlpha = 1;
}

function heroTemplate(day) {
  const poem = day.poem.map(line => `<p>${escapeHtml(line)}</p>`).join('');
  return `
    <div class="hero-art"><canvas id="hero-canvas" role="img" aria-label="${escapeHtml(day.title)}"></canvas></div>
    <div class="hero-copy">
      <p class="eyebrow">${escapeHtml(day.date)} · GENERATION WINNER</p>
      <h1>${escapeHtml(day.title)}</h1>
      <p class="place">${escapeHtml(day.city)}, ${escapeHtml(day.country)}</p>
      <div class="poem">${poem}</div>
      <div class="metadata">
        <span><strong>${Number(day.temperature_c).toFixed(1)}°C</strong>temperature</span>
        <span><strong>${weatherLabel(day.weather.weather_code)}</strong>sky</span>
        <span><strong>${Number(day.score).toFixed(2)}</strong>fitness / 10</span>
        <span><strong>${escapeHtml(day.winner)}</strong>candidate</span>
      </div>
      <button class="speak" type="button">Listen to the poem</button>
    </div>`;
}

const renderedDates = new Set();
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const canvas = entry.target;
    renderRecipe(canvas, canvas.recipe, true);
    observer.unobserve(canvas);
  });
}, { rootMargin: '300px' });

function appendCards(days) {
  const gallery = document.querySelector('#gallery');
  days.forEach(day => {
    if (renderedDates.has(day.date)) return;
    renderedDates.add(day.date);
    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `<canvas role="img" aria-label="${escapeHtml(day.title)}"></canvas>
      <div class="card-copy"><h3>${escapeHtml(day.title)}</h3>
      <p>${escapeHtml(day.city)} · ${escapeHtml(day.date)} · ${Number(day.score).toFixed(2)}</p></div>`;
    const canvas = card.querySelector('canvas');
    canvas.recipe = day;
    observer.observe(canvas);
    gallery.appendChild(card);
  });
}

async function loadArchive() {
  const button = document.querySelector('#load-archive');
  button.disabled = true;
  const months = await fetch('data/archive-index.json', { cache: 'no-store' }).then(response => response.json());
  for (const month of months) {
    const days = await fetch(`data/archive/${month}.json`, { cache: 'no-store' }).then(response => response.json());
    appendCards(days);
  }
  button.hidden = true;
}

fetch('data/recent.json', { cache: 'no-store' })
  .then(response => {
    if (!response.ok) throw new Error('Gallery unavailable');
    return response.json();
  })
  .then(days => {
    if (!days.length) throw new Error('No mornings yet');
    const [latest, ...archive] = days;
    document.querySelector('#hero').innerHTML = heroTemplate(latest);
    renderRecipe(document.querySelector('#hero-canvas'), latest);
    renderedDates.add(latest.date);
    appendCards(archive);
    document.querySelector('#load-archive').hidden = days.length < 90;
    document.querySelector('.speak').addEventListener('click', () => {
      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(`${latest.title}. ${latest.poem.join(' ')}`);
      utterance.rate = 0.88;
      speechSynthesis.speak(utterance);
    });
  })
  .catch(error => {
    document.querySelector('#hero').innerHTML = `<p class="empty">${escapeHtml(error.message)}. Run Skyloom once to begin.</p>`;
  });

document.querySelector('#load-archive').addEventListener('click', () => {
  loadArchive().catch(error => {
    document.querySelector('#load-archive').textContent = `Could not load archive: ${error.message}`;
  });
});
