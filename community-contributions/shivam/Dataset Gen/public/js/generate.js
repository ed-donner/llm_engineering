const params = new URLSearchParams(window.location.search);
const datasetId = params.get("id");

if (!datasetId) {
  alert("No dataset selected");
  window.location.href = "/";
}

let dataset;

async function loadTemplates() {
  try {
    const templates = await api.templates.list();
    const select = document.getElementById("template-select");
    templates.forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t.id;
      opt.textContent = t.name;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Failed to load templates:", err);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    dataset = await api.datasets.get(datasetId);
    document.getElementById("dataset-info").textContent = `${dataset.name} — ${dataset.schema.length} fields`;
    const regenLink = document.getElementById("regenerate-link");
    if (regenLink) regenLink.href = `/generate.html?id=${datasetId}`;

    const promptTemplate = `Generate ${dataset.schema.length} fields: ${dataset.schema.map((f) => f.name).join(", ")}. Make data realistic and diverse.`;
    document.getElementById("prompt-editor").value = promptTemplate;

    const models = await api.models.list();
    const select = document.getElementById("model-select");
    models.slice(0, 20).forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = `${m.name || m.id} (${m.provider || "unknown"})`;
      select.appendChild(opt);
    });

    await loadTemplates();
  } catch (err) {
    alert(`Error: ${err.message}`);
    window.location.href = "/";
  }
});

document.getElementById("template-select").addEventListener("change", async (e) => {
  const templateId = e.target.value;
  if (!templateId) return;

  try {
    const template = await api.templates.get(templateId);
    document.getElementById("prompt-editor").value = template.prompt;
    if (template.modelId) {
      document.getElementById("model-select").value = template.modelId;
    }
  } catch (err) {
    alert(`Error loading template: ${err.message}`);
  }
});

document.getElementById("save-template-btn").addEventListener("click", async () => {
  const name = prompt("Enter template name:");
  if (!name) return;

  try {
    await api.templates.create({
      name,
      schema: dataset.schema,
      prompt: document.getElementById("prompt-editor").value,
      modelId: document.getElementById("model-select").value,
    });
    alert("Template saved!");
    const select = document.getElementById("template-select");
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "-- Select a template --";
    select.insertBefore(opt, select.firstChild);
    await loadTemplates();
  } catch (err) {
    alert(`Error saving template: ${err.message}`);
  }
});

document.querySelector('input[name="temperature"]').addEventListener("input", (e) => {
  document.getElementById("temp-value").textContent = e.target.value;
});

let pollInterval;

document.getElementById("generate-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("start-btn");
  btn.disabled = true;

  const config = {
    datasetId,
    modelId: document.getElementById("model-select").value,
    prompt: document.getElementById("prompt-editor").value,
    targetCount: parseInt(document.querySelector('input[name="targetCount"]').value),
    batchSize: parseInt(document.querySelector('input[name="batchSize"]').value),
    temperature: parseFloat(document.querySelector('input[name="temperature"]').value),
  };

  try {
    const run = await api.generate.start(config);
    document.getElementById("config-section").classList.add("hidden");
    document.getElementById("progress-section").classList.remove("hidden");
    document.getElementById("target-text").textContent = config.targetCount;

    pollInterval = setInterval(async () => {
      const status = await api.generate.status(run.id);
      document.getElementById("progress-text").textContent = status.progress;
      document.getElementById("progress-bar").value = (status.progress / status.totalTarget) * 100;
      document.getElementById("status-text").textContent = status.status;

      if (status.status === "COMPLETED") {
        clearInterval(pollInterval);
        window.location.href = `/dataset.html?id=${datasetId}`;
      } else if (status.status === "FAILED") {
        clearInterval(pollInterval);
        alert(`Generation failed: ${status.error}`);
        btn.disabled = false;
      }
    }, 2000);
  } catch (err) {
    alert(`Error: ${err.message}`);
    btn.disabled = false;
  }
});