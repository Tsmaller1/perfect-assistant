import asyncio
import hashlib
import logging
import re

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
OVERLAP    = 100


def _clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def _chunk_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start: start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks


async def scrape_business_url(tenant_id: str, url: str) -> list[dict]:
    logger.info("Scraping | tenant=%s | url=%s", tenant_id, url)
    chunks_out: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page    = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            raw_text = await page.evaluate("""
                () => {
                    const walker = document.createTreeWalker(
                        document.body, NodeFilter.SHOW_TEXT,
                        { acceptNode: n =>
                            ['SCRIPT','STYLE','NOSCRIPT'].includes(n.parentElement.tagName)
                            ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT }
                    );
                    const parts = [];
                    let node;
                    while ((node = walker.nextNode())) parts.push(node.textContent.trim());
                    return parts.filter(Boolean).join('\\n');
                }
            """)
            clean = _clean_text(raw_text)
            for i, chunk in enumerate(_chunk_text(clean)):
                chunk_id = hashlib.md5(f"{tenant_id}-{i}-{chunk[:40]}".encode()).hexdigest()
                chunks_out.append({"id": chunk_id, "tenant_id": tenant_id,
                                   "source_url": url, "chunk_index": i, "text": chunk})
        finally:
            await browser.close()

    logger.info("Scraped %d chunks | tenant=%s", len(chunks_out), tenant_id)
    return chunks_out


if __name__ == "__main__":
    result = asyncio.run(scrape_business_url("demo", "https://example.com"))
    print(f"Scraped {len(result)} chunks")
