from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from sephora_setup import *
import pandas as pd
import requests
import time
import bs4
import re
import os

# TODO:
    # update format_ingredients to better handle all ingredient lists
    # update functions to crawl every page of subcategories (not just search on first page)
        # tried adding "?pageSize=300" but no luck

def get_sephora_products():
    """
    Description
    -----------
    Main function to pull info from sephora.com, format it, and save it

    Returns
    -------
    Saves ingredients.csv and products.csv
    """

    # create instance of Sephora class
    sephora = Sephora()

    # get links to all the subcategory pages
    for subcategory in SUBCATEGORIES[0:1]: # SUBSETTING FOR TESTING
        print(f"getting subcategories for {subcategory}")
        sephora.get_subcategory_links(subcategory)

    n_subcategories = len(sephora.subcategory_links)
    print(f"found {n_subcategories} subcategories\n")

    # for each subcategory page, get links to all product pages
    for i, subcategory in enumerate(sephora.subcategory_links[0:1]): # SUBSETTING FOR TESTING
        print(f"getting product links for subcategory {i+1}/{n_subcategories}")
        print(subcategory)
        sephora.get_product_links(subcategory)

    n_products = len(sephora.product_links)
    print(f"found {n_products} products\n")

    # for each product page, get all product information
    for i, product in enumerate(sephora.product_links[0:5]): # SUBSETTING FOR TESTING
        print(f"getting product info for product {i+1}/{n_products}")
        sephora.get_product_info(product)

    # create and save dataframes with product info
    ingredient_table = make_dataframe(
        product_info = sephora.product_info,
        table_type = "ingredients"
    )

    product_table = make_dataframe(
        product_info = sephora.product_info,
        table_type = "products"
    )






# ---------------------------- < SEPHORA CLASS > ----------------------------- #
class Sephora:
    """
    A class used to represent Sephora.

    Attributes
    ----------
    category_links: list of str
        links to category pages (e.g. Moisurizers, Cleansers, etc.)
    product_links: list of str
        links to product pages (found on category pages)
    product_info: list of dict
        dictionary for each product
    """

    def __init__(self):
        self.subcategory_links = []
        self.product_links = []
        self.product_info = []


    def get_subcategory_links(self, category_name: str):
        """
        Description
        -----------
        Get links to all the subcategories associated with a given category,
        e.g. category = skincare, subcategories = cleansers, face masks, etc.

        category_name currently accepts "skincare" or "makeup-cosmetics"

        Parameters
        ----------
        category_name: str
            name of the category

        Returns
        -------
        Updates self.subcategory_links to include links for specified category
        """

        assert category_name in ["skincare", "makeup-cosmetics"], (
            "category_name must be 'skincare' or 'makeup-cosmetics'")

        categories = search_url(
            url = BASE_URL + "shop/" + category_name,
            class_type = "a",
            class_tag = PRODUCT_CATEGORY_CLASS
        )

        # EXCLUDE_SUBCATEGORIES listed in sephora_setup.py
        links = [c["href"] for c in categories if c not in EXCLUDE_SUBCATEGORIES]
        self.subcategory_links += links


    def get_product_links(self, subcategory_link: str):
        """
        Description
        -----------
        TODO: click "next page" and continue
        (this currently grabs first 200 products by scrolling,
         but there are still more pages) --> next page button is css-a8wls9

        Get links to every product on a given subcategory page

        Subcategory pages load as you scroll – this function uses
        selenium to handle this. Scrolling code was adapted from:
        https://michaeljsanders.com/2017/05/12/scrapin-and-scrollin.html

        Parameters
        ----------
        subcategory_link: str
            link suffix for a subcategory page, e.g. "/shop/cleanser"

        Returns
        -------
        Updates self.product_links with links for the specified subcategory
        """

        # setup for scrolling
        browser = webdriver.Chrome(ChromeDriverManager().install())
        browser.get(BASE_URL + subcategory_link + "?pageSize=300")

        # scroll to the bottom, wait 2 seconds, continue until done
        get_length_of_page = """
            window.scrollTo(0, document.body.scrollHeight);
            var lenOfPage = document.body.scrollHeight;
            return lenOfPage;"""

        length_of_page = browser.execute_script(get_length_of_page)

        finished = False
        while not finished:
            last_count = length_of_page
            time.sleep(3)
            length_of_page = browser.execute_script(get_length_of_page)
            if last_count == length_of_page:
                finished = True

        # now we can grab the full source code
        source_code = browser.page_source
        browser.close()

        # use BeautifulSoup to search for the product links
        soup = bs4.BeautifulSoup(source_code, "html.parser")
        products = soup.find_all("a", class_ = PRODUCT_LINK_CLASS)

        links = [c["href"] for c in products]
        print(f"{len(links)} products found")
        self.product_links += links



    def get_product_info(self, product_link: str):
        """
        Description
        -----------
        Get product info for a given product on a given subcategory page

        Parameters
        ----------
        product_link: str
            link suffix for a product page, e.g.
            "/product/fablantis-P447792?icid2=products grid:p447792"

        Returns
        -------
        Updates self.product_info with a dictionary for the specified product
        """

        url = BASE_URL + product_link
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.content, 'html.parser')

        name = soup.find("span", class_ = NAME_CLASS).get_text()

        # skip kits/sets of products
        pattern = re.compile(r"set|kit", re.IGNORECASE)
        if pattern.search(name):
            return None

        # FIXME (doesn't work for all products)
        #type = soup.find("a", class_ = PRODUCT_TYPE_CLASS).get_text()
        brand = soup.find("span", class_ = BRAND_CLASS).get_text()
        price = soup.find("div", class_ = PRICE_CLASS).get_text()
        product_details = soup.find_all("div", class_ = PRODUCT_CLASS)

        description = None
        usage = None
        raw_ingredients = None

        product_details_length = len(product_details)

        if product_details_length > 0:
            description = product_details[0].get_text()

        if product_details_length > 1:
            usage = product_details[1].get_text()

        if product_details_length > 2:
            raw_ingredients = product_details[2].get_text()

        # convert the raw ingredient string to a list of formatted ingredients
        # formatted = lowercase, no punctuation, etc.
        formatted_ingredients = self.format_ingredients(raw_ingredients)

        self.product_info.append({
            "name": name,
            "link": url,
            "brand": brand,
            "price": price,
            "raw ingredients": raw_ingredients,
            "ingredients": formatted_ingredients,
            #"type": type
        })


    def format_ingredients(self, raw_ingredients: str) -> list:
        """
        Description
        -----------
        Create a list of formatted ingredients from the raw_ingredients string
        e.g. raw_ingredients = "Aqua (Water), Glycerin, Niacinamide"
             formatted_ingredients = ["aqua", "glycerin", "nicacinamide"]

        Parameters
        ----------
        raw_ingredients: str
            string listing all ingredients, e.g.
            "Water, Simmondsia Chinensis (Jojoba) Seed Oil,
                Butyrospermum Parkii (Shea) Butter, ..."

        Returns
        -------
        formatted_ingredients: list of str
            List of formatted ingredient strings
        """

        # handle case when no ingredients were found on the page
        if not raw_ingredients:
            return[None]

        ingredients = []

        # remove parentheticals
        # e.g. Titanium Dioxide (CI 77891) -> Titanium Dioxide
        try:
            regex = r"\({1}.{1,20}\){1}\s"
            raw_ingredients = re.sub(regex, "", raw_ingredients)
        except:
            pass

        # remove hyphens
        try:
            regex = r"\-"
            raw_ingredients = re.sub(regex, " ", raw_ingredients)
        except:
            pass

        # remove weird line breaks / characters
        try:
            for pattern in [u"\xa0", u"\u2028", u"\r", u"\t", u"\n"]:
                raw_ingredients = raw_ingredients.replace(pattern, u"")
        except:
            pass

        # because of the way the ingredient lists are set up on Sephora.com,
        # we need special regex to identify where the first ingredient begins.
        # we then use that as the starting point to identify the rest
        first_ingredient_regex = r"\.([A-Z]+[\w\s]*)\,|[\.\s?]\s([A-Z]+[\w\s]*)\,"
        remaining_ingredients_regex = r"[\,]\s([A-Z]+[\w\s]*)"

        first_ingredient = re.search(first_ingredient_regex, raw_ingredients)

        # if the above regex didn't work, try another way
        if not first_ingredient:
            first_ingredient = re.search(r"([A-Z][a-z]*)\,", raw_ingredients)

        try:
            ingredients.append(first_ingredient.group().strip("., \r"))
        except:
            pass

        try:
            ingredients += re.findall(remaining_ingredients_regex, raw_ingredients)
        except:
            pass

        clean_ingredients = [ingr.strip().lower() for ingr in ingredients]
        return clean_ingredients




