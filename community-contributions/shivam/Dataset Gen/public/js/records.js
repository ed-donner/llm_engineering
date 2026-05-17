const params = new URLSearchParams(window.location.search);
const datasetId = params.get("id");

if (!datasetId) {
  alert("No dataset selected");
  window.location.href = "/";
}

let dataset;
let currentPage = 1;

async function loadDataset() {
  dataset = await api.datasets.get(datasetId);
  document.getElementById("dataset-title").textContent = dataset.name;
  const regenLink = document.getElementById("regenerate-link");
  if (regenLink) regenLink.href = `/generate.html?id=${datasetId}`;
}

async function loadRecords(page = 1) {
  currentPage = page;
  const { records, pagination } = await api.datasets.getRecords(datasetId, page, 50);

  const tableContainer = document.getElementById("table-container");
  if (records.length === 0) {
    tableContainer.innerHTML = "<p>No records generated yet.</p>";
    return;
  }

  const fields = dataset.schema.map((f) => f.name);

  let tableHtml = `<table><thead><tr>${fields.map((f) => `<th>${f}</th>`).join("")}</tr></thead><tbody>`;
  records.forEach((r) => {
    tableHtml += `<tr>${fields.map((f) => `<td>${JSON.stringify(r.data[f] ?? "")}</td>`).join("")}</tr>`;
  });
  tableHtml += "</tbody></table>";

  tableContainer.innerHTML = tableHtml;

  const paginationNav = document.getElementById("pagination");
  if (pagination.totalPages > 1) {
    let pagesHtml = "";
    const maxVisible = 7;
    let startPage = Math.max(1, page - Math.floor(maxVisible / 2));
    let endPage = Math.min(pagination.totalPages, startPage + maxVisible - 1);
    if (endPage - startPage < maxVisible - 1) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
      pagesHtml += `<li><button onclick="loadRecords(1)">1</button></li>`;
      if (startPage > 2) pagesHtml += `<li>...</li>`;
    }

    for (let i = startPage; i <= endPage; i++) {
      const active = i === page ? 'class="active"' : "";
      pagesHtml += `<li><button ${active} onclick="loadRecords(${i})">${i}</button></li>`;
    }

    if (endPage < pagination.totalPages) {
      if (endPage < pagination.totalPages - 1) pagesHtml += `<li>...</li>`;
      pagesHtml += `<li><button onclick="loadRecords(${pagination.totalPages})">${pagination.totalPages}</button></li>`;
    }

    let prevDisabled = page === 1 ? "disabled" : "";
    let nextDisabled = page === pagination.totalPages ? "disabled" : "";

    paginationNav.innerHTML = `
      <ul>
        <li><button ${prevDisabled} onclick="loadRecords(${page - 1})">Previous</button></li>
        ${pagesHtml}
        <li><button ${nextDisabled} onclick="loadRecords(${page + 1})">Next</button></li>
      </ul>
      <p>Showing ${(page - 1) * pagination.limit + 1}-${Math.min(page * pagination.limit, pagination.total)} of ${pagination.total} records</p>
    `;
  } else {
    paginationNav.innerHTML = "";
  }
}

function showDownloadProgress(format) {
  const progressDiv = document.getElementById("download-progress");
  const progressText = progressDiv.querySelector("p");
  progressText.textContent = `Preparing ${format} download...`;
  progressDiv.classList.remove("hidden");

  setTimeout(() => {
    progressText.textContent = `Downloading ${format}...`;
  }, 500);

  setTimeout(() => {
    progressDiv.classList.add("hidden");
  }, 5000);
}

document.getElementById("export-json").addEventListener("click", () => {
  showDownloadProgress("JSON");
  window.location.href = api.export.json(datasetId);
});

document.getElementById("export-csv").addEventListener("click", () => {
  showDownloadProgress("CSV");
  window.location.href = api.export.csv(datasetId);
});

document.getElementById("export-sql").addEventListener("click", () => {
  showDownloadProgress("SQL");
  window.location.href = api.export.sql(datasetId);
});

(async () => {
  await loadDataset();
  await loadRecords(1);
})();