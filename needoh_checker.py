"""
NeeDoh availability checker across UK toy shops.

Shops covered:
  - Big Jigs Toys  (Shopify – uses /collections/nee-doh/products.json via page context)
  - Menkind        (BigCommerce + Algolia – intercepts search API)

Run:
    python needoh_checker.py
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

import gradio as gr
from playwright.async_api import async_playwright, Browser

# ── URLs ──────────────────────────────────────────────────────────────────────

BIG_JIGS_URL = "https://www.bigjigstoys.co.uk/collections/nee-doh"
BIG_JIGS_COLLECTION_JSON = "/collections/nee-doh/products.json?limit=50"

MENKIND_SEARCH_URL = (
    "https://www.menkind.co.uk/search.php?BigCommerceX%5Bquery%5D=needoh"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Product:
    shop: str
    name: str
    available: bool
    price: str
    url: str


@dataclass
class ShopResult:
    shop: str
    products: list[Product] = field(default_factory=list)
    stocked: bool = True      # False = shop doesn't carry NeeDoh at all
    error: Optional[str] = None


# ── Big Jigs Toys ─────────────────────────────────────────────────────────────

async def fetch_big_jigs(browser: Browser) -> ShopResult:
    """
    Fetches /collections/nee-doh/products.json via the browser's own fetch()
    to avoid Shopify's external IP rate limiting.
    """
    result = ShopResult(shop="Big Jigs Toys")
    page = await browser.new_page(extra_http_headers=HEADERS)

    try:
        await page.goto(BIG_JIGS_URL, timeout=25_000, wait_until="domcontentloaded")

        data = await page.evaluate(f"""
            async () => {{
                const r = await fetch("{BIG_JIGS_COLLECTION_JSON}", {{
                    headers: {{ "Accept": "application/json" }}
                }});
                return r.ok ? await r.json() : {{ error: r.status }};
            }}
        """)

        if "error" in data:
            result.error = f"Shopify returned HTTP {data['error']}"
            return result

        base = "https://www.bigjigstoys.co.uk/products/"
        for p in data.get("products", []):
            variants = p.get("variants", [])
            is_available = any(v.get("available") for v in variants)
            raw_price = variants[0].get("price", "0") if variants else "0"
            try:
                price_str = f"£{float(raw_price):.2f}"
            except (ValueError, TypeError):
                price_str = f"£{raw_price}"

            result.products.append(Product(
                shop="Big Jigs Toys",
                name=p.get("title", "Unknown"),
                available=is_available,
                price=price_str,
                url=base + p.get("handle", ""),
            ))

    except Exception as exc:
        result.error = str(exc)
    finally:
        await page.close()

    return result


# ── Menkind ───────────────────────────────────────────────────────────────────

async def fetch_menkind(browser: Browser) -> ShopResult:
    """
    Loads Menkind's search page and intercepts the Algolia API response,
    then filters for products whose name actually contains 'needoh'.
    """
    result = ShopResult(shop="Menkind")
    captured: list[dict] = []
    page = await browser.new_page(extra_http_headers=HEADERS)

    async def on_response(resp):
        if "algolia" in resp.url.lower() and resp.status == 200:
            try:
                captured.append(await resp.json())
            except Exception:
                pass

    page.on("response", on_response)

    try:
        await page.goto(MENKIND_SEARCH_URL, timeout=25_000, wait_until="networkidle")
        await page.wait_for_timeout(3_000)
    except Exception as exc:
        result.error = f"Page load failed: {exc}"
        await page.close()
        return result
    finally:
        await page.close()

    if not captured:
        result.error = "No Algolia API response captured"
        return result

    hits = captured[0].get("results", [{}])[0].get("hits", [])
    needoh_hits = [
        h for h in hits
        if "needoh" in (h.get("name") or h.get("title") or "").lower()
    ]

    if not needoh_hits:
        result.stocked = False
        return result

    base = "https://www.menkind.co.uk"
    for h in needoh_hits:
        name = h.get("name") or h.get("title") or "Unknown"
        url = h.get("url") or ""
        if url and not url.startswith("http"):
            url = base + url

        prices = h.get("sales_prices") or {}
        price_val = prices.get("GBP")
        price_str = f"£{price_val:.2f}" if price_val else "—"

        is_available = int(h.get("inventory_quantity") or 0) > 0

        result.products.append(Product(
            shop="Menkind",
            name=name,
            available=is_available,
            price=price_str,
            url=url,
        ))

    return result


# ── Orchestration ─────────────────────────────────────────────────────────────

async def run_all_async() -> list[ShopResult]:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        results = await asyncio.gather(
            fetch_big_jigs(browser),
            fetch_menkind(browser),
        )
        await browser.close()
    return list(results)


def check_all() -> tuple[list[list], str]:
    """Gradio callback — returns (table rows, summary markdown)."""
    shop_results = asyncio.run(run_all_async())

    rows: list[list] = []
    summary_parts: list[str] = []

    for sr in shop_results:
        if sr.error:
            rows.append(["❌", sr.shop, f"Error: {sr.error}", "—", "—", "—"])
            summary_parts.append(f"❌ **{sr.shop}**: scrape failed — {sr.error}")
            continue

        if not sr.stocked:
            rows.append(["🔍", sr.shop, "NeeDoh not currently stocked", "—", "—", "—"])
            summary_parts.append(f"🔍 **{sr.shop}**: NeeDoh not currently stocked")
            continue

        in_stock = [p for p in sr.products if p.available]
        total = len(sr.products)
        status_text = (
            f"{len(in_stock)}/{total} variants in stock"
            if in_stock else
            f"All {total} products out of stock"
        )
        emoji = "✅" if in_stock else "🚫"
        summary_parts.append(f"{emoji} **{sr.shop}**: {status_text}")

        for p in sorted(sr.products, key=lambda x: (not x.available, x.name)):
            avail_label = "✅ In stock" if p.available else "🚫 Out of stock"
            link = f"[View]({p.url})" if p.url else "—"
            rows.append(["", p.shop, p.name[:72], avail_label, p.price, link])

    return rows, "\n\n".join(summary_parts)


# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="NeeDoh Availability Checker", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 🧸 NeeDoh Availability Checker\n"
        "Checks live stock across **Big Jigs Toys** and **Menkind**."
    )

    check_btn = gr.Button("Check availability now", variant="primary", size="lg")
    summary_md = gr.Markdown(value="*Click the button above to run a live check.*")
    results_table = gr.Dataframe(
        headers=["", "Shop", "Product", "Availability", "Price", "Link"],
        datatype=["str", "str", "str", "str", "str", "markdown"],
        interactive=False,
        wrap=True,
    )

    check_btn.click(fn=check_all, outputs=[results_table, summary_md])


if __name__ == "__main__":
    demo.launch()
