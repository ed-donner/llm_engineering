export interface SchemaField {
  name: string;
  type: string;
  description?: string;
  min?: number;
  max?: number;
  values?: string[];
}

export interface Schema extends Array<SchemaField> {}

export function buildPrompt(schema: Schema, batchSize: number, userPrompt: string): {
  system: string;
  user: string;
} {
  const schemaDescription = schema
    .map((field) => {
      let desc = `{ "field": "${field.name}", "type": "${field.type}"`;
      if (field.description) desc += `, "description": "${field.description}"`;
      if (field.min !== undefined) desc += `, "min": ${field.min}`;
      if (field.max !== undefined) desc += `, "max": ${field.max}`;
      if (field.values) desc += `, "values": [${field.values.map((v) => `"${v}"`).join(", ")}]`;
      desc += " }";
      return desc;
    })
    .join("\n");

  const system = `You are a synthetic data generator. Generate exactly ${batchSize} records as a valid JSON array matching this schema:

[
  ${schemaDescription}
]

IMPORTANT:
- Return ONLY valid JSON. No markdown, no code fences.
- Each object must have ALL fields.
- Values must respect types and constraints.
- Make the data realistic and diverse.`;

  const user = userPrompt || `Generate ${batchSize} realistic records matching the schema above.`;

  return { system, user };
}