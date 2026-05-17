const FIELD_TYPES = [
  { value: "string", label: "String" },
  { value: "integer", label: "Integer" },
  { value: "float", label: "Float" },
  { value: "boolean", label: "Boolean" },
  { value: "email", label: "Email" },
  { value: "date", label: "Date" },
  { value: "enum", label: "Enum (comma-separated values)" },
];

function createFieldRow() {
  const row = document.createElement("div");
  row.className = "schema-field";
  row.innerHTML = `
    <input type="text" name="fieldName" placeholder="Field name" required>
    <select name="fieldType">
      ${FIELD_TYPES.map((t) => `<option value="${t.value}">${t.label}</option>`).join("")}
    </select>
    <input type="text" name="fieldDesc" placeholder="Description (optional)">
    <input type="text" name="fieldConstraints" placeholder="Constraints (e.g., min:18,max:90 or values:a,b,c)">
    <button type="button" class="remove-field secondary">×</button>
  `;
  row.querySelector(".remove-field").addEventListener("click", () => row.remove());
  return row;
}

document.getElementById("add-field").addEventListener("click", () => {
  document.getElementById("schema-fields").appendChild(createFieldRow());
});

document.getElementById("dataset-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = e.target.name.value;
  const description = e.target.description.value;

  const schema = [];
  document.querySelectorAll(".schema-field").forEach((row) => {
    const fieldName = row.querySelector('[name="fieldName"]').value.trim();
    const fieldType = row.querySelector('[name="fieldType"]').value;
    const fieldDesc = row.querySelector('[name="fieldDesc"]').value.trim();
    const fieldConstraints = row.querySelector('[name="fieldConstraints"]').value.trim();

    if (!fieldName) return;

    const field = { name: fieldName, type: fieldType };
    if (fieldDesc) field.description = fieldDesc;

    if (fieldConstraints) {
      if (fieldType === "integer" || fieldType === "float") {
        const [min, max] = fieldConstraints.split(",").map((s) => s.trim());
        if (min) field.min = parseFloat(min);
        if (max) field.max = parseFloat(max);
      } else if (fieldType === "enum") {
        field.values = fieldConstraints.split(",").map((s) => s.trim());
      }
    }

    schema.push(field);
  });

  if (schema.length === 0) {
    alert("Add at least one field to the schema");
    return;
  }

  try {
    const dataset = await api.datasets.create({ name, description, schema });
    window.location.href = `/generate.html?id=${dataset.id}`;
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
});

document.getElementById("schema-fields").appendChild(createFieldRow());