import asyncio
import json
import logging
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def discover_amazon_categories(crawler):
    """Dynamically discover Amazon categories available for bestsellers"""

    # Use a more general schema to extract category links from the main bestsellers page
    category_schema = {
        "name": "Amazon Categories",
        "baseSelector": "#zg-left-col li",
        "fields": [
            {"name": "category_name", "selector": "a", "type": "text"},
            {"name": "category_url", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(category_schema)
    config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="#zg-left-col",
        page_timeout=30000
    )

    result = await crawler.arun(url="https://www.amazon.com/Best-Sellers/zgbs/", config=config)

    categories = []
    if result.success and result.extracted_content:
        data = json.loads(result.extracted_content)
        for item in data:
            if "category_url" in item and "category_name" in item:
                categories.append({
                    "name": item["category_name"].strip(),
                    "url": item["category_url"]
                })

    # Add fallback categories in case dynamic discovery fails
    if not categories:
        fallback_categories = [
            {"name": "All Categories", "url": "https://www.amazon.com/Best-Sellers/zgbs/"},
            {"name": "Electronics", "url": "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"},
            {"name": "Books", "url": "https://www.amazon.com/Best-Sellers-Books/zgbs/books/"},
            {"name": "Clothing", "url": "https://www.amazon.com/Best-Sellers-Clothing-Shoes-Jewelry/zgbs/fashion/"},
            {"name": "Home & Kitchen", "url": "https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden/"},
            {"name": "Toys & Games", "url": "https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games/"},
            {"name": "Beauty", "url": "https://www.amazon.com/Best-Sellers-Beauty/zgbs/beauty/"},
            {"name": "Health & Household", "url": "https://www.amazon.com/Best-Sellers-Health-Personal-Care/zgbs/hpc/"},
            {"name": "Sports & Outdoors", "url": "https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods/"},
            {"name": "Pet Supplies", "url": "https://www.amazon.com/Best-Sellers-Pet-Supplies/zgbs/pet-supplies/"}
        ]
        categories = fallback_categories

    logger.info(f"Discovered {len(categories)} Amazon categories")
    return categories

async def scrape_amazon_bestsellers(crawler, categories):
    """Scrape bestsellers from multiple Amazon categories"""

    # Adaptive schema for different Amazon category layouts
    bestseller_schema = {
        "name": "Amazon Bestsellers",
        "baseSelector": ".p13n-sc-uncoverable-faceout, .a-carousel-card, .zg-item",  # Multiple selectors to match different layouts
        "fields": [
            {"name": "rank", "selector": ".zg-bdg-text, .zg-badge-text", "type": "text"},
            {"name": "product_name", "selector": "._p13n-zg-list-grid-desktop_style_productName__3CmSj, .p13n-sc-truncate, .a-size-medium", "type": "text"},
            {"name": "price", "selector": "._p13n-zg-list-grid-desktop_price_p13n-sc-price__3mJ9Z, .p13n-sc-price, .a-color-price", "type": "text"},
            {"name": "rating", "selector": ".a-icon-alt", "type": "text"},
            {"name": "review_count", "selector": ".a-size-small[href*='#customerReviews'], .a-size-small", "type": "text"},
            {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(bestseller_schema)
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for=".p13n-sc-uncoverable-faceout, .a-carousel-card, .zg-item",  # Wait for any product card type
        js_code="""
            // Scroll down to load all products (for lazy loading)
            function autoScroll() {
                window.scrollBy(0, 300);
                if(window.scrollY + window.innerHeight >= document.body.scrollHeight) {
                    clearInterval(scrollInterval);
                }
            }
            let scrollInterval = setInterval(autoScroll, 500);

            // Click "Next page" button if available
            setTimeout(() => {
                const nextButton = document.querySelector('.a-last a, .a-pagination .a-last');
                if (nextButton) nextButton.click();
            }, 5000);
        """,
        page_timeout=60000
    )

    results = {}
    for category in categories:
        try:
            logger.info(f"Scraping bestsellers for category: {category['name']}")
            result = await crawler.arun(url=category['url'], config=run_config)

            if result.success and result.extracted_content:
                category_data = json.loads(result.extracted_content)
                logger.info(f"Successfully extracted {len(category_data)} products from {category['name']}")
                results[category['name']] = category_data
            else:
                logger.warning(f"Failed to extract data from {category['name']}")

                # Fallback to LLM extraction if structured extraction fails
                if result.html:
                    llm_result = await extract_with_llm(crawler, category['url'], category['name'])
                    if llm_result:
                        results[category['name']] = llm_result

        except Exception as e:
            logger.error(f"Error scraping {category['name']}: {str(e)}")

    return results

async def extract_with_llm(crawler, url, category_name):
    """Fallback method using LLM extraction for complex layouts"""
    try:
        # Skip LLM extraction if no API key is available
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            logger.warning("No OpenAI API key found for LLM extraction fallback")
            return None

        llm_strategy = LLMExtractionStrategy(
            llm_config={
                "provider": "openai/gpt-3.5-turbo",
                "api_token": openai_key
            },
            instruction=f"""
            Extract top bestselling products from this Amazon {category_name} page.
            For each product, extract:
            - Rank number
            - Product name
            - Price (if available)
            - Rating (if available)
            - Number of reviews (if available)

            Return as a JSON array of products.
            """,
            extraction_type="block",
            chunk_token_threshold=3000
        )

        config = CrawlerRunConfig(
            extraction_strategy=llm_strategy,
            page_timeout=60000
        )

        result = await crawler.arun(url=url, config=config)
        if result.success and result.extracted_content:
            try:
                return json.loads(result.extracted_content)
            except json.JSONDecodeError:
                # If LLM didn't return proper JSON, try to parse it
                logger.warning("LLM didn't return proper JSON. Attempting to parse.")
                return {"raw_text": result.extracted_content}

    except Exception as e:
        logger.error(f"Error in LLM extraction for {category_name}: {str(e)}")

    return None

async def scrape_amazon_product_trends(crawler):
    """Scrape trending products (Movers & Shakers) from Amazon"""

    # Discover trend categories
    trend_categories = [
        {"name": "All Categories", "url": "https://www.amazon.com/gp/movers-and-shakers/"},
        {"name": "Electronics", "url": "https://www.amazon.com/gp/movers-and-shakers/electronics/"},
        {"name": "Books", "url": "https://www.amazon.com/gp/movers-and-shakers/books/"},
        {"name": "Toys & Games", "url": "https://www.amazon.com/gp/movers-and-shakers/toys-and-games/"},
        {"name": "Home & Kitchen", "url": "https://www.amazon.com/gp/movers-and-shakers/home-garden/"}
    ]

    trends_schema = {
        "name": "Amazon Trends",
        "baseSelector": ".zg-item, .a-carousel-card",
        "fields": [
            {"name": "product_name", "selector": ".p13n-sc-truncate, .a-size-medium", "type": "text"},
            {"name": "price", "selector": ".p13n-sc-price, .a-color-price", "type": "text"},
            {"name": "percent_change", "selector": ".zg-percent-change, .p13n-sc-price-change", "type": "text"},
            {"name": "previous_rank", "selector": ".zg-badge-text2", "type": "text"},
            {"name": "current_rank", "selector": ".zg-badge-text", "type": "text"},
            {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(trends_schema)
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for=".zg-item, .a-carousel-card",
        js_code="""
            // Scroll to load all content
            window.scrollTo(0, document.body.scrollHeight);

            // Click through carousel if present
            const interval = setInterval(() => {
                const nextButton = document.querySelector('.a-carousel-goto-nextpage');
                if (nextButton) {
                    nextButton.click();
                }
            }, 1000);

            // Clear interval after 15 seconds
            setTimeout(() => clearInterval(interval), 15000);
        """,
        page_timeout=60000
    )

    trend_results = {}
    for category in trend_categories:
        try:
            logger.info(f"Scraping trends for: {category['name']}")
            result = await crawler.arun(url=category['url'], config=run_config)

            if result.success and result.extracted_content:
                data = json.loads(result.extracted_content)
                logger.info(f"Successfully extracted {len(data)} trending products from {category['name']}")
                trend_results[category['name']] = data
        except Exception as e:
            logger.error(f"Error scraping trends for {category['name']}: {str(e)}")

    return trend_results

async def scrape_amazon_new_releases(crawler):
    """Scrape new releases from Amazon"""

    new_release_categories = [
        {"name": "All Categories", "url": "https://www.amazon.com/gp/new-releases/"},
        {"name": "Electronics", "url": "https://www.amazon.com/gp/new-releases/electronics/"},
        {"name": "Books", "url": "https://www.amazon.com/gp/new-releases/books/"}
    ]

    new_releases_schema = {
        "name": "Amazon New Releases",
        "baseSelector": ".zg-item, .a-carousel-card",
        "fields": [
            {"name": "rank", "selector": ".zg-badge-text", "type": "text"},
            {"name": "product_name", "selector": ".p13n-sc-truncate, .a-size-medium", "type": "text"},
            {"name": "price", "selector": ".p13n-sc-price, .a-color-price", "type": "text"},
            {"name": "release_date", "selector": ".zg-release-date", "type": "text"},
            {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(new_releases_schema)
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for=".zg-item, .a-carousel-card",
        page_timeout=60000
    )

    new_release_results = {}
    for category in new_release_categories:
        try:
            logger.info(f"Scraping new releases for: {category['name']}")
            result = await crawler.arun(url=category['url'], config=run_config)

            if result.success and result.extracted_content:
                data = json.loads(result.extracted_content)
                logger.info(f"Successfully extracted {len(data)} new releases from {category['name']}")
                new_release_results[category['name']] = data
        except Exception as e:
            logger.error(f"Error scraping new releases for {category['name']}: {str(e)}")

    return new_release_results

async def main():
    # Configure browser settings for maximum stealth
    browser_config = BrowserConfig(
        browser_mode='dedicated',  # Use a dedicated browser instance
        headless=False,  # Set to True for production
        verbose=True,
        # stealth_mode is not available in this version
        # Use user_agent_mode instead for stealth
        user_agent_mode='stealth',
        viewport_width=1920,
        viewport_height=1080,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    try:
        # Initialize crawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Discover categories
            categories = await discover_amazon_categories(crawler)

            # Scrape different data types
            bestsellers = await scrape_amazon_bestsellers(crawler, categories)
            trends = await scrape_amazon_product_trends(crawler)
            new_releases = await scrape_amazon_new_releases(crawler)

            # Combine results for analysis
            combined_data = {
                "bestsellers": bestsellers,
                "trends": trends,
                "new_releases": new_releases,
                "timestamp": asyncio.get_event_loop().time(),
                "categories_scraped": [cat["name"] for cat in categories]
            }

            # Save to JSON files
            with open("amazon_bestsellers.json", "w", encoding="utf-8") as f:
                json.dump(bestsellers, f, indent=2, ensure_ascii=False)

            with open("amazon_trends.json", "w", encoding="utf-8") as f:
                json.dump(trends, f, indent=2, ensure_ascii=False)

            with open("amazon_new_releases.json", "w", encoding="utf-8") as f:
                json.dump(new_releases, f, indent=2, ensure_ascii=False)

            with open("amazon_sales_data.json", "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)

            # Print summary
            logger.info("Amazon sales data scraping complete!")
            logger.info(f"Scraped {len(bestsellers)} bestseller categories")
            logger.info(f"Scraped {len(trends)} trend categories")
            logger.info(f"Scraped {len(new_releases)} new release categories")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())