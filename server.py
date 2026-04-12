from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from env import ProjectManagerEnv, SCENARIOS
from grader import grade_all
from models import EnvState

app = FastAPI(title='AI Project Manager Environment', version='1.1.0')
env = ProjectManagerEnv(scenario='easy')

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Project Manager Environment</title>
  <style>
    :root {
      --bg: #0f1723;
      --bg-soft: #172435;
      --panel: rgba(14, 21, 32, 0.82);
      --panel-strong: rgba(18, 28, 42, 0.94);
      --ink: #edf3fb;
      --muted: #91a4bb;
      --line: rgba(147, 169, 194, 0.18);
      --accent: #d7a55a;
      --accent-2: #4fc3b3;
      --accent-3: #7aa2ff;
      --danger: #ff7a87;
      --shadow: 0 24px 60px rgba(0, 0, 0, 0.34);
      --radius-xl: 28px;
      --radius-lg: 20px;
      --radius-md: 14px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(122, 162, 255, 0.22), transparent 24%),
        radial-gradient(circle at 85% 10%, rgba(79, 195, 179, 0.2), transparent 22%),
        radial-gradient(circle at 50% 100%, rgba(215, 165, 90, 0.18), transparent 24%),
        linear-gradient(180deg, #0c1119 0%, var(--bg) 42%, #0a1018 100%);
      min-height: 100vh;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
      background-size: 72px 72px;
      mask-image: radial-gradient(circle at center, black 28%, transparent 78%);
      opacity: 0.5;
    }
    .wrap {
      position: relative;
      max-width: 1240px;
      margin: 0 auto;
      padding: 36px 20px 54px;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 22px;
      margin-bottom: 26px;
      align-items: end;
    }
    .hero-main,
    .hero-side {
      background: linear-gradient(180deg, rgba(19, 29, 44, 0.92), rgba(11, 18, 28, 0.84));
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }
    .hero-main {
      padding: 34px;
    }
    .hero-side {
      padding: 28px;
      display: grid;
      gap: 18px;
      align-content: space-between;
      min-height: 100%;
    }
    .eyebrow,
    .mini-label {
      font-family: "Avenir Next Condensed", "Arial Narrow", sans-serif;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 12px;
      font-weight: 700;
      color: var(--accent);
    }
    .eyebrow {
      margin-bottom: 14px;
    }
    h1 {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      font-size: clamp(2.7rem, 5.4vw, 5.6rem);
      line-height: 0.88;
      letter-spacing: -0.04em;
      max-width: 760px;
    }
    .subtitle {
      max-width: 700px;
      color: var(--muted);
      font-size: 1.08rem;
      line-height: 1.75;
      margin-top: 18px;
    }
    .hero-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .hero-note {
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 16px 18px;
      background: rgba(255, 255, 255, 0.02);
    }
    .hero-note strong {
      display: block;
      margin-top: 8px;
      font-size: 1.05rem;
      color: var(--ink);
    }
    .hero-copy {
      color: var(--muted);
      line-height: 1.65;
      font-size: 0.98rem;
    }
    .hero-pulse {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border-radius: 999px;
      width: fit-content;
      background: rgba(79, 195, 179, 0.08);
      border: 1px solid rgba(79, 195, 179, 0.18);
      color: #d8fff9;
      font-size: 0.92rem;
    }
    .hero-pulse::before {
      content: "";
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: var(--accent-2);
      box-shadow: 0 0 0 6px rgba(79, 195, 179, 0.12);
    }
    .layout {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 22px;
    }
    .panel {
      background: linear-gradient(180deg, rgba(18, 28, 43, 0.92), rgba(12, 19, 30, 0.82));
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
      padding: 22px;
      backdrop-filter: blur(18px);
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 18px;
    }
    label {
      color: var(--muted);
      font-size: 0.96rem;
      font-weight: 600;
    }
    select, button {
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--ink);
      padding: 12px 18px;
      font: inherit;
    }
    select {
      background: rgba(255, 255, 255, 0.04);
      min-width: 140px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }
    button {
      cursor: pointer;
      background: linear-gradient(135deg, #202f46, #111c2c);
      color: #f8fbff;
      border-color: rgba(122, 162, 255, 0.22);
      font-weight: 700;
      letter-spacing: 0.01em;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    button.secondary {
      background: linear-gradient(135deg, #1d6d65, #154f4a);
      border-color: rgba(79, 195, 179, 0.28);
    }
    button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    button:hover:not(:disabled) {
      transform: translateY(-1px);
      transition: 160ms ease;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .stat {
      padding: 16px;
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02));
      border: 1px solid var(--line);
    }
    .stat span {
      display: block;
      color: var(--muted);
      font-size: 0.86rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }
    .stat strong {
      display: block;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      font-size: 1.65rem;
      margin-top: 8px;
      letter-spacing: -0.03em;
    }
    .hint {
      padding: 18px 18px 18px 22px;
      border: 1px solid rgba(215, 165, 90, 0.18);
      border-left: 4px solid var(--accent);
      background: linear-gradient(90deg, rgba(215, 165, 90, 0.12), rgba(215, 165, 90, 0.04));
      border-radius: var(--radius-lg);
      margin-bottom: 18px;
      line-height: 1.7;
      color: #f3eadf;
    }
    .tasks {
      display: grid;
      gap: 12px;
    }
    .task {
      display: grid;
      gap: 14px;
      padding: 18px;
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(12, 18, 28, 0.94), rgba(18, 27, 41, 0.82));
      border: 1px solid rgba(122, 162, 255, 0.12);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }
    .task-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
    }
    .task-id {
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      font-weight: 700;
      font-size: 1.35rem;
      word-break: break-word;
    }
    .badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .badge {
      display: inline-block;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.06);
      color: #d5e0ee;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .task button {
      width: fit-content;
    }
    .log {
      display: grid;
      gap: 12px;
      max-height: 760px;
      overflow: auto;
      padding-right: 6px;
      scrollbar-width: thin;
      scrollbar-color: rgba(122, 162, 255, 0.42) transparent;
    }
    .entry {
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 16px;
      background: linear-gradient(180deg, rgba(17, 27, 41, 0.96), rgba(11, 17, 27, 0.82));
    }
    .entry-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
      font-weight: 700;
      font-size: 1.05rem;
    }
    .meta {
      color: var(--muted);
      font-size: 0.97rem;
      line-height: 1.72;
    }
    .danger {
      color: var(--danger);
    }
    .empty-state {
      border-style: dashed;
      text-align: center;
      color: var(--muted);
      padding: 28px 20px;
    }
    strong {
      color: var(--ink);
    }
    @media (max-width: 900px) {
      .hero,
      .layout { grid-template-columns: 1fr; }
      .stats,
      .hero-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .hero-main,
      .hero-side,
      .panel { padding: 20px; }
      h1 { max-width: none; }
    }
    @media (max-width: 640px) {
      .wrap { padding: 18px 14px 28px; }
      .stats,
      .hero-grid { grid-template-columns: 1fr 1fr; }
      .controls { align-items: stretch; }
      .controls > * { width: 100%; }
      .task-top,
      .entry-head { flex-direction: column; align-items: flex-start; }
      button { width: 100%; justify-content: center; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="hero-main">
        <div class="eyebrow">Operational Sandbox</div>
        <h1>AI Project Manager Environment</h1>
        <div class="subtitle">
          A premium control surface for evaluating how an agent prioritizes work, manages deadline pressure,
          and preserves schedule quality across a constrained project cycle.
        </div>
      </div>
      <div class="hero-side">
        <div class="hero-pulse">Live environment ready for grading</div>
        <div class="hero-grid">
          <div class="hero-note">
            <div class="mini-label">Domain</div>
            <strong>Real project scheduling</strong>
            <div class="hero-copy">Models trade-offs between impact, urgency, and long-horizon execution quality.</div>
          </div>
          <div class="hero-note">
            <div class="mini-label">Scoring</div>
            <strong>Shaped and deterministic</strong>
            <div class="hero-copy">Reward stays normalized while preserving meaningful variation over each episode.</div>
          </div>
        </div>
      </div>
    </section>

    <div class="layout">
      <section class="panel">
        <div class="controls">
          <label for="scenario">Scenario</label>
          <select id="scenario">
            <option value="easy">easy</option>
            <option value="medium">medium</option>
            <option value="hard" selected>hard</option>
          </select>
          <button id="resetBtn">Reset Episode</button>
          <button id="gradeBtn" class="secondary">Load Baseline Grade</button>
        </div>

        <div class="stats">
          <div class="stat"><span>Scenario</span><strong id="scenarioValue">-</strong></div>
          <div class="stat"><span>Step</span><strong id="stepValue">-</strong></div>
          <div class="stat"><span>Mistakes</span><strong id="mistakesValue">-</strong></div>
          <div class="stat"><span>Total Score</span><strong id="scoreValue">-</strong></div>
        </div>

        <div id="hintBox" class="hint">Reset the environment to begin.</div>
        <div id="tasks" class="tasks"></div>
      </section>

      <section class="panel">
        <div class="entry">
          <div class="entry-head"><span>Live Grade</span><span id="gradeValue">Not loaded</span></div>
          <div class="meta" id="gradeMeta">Run the baseline grader to inspect current scenario performance.</div>
        </div>
        <div class="log" id="log"></div>
      </section>
    </div>
  </div>

  <script>
    const tasksEl = document.getElementById('tasks');
    const logEl = document.getElementById('log');
    const hintBox = document.getElementById('hintBox');
    const scenarioSelect = document.getElementById('scenario');
    const scenarioValue = document.getElementById('scenarioValue');
    const stepValue = document.getElementById('stepValue');
    const mistakesValue = document.getElementById('mistakesValue');
    const scoreValue = document.getElementById('scoreValue');
    const gradeValue = document.getElementById('gradeValue');
    const gradeMeta = document.getElementById('gradeMeta');
    let currentState = null;

    function appendLog(title, payload, danger = false) {
      const entry = document.createElement('div');
      entry.className = 'entry';
      entry.innerHTML = `
        <div class="entry-head">
          <span>${title}</span>
          <span class="${danger ? 'danger' : ''}">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="meta">${payload}</div>
      `;
      logEl.prepend(entry);
    }

    function renderState(state) {
      currentState = state;
      const observation = state.observation;
      scenarioValue.textContent = observation.scenario;
      stepValue.textContent = `${observation.step} / 3`;
      mistakesValue.textContent = state.mistakes;
      scoreValue.textContent = Number(state.total_normalized_reward).toFixed(4);
      hintBox.textContent = observation.hint;

      tasksEl.innerHTML = '';
      if (!observation.tasks.length) {
        const empty = document.createElement('div');
        empty.className = 'entry empty-state';
        empty.innerHTML = '<div class="meta">No active tasks remain. Reset the episode to run another schedule.</div>';
        tasksEl.appendChild(empty);
        return;
      }

      observation.tasks.forEach((task) => {
        const card = document.createElement('div');
        card.className = 'task';
        card.innerHTML = `
          <div class="task-top">
            <div class="task-id">${task.id}</div>
            <button ${state.done ? 'disabled' : ''} data-task-id="${task.id}">Execute Task</button>
          </div>
          <div class="badges">
            <span class="badge">priority ${task.priority}</span>
            <span class="badge">deadline ${task.deadline}</span>
            <span class="badge">estimated ${task.estimated_time}</span>
            <span class="badge">urgency ${task.urgency_score}</span>
          </div>
        `;
        tasksEl.appendChild(card);
      });

      tasksEl.querySelectorAll('button[data-task-id]').forEach((button) => {
        button.addEventListener('click', async () => {
          await runStep(button.getAttribute('data-task-id'));
        });
      });
    }

    async function refreshState() {
      const response = await fetch('/state');
      const state = await response.json();
      renderState(state);
    }

    async function resetEpisode() {
      const response = await fetch('/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: scenarioSelect.value })
      });
      const payload = await response.json();
      appendLog('Reset', payload.info.strategy || 'Environment reset.');
      await refreshState();
    }

    async function runStep(taskId) {
      const response = await fetch('/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
      });
      const payload = await response.json();
      if (!response.ok) {
        appendLog('Error', payload.detail || 'Unknown step error.', true);
        return;
      }
      appendLog(
        `Step ${payload.observation.step}`,
        `Task <strong>${taskId}</strong> | reward ${Number(payload.reward).toFixed(4)}<br>` +
        `Reason: ${payload.info.reason}<br>` +
        `Mistake: ${payload.info.mistake}<br>` +
        `Strategy: ${payload.info.strategy}`,
        payload.info.mistake !== 'No tactical mistakes were identified on this step.'
      );
      await refreshState();
    }

    async function loadGrade() {
      const response = await fetch('/grade');
      const payload = await response.json();
      gradeValue.textContent = Number(payload.average_score).toFixed(4);
      gradeMeta.textContent =
        `easy ${payload.scenario_scores.easy} | medium ${payload.scenario_scores.medium} | hard ${payload.scenario_scores.hard}`;
      appendLog('Baseline Grade', `Average score ${payload.average_score}`);
    }

    document.getElementById('resetBtn').addEventListener('click', resetEpisode);
    document.getElementById('gradeBtn').addEventListener('click', loadGrade);
    refreshState();
  </script>