# ------------------------------- < HELPERS > -------------------------------- #
def search_url(url, class_type: str, class_tag: str) -> bs4.element.ResultSet:
    """
    Description
    -----------
    Helper function to search a webpage for a given class type and tag

    Parameters
    ----------
    class_type: str
        e.g., "a", "div", "span", etc.
    class_tag: str
        the specific tag to search for, e.g. "css-or7ouu"
        (these are defined in sephora_setup.py)

    Returns
    -------
    bs4.element.ResultSet object (iterable)
    """
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    result = soup.find_all(class_type, class_ = class_tag)
    return result



def make_dataframe(product_info: list, table_type: str) -> pd.DataFrame:
    """
    Description
    -----------
    Convert product_info (list of dictionaries) to a dataframe
    containing product name, ingredients, and ingredient rank
    (i.e. rank = 1 for first ingredient) –> long format

    Parameters
    ----------
    product_info: list of dict
        one dictionary for each product in list
    table_type: str
        one of ["ingredients", "products"]

    Returns
    -------
    df: DataFrame

    This function also saves the resulting dataframe as a .csv
    """

    assert table_type in ["ingredients", "products"], (
        "table_type must be 'ingredients' or 'products'")

    dataframes = []

    for product in product_info:
        if table_type == "ingredients":
            product_dict = {
                "name": product["name"],
                "ingredient": product["ingredients"],
                "rank": list(range(1, len(product["ingredients"]) + 1))
            }

        if table_type == "products":
            product_dict = {
                "name": [product["name"]],
                "brand": [product["brand"]],
                "price": [product["price"]],
                "link": [product["link"]]
            }

        dataframes.append(pd.DataFrame(product_dict))

    df = pd.concat(dataframes)

    # save dataframe to csv
    df.to_csv(f"{table_type}.csv", index = False)

    return df







if __name__ == '__main__':
    get_sephora_products()
