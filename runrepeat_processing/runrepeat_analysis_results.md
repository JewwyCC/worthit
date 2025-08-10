# RunRepeat Website Structure Analysis

## Key Findings

### 1. Website Architecture
**RunRepeat is a JavaScript Single Page Application (SPA)** that loads data dynamically via JSON. The current scraper approach won't work because:

- The HTML contains no `li.product_list` elements with shoe data
- All shoe data is loaded dynamically via JavaScript 
- The data exists in JSON format embedded in `<script>` tags

### 2. Available Data Sources

#### A. JSON-LD Structured Data (Most Reliable)
Found in `<script type="application/ld+json">` tags:
```json
{
  "@context":"https://schema.org",
  "@type":"ItemList",
  "itemListElement":[
    {
      "@type":"ListItem",
      "position":1,
      "url":"https://runrepeat.com/adidas-don-issue-6",
      "name":"Adidas D.O.N. Issue #6",
      "image":"https://cdn.runrepeat.com/storage/gallery/product_primary/40433/adidas-d-o-n-issue-6-main-2-22673422-720.jpg"
    }
  ]
}
```

#### B. JavaScript State Data
Embedded in large JSON objects within `<script>` tags containing:
- Detailed shoe information
- Scores and ratings
- Prices
- Brand information
- Complete product catalog

### 3. Current Scraper Issues

#### Problem: Incorrect CSS Selectors
The current scraper looks for:
- `li.product_list` ❌ (doesn't exist in HTML)
- `div.product-name` ❌ (doesn't exist)
- `span.price` ❌ (doesn't exist)
- `div.product-score` ❌ (doesn't exist)

#### Problem: Static HTML Parsing
The scraper assumes static HTML with server-rendered content, but RunRepeat uses client-side rendering.

### 4. Sample Data From Analysis

From the JSON-LD structured data, we found 30 shoes with complete information:

1. **Adidas D.O.N. Issue #6** - Score: 92 (Superb)
2. **Nike G.T. Cut 3** - Score: 88 (Great)  
3. **Nike LeBron 22** - Score: 91 (Superb)
4. **Adidas Dame 9** - Score: 92 (Superb)
5. **Adidas Harden Vol. 9** - Score: 90 (Great)

Each entry includes:
- Complete shoe name
- Direct URL to shoe page
- High-quality product image
- Scoring information (from other parts of JSON data)

### 5. Solution Approaches

#### Option A: JSON-LD Parsing (Recommended)
- Parse the JSON-LD structured data from `<script>` tags
- Extract shoe names, URLs, and images directly
- Make additional requests to individual shoe pages for detailed reviews

#### Option B: JavaScript State Extraction  
- Parse the large JSON objects in `<script>` tags
- Extract complete product information including scores, prices, etc.
- More comprehensive but more complex to parse

#### Option C: Selenium/Browser Automation
- Use Selenium to render JavaScript and wait for dynamic content
- Then scrape the rendered HTML
- Most reliable but slower and resource-intensive

### 6. Individual Shoe Page Structure

From analyzing `https://runrepeat.com/nike-g-t-cut-3`:
- Page title format: "Cut in half: Nike G.T. Cut 3 Review (2024) | RunRepeat"
- Contains detailed reviews, pros/cons, specifications
- Score in div with classes: `['score_green', 'trigger-popover-0', 'corescore-big__score']`
- Prices in `span` elements

### 7. Recommended Implementation

1. **Parse JSON-LD** for initial shoe list and basic info
2. **Extract embedded JSON data** for scores and detailed information  
3. **Make targeted requests** to individual shoe pages for full reviews
4. **Update CSS selectors** based on actual rendered HTML structure

This approach will be much more reliable than the current static HTML parsing method. 