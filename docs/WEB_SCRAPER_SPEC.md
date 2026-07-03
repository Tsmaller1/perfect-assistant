# Perfect Assistant — Web Scraper Specification

## Overview
The web scraper extracts structured business data from a company website and formats it as AI-usable context. It handles various website structures and gracefully extracts maximum relevant information.

## Extraction Targets

### Primary Data
| Field | Extraction Method | Priority | Example |
|-------|-------------------|----------|---------|
| Business Name | `<title>`, `<h1>`, meta tags | HIGH | "I10 Education" |
| Phone Number | regex `\+?1?\d{10}`, href="tel:" | HIGH | "+15551234567" |
| Address | "Contact" page, footer, schema.org | MEDIUM | "123 Main St, City, State" |
| Email | regex `\S+@\S+`, footer contact | MEDIUM | "info@company.com" |
| Hours of Operation | Contact page, homepage, footer | MEDIUM | "Mon-Fri 9-5, Sat 10-3" |
| Description | Meta description, About page, first paragraph | HIGH | "We offer educational services..." |
| Services/Products | Service pages, product listings | HIGH | [{name, description, price}, ...] |
| Pricing | Pricing page, product pages | MEDIUM | [{item, price, unit}, ...] |
| Social Media | Footer links | LOW | {facebook, instagram, linkedin, twitter} |
| Location/Map | Google Maps embed, address | LOW | {lat, lon} |

### Secondary Data (Context)
- FAQ content
- Testimonials/reviews
- Team members
- Certifications/accreditations
- Blog posts (recent titles)

## Scraping Strategy

### 1. Initial Reconnaissance
```
GET website homepage
Parse HTML with BeautifulSoup
Identify site structure (WordPress, Shopify, Custom, etc.)
Detect robots.txt restrictions
Check for sitemap.xml
```

### 2. Page Discovery
Crawl:
- `/` (homepage)
- `/about`, `/about-us`
- `/contact`, `/contact-us`
- `/services`, `/products`, `/pricing`
- `/faq`, `/faqs`, `/help`
- Menu links (up to depth 2)

Max pages: 20

### 3. Content Extraction

**Use BeautifulSoup to extract:**
- Text nodes (remove scripts, styles, ads)
- Structured data (schema.org JSON-LD)
- Meta tags (description, keywords, og:title, etc.)
- Links (contact forms, external services)
- Images (logo, hero images)

**Use Regex patterns for:**
- Phone numbers: `(\+?1?)[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{4}`
- Email: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Prices: `\$[\d,]+\.?\d{0,2}`
- Hours: patterns like "Mon-Fri 9-5", "M-F 9am-5pm"

## Output Format

```json
{
  "business": {
    "name": "I10 Education",
    "website": "https://i10education.com",
    "phone": "+15551234567",
    "email": "info@i10education.com",
    "address": "123 Main St, City, State",
    "hours": {
      "monday": "9:00-17:00",
      "tuesday": "9:00-17:00",
      "wednesday": "9:00-17:00",
      "thursday": "9:00-17:00",
      "friday": "9:00-17:00",
      "saturday": null,
      "sunday": null
    }
  },
  
  "description": "I10 Education provides professional development courses in technology and business.",
  
  "services": [
    {
      "name": "Python Programming",
      "description": "Beginner to advanced Python courses",
      "price": "$199",
      "duration": "4 weeks"
    },
    {
      "name": "Web Development",
      "description": "Full-stack web development with React and Node.js",
      "price": "$299",
      "duration": "8 weeks"
    }
  ],
  
  "pricing": [
    {"item": "Single Course", "price": "$199-$299"},
    {"item": "Monthly Subscription", "price": "$99/month"},
    {"item": "Corporate Training", "price": "Custom quote"}
  ],
  
  "faqs": [
    {
      "question": "Do you offer refunds?",
      "answer": "Yes, 30-day money-back guarantee if not satisfied."
    }
  ],
  
  "social_media": {
    "facebook": "https://facebook.com/i10education",
    "instagram": "https://instagram.com/i10education",
    "linkedin": "https://linkedin.com/company/i10education"
  },
  
  "ai_context": "I10 Education offers professional development courses including Python Programming ($199), Web Development ($299), and more. They are open Monday-Friday 9am-5pm. Contact them at +15551234567 or info@i10education.com. They offer a 30-day money-back guarantee on all courses."
}
```

## Error Handling

| Scenario | Action |
|----------|--------|
| Website down/timeout | Return empty profile, mark for retry |
| robots.txt blocks scraping | Use structured data only (JSON-LD, meta tags) |
| JavaScript-rendered content | Use Playwright (headless browser) |
| Rate limiting | Implement exponential backoff + delays |
| No phone number found | Mark as required, ask user to provide |
| No hours found | Default to business hours assumption ("9-5") |

## Timeout & Resource Limits

```
- Page load timeout: 10 seconds
- Total crawl timeout: 60 seconds
- Max pages: 20
- Max content per page: 500KB
- Max retries: 2
- Delay between requests: 1 second
```

## Dependencies

```python
beautifulsoup4>=4.12.0      # HTML parsing
playwright>=1.44.0          # JavaScript rendering (fallback)
httpx>=0.25.0               # Async HTTP client
python-dateutil>=2.8.2      # Date/time parsing
```

## Function Signature

```python
async def scrape_business_website(
    url: str,
    tenant_id: str,
    timeout: int = 60,
    max_pages: int = 20
) -> dict:
    """
    Scrape business website and extract structured data.
    
    Args:
        url: Website URL to scrape
        tenant_id: Business tenant ID
        timeout: Total scraping timeout (seconds)
        max_pages: Max pages to crawl
    
    Returns:
        {
            "status": "success|error",
            "data": {...},  # Extraction output JSON above
            "error": "...",
            "warnings": ["..."]
        }
    """
```

## Testing

```python
# Test URLs
test_cases = [
    "https://i10education.com",           # Educational
    "https://www.google.com",             # Large site
    "https://example.com",                # Minimal site
]

# Verify outputs
assert result["business"]["phone"] is not None
assert result["business"]["name"] is not None
assert result["ai_context"] is not None
```

## Performance

- Average time per website: 5-15 seconds
- Memory usage: ~50MB per concurrent crawl
- Success rate target: >95%
