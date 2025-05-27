import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import pandas as pd

class RunRepeatScraper:
    def __init__(self):
        self.base_url = "https://runrepeat.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.shoes_data = []

    def get_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a webpage."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_shoe_data(self, shoe_element) -> Dict:
        """Extract data from a single shoe card."""
        try:
            # Get shoe name
            name_element = shoe_element.find('div', class_='product-name')
            name = name_element.text.strip() if name_element else "N/A"

            # Get price
            price_element = shoe_element.find('span', class_='price')
            price = price_element.text.strip() if price_element else "N/A"

            # Get rating
            rating_element = shoe_element.find('div', class_='product-score')
            rating = rating_element.text.strip() if rating_element else "N/A"

            # Get number of reviews
            reviews_element = shoe_element.find('div', class_='reviews-count')
            reviews_count = reviews_element.text.strip() if reviews_element else "N/A"

            # Get shoe URL
            url_element = shoe_element.find('a', href=True)
            shoe_url = self.base_url + url_element['href'] if url_element else "N/A"

            # Get brand
            brand_element = shoe_element.find('div', class_='brand')
            brand = brand_element.text.strip() if brand_element else "N/A"

            # Get release date
            release_element = shoe_element.find('div', class_='release-date')
            release_date = release_element.text.strip() if release_element else "N/A"

            # Get popularity score
            popularity_element = shoe_element.find('div', class_='popularity-score')
            popularity = popularity_element.text.strip() if popularity_element else "N/A"

            # Get expert score
            expert_score_element = shoe_element.find('div', class_='expert-score')
            expert_score = expert_score_element.text.strip() if expert_score_element else "N/A"

            # Get user score
            user_score_element = shoe_element.find('div', class_='user-score')
            user_score = user_score_element.text.strip() if user_score_element else "N/A"

            # Get color options
            colors_element = shoe_element.find('div', class_='color-options')
            colors = [color.text.strip() for color in colors_element.find_all('span')] if colors_element else []

            # Get price history
            price_history_element = shoe_element.find('div', class_='price-history')
            price_history = price_history_element.text.strip() if price_history_element else "N/A"

            # Get discount percentage if available
            discount_element = shoe_element.find('div', class_='discount')
            discount = discount_element.text.strip() if discount_element else "N/A"

            return {
                'name': name,
                'brand': brand,
                'price': price,
                'discount': discount,
                'rating': rating,
                'reviews_count': reviews_count,
                'expert_score': expert_score,
                'user_score': user_score,
                'popularity': popularity,
                'release_date': release_date,
                'colors': colors,
                'price_history': price_history,
                'url': shoe_url
            }
        except Exception as e:
            print(f"Error extracting shoe data: {e}")
            return None

    def get_shoe_details(self, url: str) -> Dict:
        """Scrape additional details from individual shoe page."""
        try:
            soup = self.get_page(url)
            if not soup:
                return {}

            details = {}
            
            # Get specifications
            specs_section = soup.find('div', class_='specifications')
            if specs_section:
                specs = {}
                for spec in specs_section.find_all('div', class_='spec'):
                    key = spec.find('span', class_='spec-name')
                    value = spec.find('span', class_='spec-value')
                    if key and value:
                        specs[key.text.strip()] = value.text.strip()
                details['specifications'] = specs

            # Get pros and cons
            pros_cons = soup.find('div', class_='pros-cons')
            if pros_cons:
                pros = [p.text.strip() for p in pros_cons.find_all('div', class_='pro')]
                cons = [c.text.strip() for c in pros_cons.find_all('div', class_='con')]
                details['pros'] = pros
                details['cons'] = cons

            # Get expert reviews
            expert_reviews = soup.find('div', class_='expert-reviews')
            if expert_reviews:
                reviews = []
                for review in expert_reviews.find_all('div', class_='review'):
                    reviewer = review.find('div', class_='reviewer')
                    content = review.find('div', class_='content')
                    if reviewer and content:
                        reviews.append({
                            'reviewer': reviewer.text.strip(),
                            'content': content.text.strip()
                        })
                details['expert_reviews'] = reviews

            return details
        except Exception as e:
            print(f"Error getting shoe details: {e}")
            return {}

    def scrape_basketball_shoes(self, max_pages: int = 5) -> List[Dict]:
        """Scrape basketball shoes data from multiple pages."""
        page = 1
        while page <= max_pages:
            url = f"{self.base_url}/catalog/basketball-shoes?page={page}"
            print(f"Scraping page {page}...")
            
            soup = self.get_page(url)
            if not soup:
                break

            shoe_elements = soup.find_all('li', class_='product_list')
            
            if not shoe_elements:
                print(f"No shoes found on page {page}")
                break

            for shoe_element in shoe_elements:
                shoe_data = self.extract_shoe_data(shoe_element)
                if shoe_data:
                    # Get additional details from individual shoe page
                    details = self.get_shoe_details(shoe_data['url'])
                    shoe_data.update(details)
                    self.shoes_data.append(shoe_data)
                    time.sleep(1)  # Be nice to the server

                        # Check if there's a next page
            
            next_page = soup.find('a', class_='paginate-buttons next-button')  # Update class name based on actual HTML
            if not next_page:
                break

            page += 1
            time.sleep(2)

        return self.shoes_data

    def save_to_json(self, filename: str = 'basketball_shoes.json'):
        """Save scraped data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.shoes_data, f, indent=4, ensure_ascii=False)

    def save_to_csv(self, filename: str = 'basketball_shoes.csv'):
        """Save scraped data to CSV file."""
        df = pd.DataFrame(self.shoes_data)
        df.to_csv(filename, index=False)

def main():
    scraper = RunRepeatScraper()
    
    # Scrape the data
    shoes_data = scraper.scrape_basketball_shoes(max_pages=5)
    
    # Save the data
    scraper.save_to_json()
    # scraper.save_to_csv()
    
    print(f"Scraped {len(shoes_data)} shoes successfully!")
    print("Data saved to basketball_shoes.json and basketball_shoes.csv")

if __name__ == "__main__":
    main()
