from pricer.items import Item

MIN_CHARS = 100
MIN_PRICE = 4
MAX_PRICE = 200

# The countries with the most wines; everything else is grouped as "Other"
TOP_COUNTRIES = [
    "US",
    "France",
    "Italy",
    "Spain",
    "Portugal",
    "Chile",
    "Argentina",
    "Austria",
    "Germany",
    "Australia",
]


def simplify(text) -> str:
    """
    Return a simplified string without line breaks or too much whitespace
    """
    return " ".join(str(text).split())


def make_title(datapoint) -> str:
    """
    Use the title if there is one; otherwise build one in the same style from the other fields
    """
    if datapoint["title"]:
        return simplify(datapoint["title"])
    parts = [datapoint["winery"], datapoint["designation"], datapoint["variety"]]
    title = " ".join(simplify(part) for part in parts if part)
    place = datapoint["region_1"] or datapoint["province"]
    return f"{title} ({simplify(place)})" if place else title


def get_region(datapoint) -> str:
    """
    Return the place the wine comes from, most specific first
    """
    places = [datapoint["region_1"], datapoint["province"], datapoint["country"]]
    return ", ".join(simplify(place) for place in places if place)


def scrub(title, datapoint) -> str:
    """
    Return the full text for this wine, with one detail per line followed by the review
    """
    result = title + "\n"
    result += f"Winery: {simplify(datapoint['winery'])}\n"
    result += f"Variety: {simplify(datapoint['variety'])}\n"
    if datapoint["designation"]:
        result += f"Designation: {simplify(datapoint['designation'])}\n"
    result += f"Region: {get_region(datapoint)}\n"
    result += f"Points: {datapoint['points']}\n"
    result += f"Review: {simplify(datapoint['description'])}"
    return result


def parse(datapoint):
    price = datapoint["price"]
    if price is None:
        return None
    if not (datapoint["winery"] and datapoint["variety"] and datapoint["country"]):
        return None
    if MIN_PRICE <= price <= MAX_PRICE:
        if len(datapoint["description"]) >= MIN_CHARS:
            title = make_title(datapoint)
            country = datapoint["country"]
            return Item(
                title=title,
                category=country if country in TOP_COUNTRIES else "Other",
                price=float(price),
                variety=simplify(datapoint["variety"]),
                winery=simplify(datapoint["winery"]),
                points=datapoint["points"],
                full=scrub(title, datapoint),
            )
