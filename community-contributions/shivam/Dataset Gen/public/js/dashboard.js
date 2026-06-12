document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("datasets-list");

  try {
    const datasets = await api.datasets.list();

    if (datasets.length === 0) {
      container.innerHTML = "<p>No datasets yet. Create your first dataset!</p>";
      return;
    }

    const table = document.createElement("table");
    table.innerHTML = `
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>Records</th>
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${datasets
          .map(
            (d) => `
          <tr>
            <td><a href="/dataset.html?id=${d.id}">${d.name}</a></td>
            <td>${d.description || "-"}</td>
            <td>${d._count.records}</td>
            <td>${new Date(d.createdAt).toLocaleDateString()}</td>
            <td>
              <button class="delete-btn" data-id="${d.id}" style="padding: 0.25rem 0.5rem;">Delete</button>
            </td>
          </tr>
        `
          )
          .join("")}
      </tbody>
    `;

    container.innerHTML = "";
    container.appendChild(table);

    container.querySelectorAll(".delete-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.dataset.id;
        if (confirm("Delete this dataset?")) {
          await api.datasets.delete(id);
          location.reload();
        }
      });
    });
  } catch (err) {
    container.innerHTML = `<p class="error">Error loading datasets: ${err.message}</p>`;
  }
});