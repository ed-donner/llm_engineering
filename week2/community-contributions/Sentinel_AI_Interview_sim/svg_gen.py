"""
svg_gen.py — SVG Question Generator for Sentinel AI Interview Simulator

Generates visual interview questions using pure Python SVG templates.
No LLM needed — deterministic, instant, and free.
"""

import random
import xml.etree.ElementTree as ET
from IPython.display import display, SVG


def generate_svg_question(question_type=None):
    """Generate a visual SVG question. Returns (svg_string, question_text, answer)."""
    generators = {
        "bar_chart": _generate_bar_chart,
        "shapes": _generate_shapes,
        "flowchart": _generate_flowchart,
    }
    if question_type is None:
        question_type = random.choice(list(generators.keys()))
    if question_type not in generators:
        question_type = "bar_chart"

    svg, question, answer = generators[question_type]()
    print(f"SVG TOOL CALLED: Generated '{question_type}' — answer: {answer}", flush=True)
    return svg, question, answer


def _generate_bar_chart():
    categories = random.sample(["Sales", "Marketing", "Engineering", "Design", "HR", "Ops"], 4)
    values = [random.randint(20, 95) for _ in categories]
    colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]
    bars = ""
    for i, (cat, val, color) in enumerate(zip(categories, values, colors)):
        x = 50 + i * 80
        h = val * 1.5
        y = 200 - h
        bars += f'<rect x="{x}" y="{y}" width="60" height="{h}" fill="{color}" rx="3"/>'
        bars += f'<text x="{x+30}" y="220" text-anchor="middle" font-size="11" fill="#333">{cat}</text>'
        bars += f'<text x="{x+30}" y="{y-5}" text-anchor="middle" font-size="10" fill="#666">{val}</text>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="250" style="background:#fafafa;border-radius:8px;border:1px solid #ddd"><text x="210" y="20" text-anchor="middle" font-size="14" font-weight="bold" fill="#333">Performance</text><line x1="40" y1="200" x2="400" y2="200" stroke="#999"/>{bars}</svg>'
    answer = categories[values.index(max(values))]
    return svg, "Which category has the highest value in this bar chart?", answer


def _generate_shapes():
    shape = random.choice(["circles", "triangles", "rectangles"])
    count = random.randint(3, 7)
    decoys = random.randint(2, 4)
    shapes_svg = ""
    for _ in range(count):
        x, y = random.randint(30, 370), random.randint(40, 220)
        if shape == "circles":
            shapes_svg += f'<circle cx="{x}" cy="{y}" r="{random.randint(12,20)}" fill="{random.choice(["#E91E63","#F44336"])}" opacity="0.8"/>'
        elif shape == "triangles":
            s = random.randint(15, 25)
            shapes_svg += f'<polygon points="{x},{y-s} {x-s},{y+s} {x+s},{y+s}" fill="{random.choice(["#4CAF50","#009688"])}" opacity="0.8"/>'
        else:
            shapes_svg += f'<rect x="{x}" y="{y}" width="{random.randint(20,35)}" height="{random.randint(15,25)}" fill="{random.choice(["#2196F3","#03A9F4"])}" rx="3" opacity="0.8"/>'
    for _ in range(decoys):
        x, y = random.randint(30, 370), random.randint(40, 220)
        shapes_svg += f'<circle cx="{x}" cy="{y}" r="12" fill="#9E9E9E" opacity="0.4"/>' if shape != "circles" else f'<rect x="{x}" y="{y}" width="20" height="15" fill="#9E9E9E" opacity="0.4"/>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="270" style="background:#fafafa;border-radius:8px;border:1px solid #ddd"><text x="210" y="22" text-anchor="middle" font-size="13" fill="#666">Count the colored shapes</text>{shapes_svg}</svg>'
    return svg, f"How many {shape} (colored, not gray) are in this image?", str(count)


def _generate_flowchart():
    threshold = random.randint(3, 8)
    inp = random.randint(1, 10)
    result = "YES" if inp > threshold else "NO"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="280" style="background:#fafafa;border-radius:8px;border:1px solid #ddd">
  <rect x="110" y="10" width="100" height="30" rx="15" fill="#4CAF50"/><text x="160" y="30" text-anchor="middle" font-size="12" fill="white">START</text>
  <line x1="160" y1="40" x2="160" y2="60" stroke="#666" stroke-width="2"/>
  <rect x="95" y="60" width="130" height="30" rx="4" fill="#2196F3"/><text x="160" y="80" text-anchor="middle" font-size="11" fill="white">Input X = {inp}</text>
  <line x1="160" y1="90" x2="160" y2="115" stroke="#666" stroke-width="2"/>
  <polygon points="160,110 240,150 160,190 80,150" fill="#FF9800"/><text x="160" y="153" text-anchor="middle" font-size="11" fill="white">X &gt; {threshold}?</text>
  <line x1="240" y1="150" x2="280" y2="150" stroke="#4CAF50" stroke-width="2"/><line x1="280" y1="150" x2="280" y2="220" stroke="#4CAF50" stroke-width="2"/>
  <text x="258" y="143" font-size="9" fill="#4CAF50">YES</text>
  <rect x="245" y="220" width="70" height="25" rx="4" fill="#4CAF50"/><text x="280" y="237" text-anchor="middle" font-size="11" fill="white">YES</text>
  <line x1="80" y1="150" x2="40" y2="150" stroke="#F44336" stroke-width="2"/><line x1="40" y1="150" x2="40" y2="220" stroke="#F44336" stroke-width="2"/>
  <text x="63" y="143" font-size="9" fill="#F44336">NO</text>
  <rect x="5" y="220" width="70" height="25" rx="4" fill="#F44336"/><text x="40" y="237" text-anchor="middle" font-size="11" fill="white">NO</text>
</svg>'''
    return svg, f"If input X = {inp} and condition is X > {threshold}, what is the output?", result


def reveal(svg):
    """Animate SVG drawing with a reveal effect (from revealer.py)."""
    if svg:
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        root = ET.fromstring(svg)
        drawable = {"path", "line", "rect", "polygon", "polyline", "circle", "text"}
        style_el = ET.SubElement(root, "style")
        style_el.text = "@keyframes reveal{from{opacity:0}to{opacity:1}}.reveal{opacity:0;animation:reveal .002s linear forwards}"
        delay = 0.0
        for el in root.iter():
            tag = el.tag.split("}", 1)[-1]
            if tag in drawable:
                el.set("style", f"{el.get('style','')};animation-delay:{delay:.1f}s")
                el.set("class", (el.get("class", "") + " reveal").strip())
                delay += 0.1
        display(SVG(ET.tostring(root, encoding="unicode")))