</body>
</html>
"""


@app.get('/', response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse(INDEX_HTML)


@app.get('/meta')
async def meta() -> dict:
    return {
        'name': 'AI Project Manager Environment',
        'available_scenarios': list(SCENARIOS.keys()),
        'endpoints': ['/reset', '/step', '/state', '/grade'],
    }


@app.post('/reset')
async def reset(request: Request) -> dict:
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    scenario = payload.get('scenario')
    if scenario not in SCENARIOS:
        scenario = None
    try:
        observation = await env.reset(scenario)
        return {
            'observation': observation.model_dump(),
            'reward': 0.0,
            'done': False,
            'info': {
                'scenario': env.scenario,
                'seed': 7,
            },
        }
    except Exception as exc:
        return {
            'observation': (await env.state()).observation.model_dump(),
            'reward': 0.0,
            'done': False,
            'info': {'error': str(exc)},
        }


@app.post('/reset/')
async def reset_with_slash(request: Request) -> dict:
    return await reset(request)


@app.post('/step')
async def step(request: Request) -> dict:
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}
    try:
        observation, reward, done, info = await env.step(payload)
        return {
            'observation': observation.model_dump(),
            'reward': reward,
            'done': done,
            'info': info,
        }
    except Exception as exc:
        return {
            'observation': (await env.state()).observation.model_dump(),
            'reward': 0.0,
            'done': (await env.state()).done,
            'info': {'error': str(exc)},
        }


@app.post('/step/')
async def step_with_slash(request: Request) -> dict:
    return await step(request)


@app.get('/state', response_model=EnvState)
async def state() -> EnvState:
    return (await env.state()).model_dump()


@app.get('/state/')
async def state_with_slash() -> dict:
    return (await env.state()).model_dump()


@app.get('/grade')
async def grade() -> dict:
    return (await grade_all()).model_dump()
