"""
XBOX Games Sales Scraper
===============================
Author: Udit Kumar Chatterjee
Email: quantumudit@gmail.com
===============================
This script enables scraping of XBOX games on sale using Playwright web automation. 
It defines a data class "Game" to hold game information and includes functions to 
extract game details from HTML content, automate web scraping of sales pages, 
and write the scraped data to a CSV file.

Functions:
----------
1. extract_game_info(): Extracts game information from HTML content.
2. web_automation(): Automates web scraping of XBOX game sales.
"""

# Import necessary libraries
import os
import re
from csv import DictWriter
from dataclasses import asdict, dataclass, fields
from datetime import datetime

from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser


# Setting up the dataclass
@dataclass
class Game:
    """
    Represents information about an XBOX game on sale.

    Attributes:
        title (str): The title of the game.
        release_date (str): The release date of the game.
        multiplayer (str): Indicates if the game supports multiplayer.
        age_criteria (str): Age criteria for the game.
        rating_system (str): The rating system of the game.
        link (str): The URL link to the game.
        img (str): The image URL of the game.
        off_pct (str): The percentage of discount on the game.
        original_price (str): The original price of the game.
        discounted_price (str): The discounted price of the game.
        star_rating (str): The rating value of the game.
        total_reviews (str): The total number of reviews for the game.
        optimization (str): Optimization details for the game.
        platforms (str): The platforms supported by the game.
        description (str): Description of the game.
        sales_title (str): The title of the sales event.
        scrape_timestamp (str): Timestamp of when the data was scraped.
    """
    title: str
    release_date: str
    multiplayer: str
    age_criteria: str
    rating_system: str
    link: str
    img: str
    off_pct: str
    original_price: str
    discounted_price: str
    star_rating: str
    total_reviews: str
    optimization: str
    platforms: str
    description: str
    sales_title: str
    scrape_timestamp: str


# Setting up constants
HEADLESS = False
SLOW_MO = 300
COLUMN_NAMES = [field.name for field in fields(Game)]

# ========== Utility Functions ========== #


def extract_game_info(page_html: str) -> list:
    """
    Extracts game information from HTML content.

    Args:
        page_html (str): HTML content of the page.

    Returns:
        list: List of dictionaries containing game information.
    """
    # List to store extracted game data
    games_info = []

    # Parse HTML content
    content = HTMLParser(page_html)

    # Extract all game info in the page
    games = content.css("div.gameDivsWrapper div.m-product-placement-item")

    # Fetch the name of the XBOX sales
    sales_name = content.css_first("h1.salesHeroHeading").text(strip=True)

    def extract(html, selector):
        """Utility function to extract text from HTML elements."""
        element = html.css_first(selector)
        if element is not None:
            return element.text(strip=True)

    # Scrape contents for each game present in the page
    for game in games:
        game_data = Game(
            title=re.sub(r"\s+", " ", game.css_first(
                "h3[itemprop='product name']").text(strip=True)),
            release_date=re.sub(r"T.*", "", game.attrs["data-releasedate"]),
            multiplayer=game.attrs["data-multiplayer"],
            age_criteria=game.attrs["data-rating"],
            rating_system=game.attrs["data-ratingsystem"],
            link=game.css_first("a.gameDivLink").attrs["href"],
            img="https:" + game.css_first(
                "picture.containerIMG img.c-image").attrs["src"],
            off_pct=game.css_first(
                "span.c-badge").text(strip=True).replace(" OFF", ""),
            original_price=game.css_first(
                "div.c-price s").text(strip=True).replace("Full price was₹", ""),
            discounted_price=game.css_first(
                "div.c-price span.textpricenew").text(strip=True).replace("₹", ""),
            star_rating=extract(
                game, "div.c-rating span[itemprop='ratingValue']"),
            total_reviews=extract(
                game, "div.popinfo span.reviewtotal"),
            optimization=extract(
                game, "div.popicons span.c-paragraph-3"),
            description=re.sub(
                r"\s+", " ",
                game.css_first(
                    "div.popdescription div.furtherrelease span.furthcontent")
                .text(strip=True).replace("\n", "")
            ),
            platforms=", ".join([
                item.text(strip=True) for item in
                game.css("div.platformdescription div.furtherplatform div.c-tag")
            ]),
            sales_title=sales_name,
            scrape_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Add the game data to a dictionary in the list
        games_info.append(asdict(game_data))
    return games_info


def web_automation(start_url: str, output: str) -> None:
    """
    Automates web scraping of XBOX game sales.

    Args:
        start_url (str): URL to start scraping from.
        output (str): Output file to save scraped data.
    """
    with sync_playwright() as pw:

        # Launch browser and navigate to the specified URL
        browser = pw.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        page = browser.new_page()
        page.goto(start_url)

        # Wait for specific content to load
        page.is_visible("div.gameDivsWrapper")

        # Increase number of games per page
        page.click("button#unique-id-for-paglist-generated-select-menu-trigger")
        page.click("li#unique-id-for-paglist-generated-select-menu-3")

        # Open CSV file to write scraped content
        with open(os.path.normpath(output), "w", newline="", encoding="utf-8") as f:
            csv_writer = DictWriter(f, fieldnames=COLUMN_NAMES)
            csv_writer.writeheader()

            # Get the HTML content of the page
            html_content = page.inner_html("body")

            # Parse & scrape HTML content and write in CSV file
            while True:
                games_data = extract_game_info(page_html=html_content)
                csv_writer.writerows(games_data)

                if page.is_visible("li.paginatenext"):
                    # Click on next page if available
                    page.click("li.paginatenext")
                    page.is_visible("div.gameDivsWrapper")
                    html_content = page.inner_html("body")
                else:
                    # Stop scraping if next page is not available
                    break


if __name__ == "__main__":

    # URL for XBOX Countdown Sales
    XBOX_SALES_URL = "https://www.xbox.com/en-IN/promotions/sales/countdown-sale"

    # Output file path
    OUTPUT_CSV = "./data/raw/countdown_sales_december_2023.csv"

    # Initiate web scraping
    web_automation(start_url=XBOX_SALES_URL, output=OUTPUT_CSV)
