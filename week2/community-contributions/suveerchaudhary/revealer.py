import xml.etree.ElementTree as ET
from IPython.display import display, SVG


def tag(el):
    return el.tag.split("}", 1)[-1]


def reveal(svg):
    if svg:
        ET.register_namespace("", "http://www.w3.org/2000/svg")

        root = ET.fromstring(svg)
        drawable = {"path", "line", "ellipse", "rect", "polygon", "polyline", "circle"}
        style = ET.SubElement(root, "style")
        style.text = """
        @keyframes reveal { from { opacity: 0; } to { opacity: 1; } }
        .reveal { opacity: 0; animation: reveal 0.002s linear forwards; }
        """

        delay = 0.0
        for el in root.iter():
            if tag(el) in drawable:
                existing = el.get("style", "")
                el.set("style", f"{existing};animation-delay:{delay:.1f}s")
                el.set("class", (el.get("class", "") + " reveal").strip())
                delay += 0.15

        display(SVG(ET.tostring(root, encoding="unicode")))
