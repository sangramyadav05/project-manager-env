from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from env import ProjectManagerEnv, SCENARIOS
from grader import grade_all
from models import EnvState, ResetResponse, StepRequest, StepResponse

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
      --bg: #f5efe4;
      --panel: #fffaf1;
      --ink: #182028;
      --muted: #5f6b76;
      --line: #d6c7ad;
      --accent: #be5b2c;
      --accent-2: #226f54;
      --danger: #a63d40;
      --shadow: 0 18px 40px rgba(24, 32, 40, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(190, 91, 44, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(34, 111, 84, 0.14), transparent 28%),
        linear-gradient(180deg, #f8f2e8 0%, var(--bg) 100%);
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: grid;
      gap: 18px;
      margin-bottom: 24px;
    }
    .eyebrow {
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      font-weight: 700;
    }
    h1 {
      margin: 0;
      font-size: clamp(2.2rem, 5vw, 4.4rem);
      line-height: 0.95;
    }
    .subtitle {
      max-width: 720px;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.6;
    }
    .layout {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 20px;
    }
    .panel {
      background: color-mix(in srgb, var(--panel) 92%, white 8%);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      padding: 20px;
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 18px;
    }
    select, button {
      border-radius: 999px;
      border: 1px solid var(--line);
      background: white;
      color: var(--ink);
      padding: 10px 16px;
      font: inherit;
    }
    button {
      cursor: pointer;
      background: var(--ink);
      color: #fff8eb;
      border-color: var(--ink);
    }
    button.secondary {
      background: var(--accent-2);
      border-color: var(--accent-2);
    }
    button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .stat {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid var(--line);
    }
    .stat strong {
      display: block;
      font-size: 1.3rem;
      margin-top: 4px;
    }
    .hint {
      padding: 14px 16px;
      border-left: 4px solid var(--accent);
      background: rgba(190, 91, 44, 0.08);
      border-radius: 14px;
      margin-bottom: 18px;
      line-height: 1.5;
    }
    .tasks {
      display: grid;
      gap: 12px;
    }
    .task {
      display: grid;
      gap: 10px;
      padding: 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--line);
    }
    .task-top {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: baseline;
    }
    .task-id {
      font-weight: 700;
      word-break: break-word;
    }
    .badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .badge {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: #f2e8d8;
      font-size: 0.9rem;
    }
    .task button {
      width: fit-content;
    }
    .log {
      display: grid;
      gap: 12px;
      max-height: 760px;
      overflow: auto;
      padding-right: 4px;
    }
    .entry {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.7);
    }
    .entry-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
      font-weight: 700;
    }
    .meta {
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.5;
    }
    .danger {
      color: var(--danger);
    }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">Hackathon Demo</div>
      <h1>AI Project Manager Environment</h1>
      <div class="subtitle">
        A deterministic multi-step scheduling environment where an agent trades off business priority,
        deadline pressure, urgency, and future schedule risk.
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
        empty.className = 'entry';
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
      const response = await fetch(`/reset?scenario=${encodeURIComponent(scenarioSelect.value)}`, { method: 'POST' });
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


@app.post('/reset', response_model=ResetResponse)
async def reset(scenario: str = Query(default='easy')) -> ResetResponse:
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f'Unknown scenario: {scenario}')
    observation, info = await env.reset(scenario)
    return ResetResponse(observation=observation, info=info)


@app.post('/step', response_model=StepResponse)
async def step(request: StepRequest) -> StepResponse:
    try:
        observation, reward, done, info = await env.step(request.task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StepResponse(observation=observation, reward=reward, done=done, info=info)


@app.get('/state', response_model=EnvState)
async def state() -> EnvState:
    return await env.state()


@app.get('/grade')
async def grade() -> dict:
    return (await grade_all()).model_dump()
