"""
Web scraper for business website data extraction
Extracts business info, services, pricing, hours, contact info, etc.
"""

import asyncio
import json
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Regex patterns
PHONE_PATTERN = r"(\+?1?)[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})"
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PRICE_PATTERN = r"\$[\d,]+\.?\d{0,2}"
HOURS_PATTERN = r"(mon|tue|wed|thu|fri|sat|sun)(?:day|.)?\s*[:-]?\s*(\d{1,2}):?(\d{2})?\s*(?:am|pm)?[\s-]*(\d{1,2}):?(\d{2})?\s*(?:am|pm)?"


class BusinessScraper:
    """Scrapes business website for relevant data."""

    def __init__(self, timeout: int = 60, max_pages: int = 20):
        self.timeout = timeout
        self.max_pages = max_pages
        self.visited_urls = set()
        self.content = {}

    async def scrape(self, url: str) -> dict:
        """
        Main scrape entry point.

        Args:
            url: Website URL to scrape

        Returns:
            Structured business data
        """
        try:
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            # Start crawling from homepage
            await self._crawl(url)

            # Extract structured data
            business_data = self._extract_business_data()

            return {
                "status": "success",
                "data": business_data,
                "warnings": [],
            }
        except asyncio.TimeoutError:
            logger.error(f"Scrape timeout for {url}")
            return {"status": "error", "error": "Scrape timeout", "data": {}}
        except Exception as e:
            logger.error(f"Scrape error for {url}: {e}")
            return {"status": "error", "error": str(e), "data": {}}

    async def _crawl(self, start_url: str) -> None:
        """Crawl website and extract all content."""
        to_visit = [start_url]
        domain = urlparse(start_url).netloc

        async with httpx.AsyncClient(timeout=10) as client:
            while to_visit and len(self.visited_urls) < self.max_pages:
                url = to_visit.pop(0)

                # Skip if already visited
                if url in self.visited_urls:
                    continue

                # Skip if different domain
                if urlparse(url).netloc != domain:
                    continue

                try:
                    logger.info(f"Scraping: {url}")
                    response = await client.get(url)
                    response.raise_for_status()

                    self.visited_urls.add(url)
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Store page content
                    self.content[url] = {
                        "text": soup.get_text(),
                        "soup": soup,
                        "html": response.text,
                    }

                    # Find new links to visit
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        absolute_url = urljoin(url, href)

                        # Only visit same domain, internal links
                        if urlparse(absolute_url).netloc == domain and absolute_url not in self.visited_urls:
                            to_visit.append(absolute_url)

                    # Prioritize key pages
                    to_visit.sort(
                        key=lambda x: self._priority_score(x), reverse=True
                    )

                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")

    def _priority_score(self, url: str) -> int:
        """Score URL for crawl priority."""
        path = urlparse(url).path.lower()
        score = 0

        priority_keywords = [
            ("contact", 10),
            ("about", 9),
            ("service", 8),
            ("product", 8),
            ("pricing", 7),
            ("faq", 6),
            ("help", 5),
        ]

        for keyword, value in priority_keywords:
            if keyword in path:
                score = max(score, value)

        return score

    def _extract_business_data(self) -> dict:
        """Extract structured business data from crawled content."""
        combined_text = "\n".join(
            [c["text"] for c in self.content.values()]
        )

        # Extract basic info
        business = {
            "name": self._extract_business_name(),
            "website": list(self.content.keys())[0] if self.content else "",
            "phone": self._extract_phone(combined_text),
            "email": self._extract_email(combined_text),
            "address": self._extract_address(combined_text),
            "hours": self._extract_hours(combined_text),
        }

        # Extract services/products
        services = self._extract_services()

        # Extract pricing
        pricing = self._extract_pricing()

        # Extract FAQs
        faqs = self._extract_faqs()

        # Extract social media
        social = self._extract_social_media()

        # Build AI context
        description = self._extract_description()
        ai_context = self._build_ai_context(business, description, services, pricing)

        return {
            "business": business,
            "description": description,
            "services": services,
            "pricing": pricing,
            "faqs": faqs,
            "social_media": social,
            "ai_context": ai_context,
        }

    def _extract_business_name(self) -> str:
        """Extract business name from title or h1."""
        for content in self.content.values():
            soup = content["soup"]

            # Try title tag
            title = soup.find("title")
            if title:
                return title.text.strip().split("|")[0].strip()

            # Try h1
            h1 = soup.find("h1")
            if h1:
                return h1.text.strip()

            # Try og:title meta
            og_title = soup.find("meta", {"property": "og:title"})
            if og_title:
                return og_title.get("content", "").strip()

        return "Business"

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number using regex."""
        match = re.search(PHONE_PATTERN, text)
        if match:
            area, exchange, line = match.group(2), match.group(3), match.group(4)
            return f"+1{area}{exchange}{line}"
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address using regex."""
        match = re.search(EMAIL_PATTERN, text)
        return match.group(0) if match else None

    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address (simplified)."""
        # Look for common address patterns
        patterns = [
            r"\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir),?\s+[\w\s]+,\s+[A-Z]{2}",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_hours(self, text: str) -> dict:
        """Extract business hours."""
        hours = {
            "monday": None,
            "tuesday": None,
            "wednesday": None,
            "thursday": None,
            "friday": None,
            "saturday": None,
            "sunday": None,
        }

        day_map = {
            "mon": "monday",
            "tue": "tuesday",
            "wed": "wednesday",
            "thu": "thursday",
            "fri": "friday",
            "sat": "saturday",
            "sun": "sunday",
        }

        # Look for patterns like "Mon-Fri 9-5"
        matches = re.finditer(
            r"(mon|tue|wed|thu|fri|sat|sun)(?:day|.)?(?:\s*-\s*)?(?:mon|tue|wed|thu|fri|sat|sun)?(?:day|.)?\s*[:\s]*(\d{1,2}):?(\d{2})?\s*(?:am|pm)?\s*-\s*(\d{1,2}):?(\d{2})?\s*(?:am|pm)?",
            text,
            re.IGNORECASE,
        )

        for match in matches:
            day_abbr = match.group(1).lower()[:3]
            if day_abbr in day_map:
                day = day_map[day_abbr]
                start_hour = match.group(2)
                end_hour = match.group(4)
                hours[day] = f"{start_hour}:00-{end_hour}:00"

        return hours

    def _extract_services(self) -> list[dict]:
        """Extract services/products offered."""
        services = []

        # Look for service sections
        for content in self.content.values():
            soup = content["soup"]

            # Find service/product items
            for section in soup.find_all(["div", "section"]):
                # Check if this looks like a service listing
                if any(
                    keyword in section.get_text().lower()
                    for keyword in ["service", "product", "offering", "course"]
                ):
                    # Extract items
                    for item in section.find_all(["h3", "h4", "li"]):
                        name = item.get_text().strip()
                        # Try to find description nearby
                        desc_elem = item.find_next(["p", "div"])
                        description = (
                            desc_elem.get_text().strip() if desc_elem else ""
                        )

                        if name:
                            services.append(
                                {
                                    "name": name,
                                    "description": description[:200],  # First 200 chars
                                    "price": self._extract_price_near(item),
                                }
                            )

        return services[:10]  # Limit to 10 services

    def _extract_pricing(self) -> list[dict]:
        """Extract pricing information."""
        pricing = []
        seen = set()

        # Find all prices mentioned
        for content in self.content.values():
            text = content["text"]
            matches = re.finditer(PRICE_PATTERN, text)

            for match in matches:
                price_str = match.group(0)
                if price_str not in seen:
                    # Try to extract context
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()

                    # Extract item name from context
                    item_name = context.split("\n")[0][:100]

                    pricing.append({"item": item_name, "price": price_str})
                    seen.add(price_str)

        return pricing[:10]  # Limit to 10 pricing tiers

    def _extract_faqs(self) -> list[dict]:
        """Extract FAQ items."""
        faqs = []

        for content in self.content.values():
            soup = content["soup"]

            # Look for FAQ sections
            faq_section = soup.find(["section", "div"], string=re.compile("faq", re.I))

            if faq_section:
                # Extract Q&A pairs
                for item in faq_section.find_all(["dt", "div"]):
                    q_text = item.get_text().strip()
                    a_elem = item.find_next(["dd", "div"])
                    a_text = a_elem.get_text().strip() if a_elem else ""

                    if q_text and a_text:
                        faqs.append({"question": q_text[:150], "answer": a_text[:300]})

        return faqs[:5]  # Limit to 5 FAQs

    def _extract_social_media(self) -> dict:
        """Extract social media links."""
        social = {}
        platforms = ["facebook", "instagram", "twitter", "linkedin", "youtube"]

        for content in self.content.values():
            soup = content["soup"]

            for link in soup.find_all("a", href=True):
                href = link["href"].lower()
                for platform in platforms:
                    if platform in href and platform not in social:
                        social[platform] = link["href"]

        return social

    def _extract_description(self) -> str:
        """Extract business description."""
        for content in self.content.values():
            soup = content["soup"]

            # Try og:description meta
            og_desc = soup.find("meta", {"property": "og:description"})
            if og_desc:
                return og_desc.get("content", "").strip()

            # Try meta description
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc:
                return meta_desc.get("content", "").strip()

            # Try first paragraph
            p = soup.find("p")
            if p:
                return p.get_text().strip()[:300]

        return ""

    def _extract_price_near(self, element) -> Optional[str]:
        """Extract price near an element."""
        text = element.get_text()
        match = re.search(PRICE_PATTERN, text)
        return match.group(0) if match else None

    def _build_ai_context(
        self,
        business: dict,
        description: str,
        services: list[dict],
        pricing: list[dict],
    ) -> str:
        """Build formatted context for AI system prompt."""
        lines = []

        # Business basics
        lines.append(f"Business: {business['name']}")
        if business["phone"]:
            lines.append(f"Phone: {business['phone']}")
        if business["email"]:
            lines.append(f"Email: {business['email']}")
        if business["address"]:
            lines.append(f"Address: {business['address']}")

        # Hours
        if any(business["hours"].values()):
            lines.append("Hours of Operation:")
            for day, hours in business["hours"].items():
                if hours:
                    lines.append(f"  {day.capitalize()}: {hours}")

        # Description
        if description:
            lines.append(f"\nAbout: {description}")

        # Services
        if services:
            lines.append("\nServices/Products:")
            for svc in services[:5]:
                lines.append(f"  - {svc['name']}")
                if svc.get("description"):
                    lines.append(f"    {svc['description'][:100]}")

        # Pricing
        if pricing:
            lines.append("\nPricing:")
            for price in pricing[:3]:
                lines.append(f"  - {price['item']}: {price['price']}")

        return "\n".join(lines)


async def scrape_business_website(url: str, tenant_id: str) -> dict:
    """
    Scrape business website (main entry point).

    Args:
        url: Website URL
        tenant_id: Tenant ID (for logging)

    Returns:
        Scraped business data
    """
    scraper = BusinessScraper()
    result = await scraper.scrape(url)
    logger.info(f"Scrape complete for tenant {tenant_id}: {result['status']}")
    return result
