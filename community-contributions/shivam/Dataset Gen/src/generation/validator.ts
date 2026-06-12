import { SchemaField, Schema } from "./prompt-builder.js";

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateRecord(record: Record<string, unknown>, schema: Schema): ValidationResult {
  const errors: string[] = [];

  for (const field of schema) {
    const value = record[field.name];

    if (value === undefined || value === null || value === "") {
      errors.push(`Missing required field: ${field.name}`);
      continue;
    }

    switch (field.type) {
      case "string":
        if (typeof value !== "string") {
          errors.push(`${field.name}: expected string, got ${typeof value}`);
        }
        break;

      case "integer":
        if (!Number.isInteger(value)) {
          errors.push(`${field.name}: expected integer, got ${typeof value}`);
        } else if (field.min !== undefined && (value as number) < field.min) {
          errors.push(`${field.name}: value ${value} below minimum ${field.min}`);
        } else if (field.max !== undefined && (value as number) > field.max) {
          errors.push(`${field.name}: value ${value} above maximum ${field.max}`);
        }
        break;

      case "float":
        if (typeof value !== "number") {
          errors.push(`${field.name}: expected number, got ${typeof value}`);
        } else if (field.min !== undefined && (value as number) < field.min) {
          errors.push(`${field.name}: value ${value} below minimum ${field.min}`);
        } else if (field.max !== undefined && (value as number) > field.max) {
          errors.push(`${field.name}: value ${value} above maximum ${field.max}`);
        }
        break;

      case "boolean":
        if (typeof value !== "boolean") {
          errors.push(`${field.name}: expected boolean, got ${typeof value}`);
        }
        break;

      case "email":
        if (typeof value !== "string" || !value.includes("@")) {
          errors.push(`${field.name}: invalid email format`);
        }
        break;

      case "date":
        if (typeof value !== "string" || isNaN(Date.parse(value))) {
          errors.push(`${field.name}: invalid date format`);
        }
        break;

      case "enum":
        if (typeof value !== "string" || !field.values?.includes(value)) {
          errors.push(`${field.name}: must be one of ${field.values?.join(", ")}`);
        }
        break;
    }
  }

  return { valid: errors.length === 0, errors };
}

export function validateRecords(records: unknown[], schema: Schema): Record<string, unknown>[] {
  const validRecords: Record<string, unknown>[] = [];

  for (let i = 0; i < records.length; i++) {
    const record = records[i];
    if (typeof record !== "object" || record === null) {
      continue;
    }

    const result = validateRecord(record as Record<string, unknown>, schema);
    if (result.valid) {
      validRecords.push(record as Record<string, unknown>);
    }
  }

  return validRecords;
}