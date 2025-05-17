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
            {"name": "product_id", "selector": "a[href*='/dp/']", "type": "attribute", "attribute": "href", "transform": "match:/dp\/(\\w+)/"},
            {"name": "rank", "selector": ".zg-bdg-text, .zg-badge-text", "type": "text"},
            {"name": "product_name", "selector": "._p13n-zg-list-grid-desktop_style_productName__3CmSj, .p13n-sc-truncate, .a-size-medium", "type": "text"},
            {"name": "discounted_price", "selector": "._p13n-zg-list-grid-desktop_price_p13n-sc-price__3mJ9Z, .p13n-sc-price, .a-color-price", "type": "text"},
            {"name": "actual_price", "selector": ".a-text-price, .a-price[data-a-strike=true]", "type": "text"},
            {"name": "discount_percentage", "selector": ".a-color-secondary:contains('%')", "type": "text"},
            {"name": "rating", "selector": ".a-icon-alt", "type": "text"},
            {"name": "review_count", "selector": ".a-size-small[href*='#customerReviews'], .a-size-small", "type": "text"},
            {"name": "category", "selector": ".zg-item-category, #zg-left-col .zg_selected", "type": "text"},
            {"name": "about_product", "selector": ".a-row .a-size-small:not([href])", "type": "text"},
            {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"},
            {"name": "product_link", "selector": "a[href*='/dp/']", "type": "attribute", "attribute": "href"},
            {"name": "seller", "selector": ".a-size-small:contains('by ')", "type": "text"},
            {"name": "badge", "selector": ".a-badge", "type": "text"},
            {"name": "bestseller_category", "selector": ".a-badge-supplementary-text, .p13n-sc-sub-text", "type": "text"},
            {"name": "is_prime", "selector": ".a-icon-prime", "type": "exists"}
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
            - Product ID (from the URL)
            - Rank number
            - Product name
            - Discounted price (if available)
            - Actual price (if available)
            - Discount percentage (if available)
            - Rating (if available)
            - Number of reviews (if available)
            - Category
            - About product (short description if available)
            - Image URL
            - Product URL
            - Seller/brand name
            - Any badges (like "Amazon's Choice", "Best Seller")
            - Whether it has Prime shipping
            - Bestseller category (if available)

            Return as a JSON array of products with all available fields.
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
            {"name": "product_id", "selector": "a[href*='/dp/']", "type": "attribute", "attribute": "href", "transform": "match:/dp\/(\\w+)/"},
            {"name": "product_name", "selector": ".p13n-sc-truncate, .a-size-medium", "type": "text"},
            {"name": "discounted_price", "selector": ".p13n-sc-price, .a-color-price", "type": "text"},
            {"name": "actual_price", "selector": ".a-text-price, .a-price[data-a-strike=true]", "type": "text"},
            {"name": "percent_change", "selector": ".zg-percent-change, .p13n-sc-price-change", "type": "text"},
            {"name": "previous_rank", "selector": ".zg-badge-text2", "type": "text"},
            {"name": "current_rank", "selector": ".zg-badge-text", "type": "text"},
            {"name": "rating", "selector": ".a-icon-alt", "type": "text"},
            {"name": "review_count", "selector": ".a-size-small[href*='#customerReviews'], .a-size-small", "type": "text"},
            {"name": "category", "selector": ".zg-item-category, #zg-left-col .zg_selected", "type": "text"},
            {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"},
            {"name": "product_link", "selector": "a[href*='/dp/']", "type": "attribute", "attribute": "href"},
            {"name": "seller", "selector": ".a-size-small:contains('by ')", "type": "text"},
            {"name": "badge", "selector": ".a-badge", "type": "text"},
            {"name": "is_prime", "selector": ".a-icon-prime", "type": "exists"}
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
            {"name": "product_id", "selector": "a[href*='/dp/']", "type": "attribute", "attribute": "href", "transform": "match:/dp\/(\\w+)/"},
            {"name": "rank", "selector": ".zg-badge-text", "type": "text"},
            {"name": "product_name", "selector": ".p13n-sc-truncate, .a-size-medium", "type": "text"},
            {"name": "discounted_price", "selector": ".p13n-sc-price, .a-color-price", "type": "text"},
            {"name": "actual_price", "selector": ".a-text-price, .a-price[data-a-strike=true]", "type": "text"},
            {"name": "discount_percentage", "selector": ".a-color-secondary:contains('%')", "type": "text"},
            {"name": "release_date", "selector": ".zg-release-date", "type": "text"},
            {"name": "rating", "selector": ".a-icon-alt", "type": "text"},
            {"name": "review_count", "selector": ".a-size-small[href*='#customerReviews'], .a-size-small", "type": "text"},
            {"name": "category", "selector": ".zg-item-category, #zg-left-col .zg_selected", "type": "text"},
            {"name": "image_url", "selector": "img", "type": "attribute", "attribute": "src"},
            {"name": "product_link", "selector": "a[href*='/dp/']", "type": "attribute", "attribute": "href"},
            {"name": "seller", "selector": ".a-size-small:contains('by ')", "type": "text"},
            {"name": "badge", "selector": ".a-badge", "type": "text"},
            {"name": "bestseller_category", "selector": ".a-badge-supplementary-text, .p13n-sc-sub-text", "type": "text"},
            {"name": "is_prime", "selector": ".a-icon-prime", "type": "exists"}
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

async def scrape_product_details(crawler, product_urls, category_name):
    """Scrape detailed information from product pages"""
    
    # Schema for product detail extraction
    product_detail_schema = {
        "name": "Amazon Product Details",
        "baseSelector": "body",  # Tüm sayfa için baseSelector ekledik
        "fields": [
            {"name": "product_id", "selector": "input[name='ASIN']", "type": "attribute", "attribute": "value"},
            {"name": "product_name", "selector": "#productTitle", "type": "text"},
            {"name": "brand", "selector": "#bylineInfo", "type": "text"},
            {"name": "description", "selector": "#productDescription p, #feature-bullets .a-list-item", "type": "text", "multiple": True},
            {"name": "technical_details", "selector": "#productDetails_techSpec_section_1 tr", "type": "text", "multiple": True},
            {"name": "product_info", "selector": "#productDetails_detailBullets_sections1 tr", "type": "text", "multiple": True},
            {"name": "dimensions", "selector": "tr:contains('Dimensions'), tr:contains('Product Dimensions')", "type": "text"},
            {"name": "weight", "selector": "tr:contains('Weight'), tr:contains('Item Weight')", "type": "text"},
            {"name": "availability", "selector": "#availability", "type": "text"},
            {"name": "shipping_info", "selector": "#deliveryMessageMirId", "type": "text"},
            {"name": "sold_by", "selector": "#merchant-info", "type": "text"},
            {"name": "bestseller_rank", "selector": "tr:contains('Best Sellers Rank')", "type": "text"},
            {"name": "customer_questions", "selector": "#askATFLink .a-size-base", "type": "text"},
            {"name": "warranty", "selector": "#warranty-information-row span", "type": "text"},
            {"name": "variations", "selector": ".a-row.a-spacing-micro .a-form-label", "type": "text", "multiple": True},
            {"name": "related_products", "selector": "#sp_detail .a-carousel-card h2 span", "type": "text", "multiple": True},
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(product_detail_schema)
    
    # Limit the number of product pages to scrape
    max_products_to_scrape = min(5, len(product_urls))
    sample_urls = product_urls[:max_products_to_scrape]
    
    results = []
    for url in sample_urls:
        try:
            # Ensure URL is absolute
            if url.startswith('/'):
                url = f"https://www.amazon.com{url}"
                
            # Extract product ID from URL if possible
            import re
            product_id = None
            match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if match:
                product_id = match.group(1)
            
            logger.info(f"Scraping product details from: {url}")
            
            config = CrawlerRunConfig(
                extraction_strategy=extraction_strategy,
                wait_for="#productTitle",
                page_timeout=30000
            )
            
            result = await crawler.arun(url=url, config=config)
            
            if result.success and result.extracted_content:
                product_data = json.loads(result.extracted_content)
                if product_id and not product_data.get("product_id"):
                    product_data["product_id"] = product_id
                product_data["category"] = category_name
                product_data["product_url"] = url
                results.append(product_data)
                logger.info(f"Successfully extracted detailed data for product")
            else:
                logger.warning(f"Failed to extract product details from {url}")
        
        except Exception as e:
            logger.error(f"Error scraping product details from {url}: {str(e)}")
    
    return results

async def scrape_product_reviews(crawler, product_id, product_url):
    """Scrape reviews for a product"""
    
    # Extract the product ID from the URL if not provided
    if not product_id and product_url:
        import re
        match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
        if match:
            product_id = match.group(1)
    
    if not product_id:
        logger.warning("Could not determine product ID for review scraping")
        return []
    
    # Construct reviews URL
    reviews_url = f"https://www.amazon.com/product-reviews/{product_id}"
    
    # Schema for review extraction
    reviews_schema = {
        "name": "Amazon Product Reviews",
        "baseSelector": "#cm_cr-review_list .review",
        "fields": [
            {"name": "review_id", "selector": "[data-hook='review']", "type": "attribute", "attribute": "id"},
            {"name": "review_title", "selector": "[data-hook='review-title']", "type": "text"},
            {"name": "review_rating", "selector": ".review-rating", "type": "text"},
            {"name": "review_date", "selector": "[data-hook='review-date']", "type": "text"},
            {"name": "verified_purchase", "selector": "[data-hook='avp-badge']", "type": "exists"},
            {"name": "reviewer_name", "selector": ".a-profile-name", "type": "text"},
            {"name": "review_text", "selector": ".review-text-content span", "type": "text"},
            {"name": "helpful_votes", "selector": "[data-hook='helpful-vote-statement']", "type": "text"},
            {"name": "review_images", "selector": "[data-hook='review-image-gallery'] img", "type": "attribute", "attribute": "src", "multiple": True},
            {"name": "review_video", "selector": "[data-hook='review-video-gallery'] video", "type": "exists"}
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(reviews_schema)
    
    config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="#cm_cr-review_list",
        js_code="""
            // Click "See more reviews" button if available
            function clickMoreReviews() {
                const moreButton = document.querySelector('.a-pagination .a-last a');
                if (moreButton) {
                    moreButton.click();
                    return true;
                }
                return false;
            }
            
            // Try to load a few pages of reviews
            let pageCount = 0;
            const maxPages = 1;  // Reduced to just one page to avoid timeout
            
            function loadMoreReviews() {
                if (pageCount < maxPages && clickMoreReviews()) {
                    pageCount++;
                    setTimeout(loadMoreReviews, 2000);
                }
            }
            
            // Start loading more reviews
            setTimeout(loadMoreReviews, 1000);
        """,
        page_timeout=30000  # Reduced timeout to avoid hanging
    )
    
    try:
        logger.info(f"Scraping reviews for product ID: {product_id}")
        result = await crawler.arun(url=reviews_url, config=config)
        
        if result.success and result.extracted_content:
            reviews = json.loads(result.extracted_content)
            logger.info(f"Successfully extracted {len(reviews)} reviews for product ID: {product_id}")
            return reviews
        else:
            logger.warning(f"Failed to extract reviews for product ID: {product_id}")
            return []
            
    except Exception as e:
        logger.error(f"Error scraping reviews for product ID {product_id}: {str(e)}")
        return []

async def analyze_product_sentiment(reviews):
    """Analyze sentiment from product reviews"""
    if not reviews:
        return {
            "sentiment_score": None,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "common_phrases": [],
            "review_count": 0
        }
    
    # Simple rating-based sentiment
    sentiment_scores = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for review in reviews:
        rating_text = review.get("review_rating", "")
        try:
            if "out of 5" in rating_text:
                rating = float(rating_text.split("out of")[0].strip())
                sentiment_scores.append(rating)
                
                if rating >= 4:
                    positive_count += 1
                elif rating <= 2:
                    negative_count += 1
                else:
                    neutral_count += 1
        except:
            pass
    
    # Calculate average sentiment
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None
    
    # Extract common phrases (simplified)
    all_review_text = " ".join([review.get("review_text", "") for review in reviews])
    words = all_review_text.lower().split()
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Skip short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top 10 most common words
    common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "sentiment_score": avg_sentiment,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "common_phrases": common_words,
        "review_count": len(reviews)
    }

async def scrape_competitive_products(crawler, product_name, category_name):
    """Scrape competitive products for a given product"""
    
    # Create a search query based on product name and category
    # Using partial product name to get more relevant competitors
    search_terms = product_name.split()[:3]  # Use first 3 words of product name
    search_query = f"{' '.join(search_terms)} {category_name}".replace(" ", "+")
    search_url = f"https://www.amazon.com/s?k={search_query}"
    
    # Schema for competitive products
    competitive_schema = {
        "name": "Amazon Competitors",
        "baseSelector": "[data-component-type='s-search-result']",
        "fields": [
            {"name": "product_name", "selector": "h2 .a-link-normal", "type": "text"},
            {"name": "product_id", "selector": "[data-asin]", "type": "attribute", "attribute": "data-asin"},
            {"name": "price", "selector": ".a-price .a-offscreen", "type": "text"},
            {"name": "rating", "selector": ".a-icon-star-small", "type": "text"},
            {"name": "review_count", "selector": ".a-size-small .a-link-normal", "type": "text"},
            {"name": "badge", "selector": ".a-badge-text", "type": "text"},
            {"name": "is_prime", "selector": ".a-icon-prime", "type": "exists"},
            {"name": "is_sponsored", "selector": ".a-color-secondary:contains('Sponsored')", "type": "exists"},
            {"name": "image_url", "selector": ".s-image", "type": "attribute", "attribute": "src"},
            {"name": "product_link", "selector": "h2 .a-link-normal", "type": "attribute", "attribute": "href"}
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(competitive_schema)
    
    config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="[data-component-type='s-search-result']",
        page_timeout=30000
    )
    
    try:
        logger.info(f"Searching for competitive products: {search_query}")
        result = await crawler.arun(url=search_url, config=config)
        
        if result.success and result.extracted_content:
            competitors = json.loads(result.extracted_content)
            logger.info(f"Successfully extracted {len(competitors)} competitive products")
            
            # Filter out the original product and sponsored products
            filtered_competitors = [
                comp for comp in competitors
                if comp.get("product_name") and not comp.get("is_sponsored", False)
            ]
            
            return filtered_competitors[:10]  # Return top 10 competitors
        else:
            logger.warning(f"Failed to extract competitive products for {product_name}")
            return []
    
    except Exception as e:
        logger.error(f"Error scraping competitive products for {product_name}: {str(e)}")
        return []

def simulate_price_history(product_id, current_price):
    """Simulate historical price data for a product"""
    if not current_price:
        return []
        
    try:
        # Extract numeric price
        import re
        price_match = re.search(r'[\d,]+\.\d+', current_price)
        if not price_match:
            return []
            
        base_price = float(price_match.group(0).replace(',', ''))
        
        # Generate simulated price history for the last 30 days
        import random
        from datetime import datetime, timedelta
        
        today = datetime.now()
        price_history = []
        
        # Create price variations (10% up or down from current price)
        variation_percent = 0.10
        min_price = base_price * (1 - variation_percent)
        max_price = base_price * (1 + variation_percent)
        
        # Add some seasonal trends and patterns
        for i in range(30):
            day = today - timedelta(days=i)
            
            # Create some weekly patterns (weekends slightly higher)
            weekday_factor = 1.02 if day.weekday() >= 5 else 1.0
            
            # Add some randomness
            random_factor = random.uniform(0.97, 1.03)
            
            # Price tends to decrease over time (older prices slightly higher)
            time_factor = 1 + (i * 0.001)
            
            # Combine factors
            daily_price = base_price * weekday_factor * random_factor * time_factor
            
            # Keep within bounds
            daily_price = max(min_price, min(max_price, daily_price))
            
            price_history.append({
                "date": day.strftime("%Y-%m-%d"),
                "price": round(daily_price, 2)
            })
            
        return price_history
    
    except Exception as e:
        logger.error(f"Error generating price history: {str(e)}")
        return []

async def analyze_pricing_strategy(products_list):
    """Analyze pricing strategies across products"""
    
    if not products_list:
        return {}
        
    try:
        price_points = []
        discount_rates = []
        prime_prices = []
        non_prime_prices = []
        
        for product in products_list:
            # Extract price data
            price_text = product.get("discounted_price", "")
            original_price_text = product.get("actual_price", "")
            has_prime = product.get("is_prime", False)
            
            # Extract numeric prices
            import re
            price_match = re.search(r'[\d,]+\.\d+', price_text) if price_text else None
            original_match = re.search(r'[\d,]+\.\d+', original_price_text) if original_price_text else None
            
            if price_match:
                price = float(price_match.group(0).replace(',', ''))
                price_points.append(price)
                
                # Separate prime and non-prime prices
                if has_prime:
                    prime_prices.append(price)
                else:
                    non_prime_prices.append(price)
                
                # Calculate discount rate if both prices available
                if original_match:
                    original_price = float(original_match.group(0).replace(',', ''))
                    if original_price > 0:
                        discount = (original_price - price) / original_price * 100
                        discount_rates.append(discount)
        
        # Calculate statistics
        analysis = {}
        
        if price_points:
            analysis["price_range"] = {
                "min": min(price_points),
                "max": max(price_points),
                "avg": sum(price_points) / len(price_points),
                "median": sorted(price_points)[len(price_points) // 2]
            }
            
        if discount_rates:
            analysis["discount_analysis"] = {
                "min_discount": min(discount_rates),
                "max_discount": max(discount_rates),
                "avg_discount": sum(discount_rates) / len(discount_rates)
            }
            
        # Compare Prime vs non-Prime pricing
        if prime_prices and non_prime_prices:
            prime_avg = sum(prime_prices) / len(prime_prices)
            non_prime_avg = sum(non_prime_prices) / len(non_prime_prices)
            
            analysis["prime_vs_non_prime"] = {
                "prime_avg_price": prime_avg,
                "non_prime_avg_price": non_prime_avg,
                "price_difference": prime_avg - non_prime_avg,
                "percentage_difference": (prime_avg - non_prime_avg) / non_prime_avg * 100 if non_prime_avg else 0
            }
            
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing pricing strategy: {str(e)}")
        return {}

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
            
            # Only use specific categories to reduce time and errors
            filtered_categories = []
            target_categories = ["Electronics", "Books", "Toys & Games"]
            
            for cat in categories:
                if any(target in cat["name"] for target in target_categories):
                    filtered_categories.append(cat)
            
            if not filtered_categories:
                # If filtering didn't work, use a few categories
                filtered_categories = categories[:3] if len(categories) > 3 else categories
                
            logger.info(f"Scraping only these categories: {[c['name'] for c in filtered_categories]}")

            # Scrape different data types
            bestsellers = await scrape_amazon_bestsellers(crawler, filtered_categories)
            trends = await scrape_amazon_product_trends(crawler)
            new_releases = await scrape_amazon_new_releases(crawler)
            
            # Extract product URLs from bestsellers for detailed scraping
            product_urls = []
            all_product_details = {}
            
            for category_name, products in bestsellers.items():
                category_product_urls = []
                for product in products:
                    # Extract any missing product IDs from URLs
                    if "product_link" in product and product["product_link"]:
                        product_url = product["product_link"]
                        # Ensure URL is absolute
                        if product_url.startswith('/'):
                            product_url = f"https://www.amazon.com{product_url}"
                        
                        # Extract product ID from URL if not already present
                        if not product.get("product_id"):
                            import re
                            match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
                            if match:
                                product["product_id"] = match.group(1)
                        
                        category_product_urls.append(product_url)
                
                # Save product names for later use
                for i, product in enumerate(products):
                    if not product.get("product_name") and i < len(category_product_urls):
                        # Extract product name from URL if possible
                        url_parts = category_product_urls[i].split('/')
                        if len(url_parts) > 3:
                            product_name_part = url_parts[-2] if url_parts[-1].startswith('ref=') else url_parts[-1]
                            product_name_part = product_name_part.split('?')[0]
                            product_name = product_name_part.replace('-', ' ').title()
                            product["product_name"] = product_name
                
                if category_product_urls:
                    # Sample a few products from each category for detailed scraping
                    logger.info(f"Scraping detailed product info for category: {category_name}")
                    category_details = await scrape_product_details(crawler, category_product_urls, category_name)
                    if category_details:
                        all_product_details[category_name] = category_details
            
            # Sample a few products for review analysis
            all_reviews = {}
            sentiment_analysis = {}
            
            # Use a limited sample of products for review analysis
            review_sample_count = 0
            max_review_samples = 3  # Reduced to 3 to avoid timeouts
            
            for category_name, products in bestsellers.items():
                if review_sample_count >= max_review_samples:
                    break
                    
                for product in products[:1]:  # Only analyze the first product in each category
                    if review_sample_count >= max_review_samples:
                        break
                        
                    product_id = product.get("product_id")
                    product_url = product.get("product_link")
                    product_name = product.get("product_name", "Unknown Product")
                    
                    # Extract product ID from URL if not already present
                    if not product_id and product_url:
                        import re
                        match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
                        if match:
                            product_id = match.group(1)
                            product["product_id"] = product_id
                    
                    # Ensure URL is absolute
                    if product_url and product_url.startswith('/'):
                        product_url = f"https://www.amazon.com{product_url}"
                    
                    if product_id:  # Only try to scrape if we have a valid product_id
                        logger.info(f"Analyzing reviews for product: {product_name}")
                        reviews = await scrape_product_reviews(crawler, product_id, product_url)
                        
                        if reviews:
                            review_sample_count += 1
                            product_key = f"{category_name}_{product_id}"
                            all_reviews[product_key] = reviews
                            
                            # Analyze sentiment
                            sentiment = await analyze_product_sentiment(reviews)
                            sentiment_analysis[product_key] = {
                                "product_name": product_name,
                                "category": category_name,
                                "analysis": sentiment
                            }
            
            # Competitive analysis for selected products
            competitive_analysis = {}
            price_history_data = {}
            
            # Sample a few products for competitive analysis
            comp_sample_count = 0
            max_comp_samples = 3  # Reduced to 3 to avoid timeouts
            
            logger.info("Starting competitive analysis for selected products")
            
            for category_name, products in bestsellers.items():
                if comp_sample_count >= max_comp_samples:
                    break
                    
                for product in products[:1]:  # Only analyze the first product in each category
                    if comp_sample_count >= max_comp_samples:
                        break
                        
                    product_id = product.get("product_id")
                    product_name = product.get("product_name", "Unknown Product")
                    current_price = product.get("discounted_price")
                    
                    if product_id and product_name and product_name != "Unknown Product":
                        logger.info(f"Analyzing competition for product: {product_name}")
                        
                        # Get competitive products
                        competitors = await scrape_competitive_products(crawler, product_name, category_name)
                        
                        if competitors:
                            comp_sample_count += 1
                            product_key = f"{category_name}_{product_id}"
                            
                            # Generate price history data (simulated)
                            price_history = simulate_price_history(product_id, current_price)
                            if price_history:
                                price_history_data[product_key] = {
                                    "product_name": product_name,
                                    "category": category_name,
                                    "history": price_history
                                }
                                
                            # Analyze pricing strategy across competitors
                            pricing_analysis = await analyze_pricing_strategy(competitors)
                            
                            # Store competitive analysis
                            competitive_analysis[product_key] = {
                                "product_name": product_name,
                                "category": category_name,
                                "competitors": competitors,
                                "pricing_analysis": pricing_analysis
                            }

            # Combine results for analysis
            combined_data = {
                "bestsellers": bestsellers,
                "trends": trends,
                "new_releases": new_releases,
                "product_details": all_product_details,
                "reviews": all_reviews,
                "sentiment_analysis": sentiment_analysis,
                "competitive_analysis": competitive_analysis,
                "price_history": price_history_data,
                "timestamp": asyncio.get_event_loop().time(),
                "categories_scraped": [cat["name"] for cat in filtered_categories]
            }

            # Save to JSON files
            with open("amazon_bestsellers.json", "w", encoding="utf-8") as f:
                json.dump(bestsellers, f, indent=2, ensure_ascii=False)

            with open("amazon_trends.json", "w", encoding="utf-8") as f:
                json.dump(trends, f, indent=2, ensure_ascii=False)

            with open("amazon_new_releases.json", "w", encoding="utf-8") as f:
                json.dump(new_releases, f, indent=2, ensure_ascii=False)
                
            with open("amazon_product_details.json", "w", encoding="utf-8") as f:
                json.dump(all_product_details, f, indent=2, ensure_ascii=False)

            with open("amazon_product_reviews.json", "w", encoding="utf-8") as f:
                json.dump(all_reviews, f, indent=2, ensure_ascii=False)
                
            with open("amazon_sentiment_analysis.json", "w", encoding="utf-8") as f:
                json.dump(sentiment_analysis, f, indent=2, ensure_ascii=False)

            with open("amazon_competitive_analysis.json", "w", encoding="utf-8") as f:
                json.dump(competitive_analysis, f, indent=2, ensure_ascii=False)
                
            with open("amazon_price_history.json", "w", encoding="utf-8") as f:
                json.dump(price_history_data, f, indent=2, ensure_ascii=False)

            with open("amazon_sales_data.json", "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)

            # Print summary
            logger.info("Amazon sales data scraping complete!")
            logger.info(f"Scraped {len(bestsellers)} bestseller categories")
            logger.info(f"Scraped {len(trends)} trend categories")
            logger.info(f"Scraped {len(new_releases)} new release categories")
            logger.info(f"Scraped {len(all_product_details)} categories with detailed product information")
            logger.info(f"Analyzed reviews for {len(all_reviews)} products")
            logger.info(f"Performed competitive analysis for {len(competitive_analysis)} products")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())