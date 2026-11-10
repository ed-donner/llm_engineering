"""Smoke test tanpa jaringan: LLM palsu memeriksa seluruh pipeline."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluator import summarize  # noqa: E402
from generator import (GenStats, coerce_row, expand_spec, extract_json,  # noqa: E402
                       generate_dataset, validate_spec)

SPEC = {
    "dataset_name": "keluhan_petani",
    "language": "id",
    "fields": [
        {"name": "keluhan", "type": "string", "description": "isi keluhan"},
        {"name": "urgensi", "type": "category", "description": "tingkat urgensi",
         "allowed_values": ["rendah", "sedang", "tinggi"]},
        {"name": "luas_lahan_ha", "type": "float", "description": "luas lahan"},
    ],
    "variation_attributes": {"komoditas": ["cabai", "tomat"], "gaya": ["santai", "formal"]},
}


class FakeLLM:
    def __init__(self):
        self.counter = 0

    def chat(self, system, user, temperature=0.7, max_tokens=2048):
        if "data designer" in system:  # permintaan skema, dengan teks pengganggu
            return "Tentu, ini skemanya:\n```json\n" + json.dumps(SPEC) + "\n```"
        n = int(re.search(r"Buat (\d+) baris", user).group(1))
        rows = []
        for _ in range(n):
            self.counter += 1
            rows.append({"keluhan": f"Tanaman bermasalah nomor {self.counter} dengan gejala unik {self.counter * 7}",
                         "urgensi": "TINGGI", "luas_lahan_ha": str(0.5 + self.counter / 10)})
        rows.append({"keluhan": "baris rusak", "urgensi": "darurat", "luas_lahan_ha": 1})  # invalid
        rows.append(dict(rows[0]))  # duplikat
        return json.dumps(rows)


def test_extract_json_handles_fences_and_prose():
    assert extract_json('blabla ```json\n{"a": 1}\n``` selesai', want=dict) == {"a": 1}
    assert extract_json("Hasil: [1] lalu [{\"x\": 2}]", want=list) == [1]


def test_validate_spec_rejects_bad_input():
    for bad in ({}, {"fields": [{"name": "Bad Name", "type": "string"}]},
                {"fields": [{"name": "k", "type": "category"}]}):
        try:
            validate_spec(bad)
        except ValueError:
            continue
        raise AssertionError("seharusnya ditolak")


def test_coerce_row():
    fields = validate_spec(SPEC)["fields"]
    ok = coerce_row({"keluhan": " halo ", "urgensi": "Sedang", "luas_lahan_ha": "1.5"}, fields)
    assert ok == {"keluhan": "halo", "urgensi": "sedang", "luas_lahan_ha": 1.5}
    assert coerce_row({"keluhan": "x", "urgensi": "ngawur", "luas_lahan_ha": 1}, fields) is None


def test_expand_spec():
    assert expand_spec("keluhan petani", FakeLLM())["dataset_name"] == "keluhan_petani"


def test_generate_dataset_end_to_end():
    spec = validate_spec(SPEC)
    rows, stats = generate_dataset(spec, FakeLLM(), total=20, batch_size=5)
    assert len(rows) == 20
    assert stats.invalid_rows > 0 and stats.duplicate_rows > 0
    assert {"meta_komoditas", "meta_gaya"} <= set(rows[0])
    import pandas as pd
    report = summarize(pd.DataFrame(rows), spec, stats, 20)
    assert "Ringkasan" in report


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK", name)
