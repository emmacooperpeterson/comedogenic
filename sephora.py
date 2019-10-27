from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from sephora_setup import *
import pandas as pd
import requests
import logging
import time
import bs4
import re
import os


def get_sephora_products():
    """
    Description
    -----------
    Main function to pull info from sephora.com, format it, and save it

    Returns
    -------
    Saves ingredients.csv and products.csv
    """

    # set up logging
    logging.basicConfig(filename = "runlog.log",
                        filemode = "w",
                        format = "%(asctime)s -> %(message)s",
                        datefmt = "%d-%b-%y %H:%M:%S'",
                        level = logging.INFO)

    # create instance of Sephora class
    sephora = Sephora()

    # get links to all the subcategory pages
    #for subcategory in SUBCATEGORIES:
    logging.info(f"getting subcategories for skincare")
    sephora.get_subcategory_links("skincare")
    n_subcategories = len(sephora.subcategory_links)
    logging.info(f"found {n_subcategories} subcategories\n\n")

    # for each subcategory page, get links to all product pages
    for i, subcategory in enumerate(sephora.subcategory_links):
        logging.info(f"getting product links for subcategory {i+1}/{n_subcategories} -> {subcategory}")
        sephora.get_product_links(subcategory)

    n_products = len(sephora.product_links)
    logging.info(f"found {n_products} products\n\n")

    # for each product page, get all product information
    for i, product in enumerate(sephora.product_links):
        logging.info(f"getting product info for product {i+1}/{n_products}")
        sephora.get_product_info(product)

    # create and save dataframes
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
        self.product_links = set()
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

        subcategories = search_url(
            url = BASE_URL + "shop/" + category_name,
            class_type = "a",
            class_tag = PRODUCT_CATEGORY_CLASS
        )

        # get the links
        # EXCLUDE_SUBCATEGORIES defined in sephora_setup.py
        links = [s["href"] for s in subcategories]
        links = [s for s in links if s not in EXCLUDE_SUBCATEGORIES]
        self.subcategory_links += links


    def get_product_links(self, subcategory_link: str, testing: bool = False):
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
        testing: bool
            if true, skip the scrolling code and only search the top of the page

        Returns
        -------
        Updates self.product_links with links for the specified subcategory
        """

        if testing:
            products = search_url(
                url = BASE_URL + subcategory_link,
                class_type = "a",
                class_tag = PRODUCT_LINK_CLASS
            )

        else:
            # setup for scrolling
            browser = webdriver.Chrome(ChromeDriverManager().install())
            browser.get(BASE_URL + subcategory_link + "?pageSize=300")

            # close the "Sign up for Sephora" box if it's there
            try:
                browser.find_element_by_class_name("css-wuwqem").click();
            except:
                pass

            # scroll to the bottom, wait 2 seconds, continue until done
            get_length_of_page = """
                window.scrollTo(0, document.body.scrollHeight);
                var lenOfPage = document.body.scrollHeight;
                return lenOfPage;"""

            length_of_page = browser.execute_script(get_length_of_page)

            finished = False
            while not finished:
                last_count = length_of_page
                time.sleep(5)
                length_of_page = browser.execute_script(get_length_of_page)
                if last_count == length_of_page:
                    finished = True

            # now we can grab the full source code
            source_code = browser.page_source
            browser.close()

            # use BeautifulSoup to search for the product links
            soup = bs4.BeautifulSoup(source_code, "html.parser")
            products = soup.find_all("a", class_ = PRODUCT_LINK_CLASS)

        links = set([c["href"] for c in products])
        logging.info(f"{len(links)} products found\n")
        self.product_links.update(links) # append to set



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

        # grab the page
        url = BASE_URL + product_link
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.content, 'html.parser')

        # find product info
        name = self.safely_find(
            soup = soup,
            tag = "span",
            class_tag = NAME_CLASS
        )

        logging.info(name)

        # skip kits/sets of products
        kit_pattern = re.compile(r"\sset\s|\skit\s", re.IGNORECASE)

        if kit_pattern.search(name):
            logging.info(f"skipping set: {name}")
            return None

        brand = self.safely_find(
            soup = soup,
            tag = "span",
            class_tag = BRAND_CLASS
        )

        price = self.safely_find(
            soup = soup,
            tag = "div",
            class_tag = PRICE_CLASS
        )

        product_type = self.safely_find(
            soup = soup,
            tag = "a",
            class_tag = PRODUCT_TYPE_CLASS
        )

        product_details = self.safely_find(
            soup = soup,
            tag = "div",
            class_tag = PRODUCT_CLASS,
            find_all = True
        )

        # separate product_details into description, usage, and ingredients
        description = None
        usage = None

        if len(product_details) > 0:
            description = product_details[0].get_text()

            # skip kits/sets of products
            if kit_pattern.search(description):
                logging.info(f"skipping set: {name}")
                return None

        if len(product_details) > 1:
            usage = product_details[1].get_text()

        final_ingredients = None
        if len(product_details) > 2:
            raw_ingredients = product_details[2]
            final_ingredients = self.find_ingredients(raw_ingredients)

        # convert the ingredient string to a list of formatted ingredients
        formatted_ingredients = self.format_ingredients(
            raw_ingredients = final_ingredients,
            product_name = name
        )

        logging.info(formatted_ingredients)
        logging.info("\n\n")

        # save the final information
        self.product_info.append({
            "name": name,
            "link": url,
            "brand": brand,
            "price": price,
            "raw ingredients": final_ingredients,
            "ingredients": formatted_ingredients,
            "product_type": product_type
        })


    def safely_find(self, soup, tag: str, class_tag: str, find_all: bool = False):
        """
        Description
        -----------
        Helper function to locate a given class with the page,
        and return None if it isn't found

        Parameters
        ----------
        soup: bs4 object returned by bs4.BeautifulSoup()
        tag: str
            e.g. "span", "div", etc.
        class_tag: str
            the specific class you're searching for
        find_all: bool
            True if find_all() is desired; otherwise, find() is used

        Returns
        -------
        result: list if find_all = True, string otherwise
        """

        try:
            if find_all:
                result = soup.find_all(tag, class_ = class_tag)
            else:
                result = soup.find(tag, class_ = class_tag).get_text()

        except:
            result = None
        return result


    def find_ingredients(self, raw_ingredients):
        """
        Description
        -----------
        Helper function to locate ingredient list within product details

        Parameters
        ----------
        raw_ingredients: bs4 object

        Returns
        -------
        ingredients: str
        """

        ingredients = None

        # sometimes the ingredients are the very first thing in the section
        # assume this is the case if the first thing contains >10 commas
        # to do: come up with a better method than 10 commas :-)
        # this misses short INCI lists entirely
        # idea: keep going to the next sibling until we reach the bottom
        # if the bottom has the "clean @ sephora" stuff or whatever
        # go one above that
        # the INCI list is almost always the last thing that contains a fair amount of commas
        first_item = next(raw_ingredients.children, None).string

        if first_item:
            if first_item.count(",") >= 10:
                ingredients = first_item

            elif raw_ingredients.br:
                ingredients = raw_ingredients.br

                # loop until we locate the ingredient list
                finished = False
                while not finished:
                    try:
                        ingredients = ingredients.next_sibling

                        if not isinstance(ingredients, bs4.element.NavigableString):
                            continue

                        if ingredients.count(",") < 10:
                            continue
                    except:
                        logging.info(f"---------------> FAILED TO FIND INGREDIENTS")

                    finished = True

        return ingredients


    def format_ingredients(self, raw_ingredients: str, product_name: str) -> list:
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
        product_name: str

        Returns
        -------
        formatted_ingredients: list of str
            List of formatted ingredient strings
        """

        # move on if no ingredient string was found
        if not raw_ingredients:
            return [None]

        # remove the language that can appear at the end of inci lists
        match = "Clean at Sephora products are formulated without:"
        raw_ingredients = raw_ingredients.split(match, 1)[0]

        match = "This product is vegan and gluten-free."
        raw_ingredients = raw_ingredients.replace(match, "")

        match = "These statements have not been evaluated"
        raw_ingredients = raw_ingredients.split(match, 1)[0]

        match = "Please be aware that ingredient lists may change"
        raw_ingredients = raw_ingredients.split(match, 1)[0]

        # remove parentheticals
        # e.g. Titanium Dioxide (CI 77891) -> Titanium Dioxide
        regex = r"\({1}.{1,20}\){1}\s"
        raw_ingredients = re.sub(regex, "", raw_ingredients)

        # remove new line characters and periods
        raw_ingredients = re.sub(r"\n|\.|\*|\r", " ", raw_ingredients)

        # split into a list of strings
        ingredients = raw_ingredients.split(", ")
        formatted_ingredients = set([ingr.strip().lower() for ingr in ingredients])

        # use set ^ in case there are any duplicates
        logging.info(f"found {len(formatted_ingredients)} ingredients: {product_name}")

        return formatted_ingredients




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
                "ingredient": list(product["ingredients"]),
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
