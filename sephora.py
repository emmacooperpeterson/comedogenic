from bs4 import BeautifulSoup as bs
from sephora_setup import *
import pandas as pd
import requests
import re



def search_url(url, class_type: str, class_tag: str):
    """
    Description
    -----------
    Helper function to search a webpage for a given class type and tag

    Parameters
    ----------
    class_type: str
        e.g., "a", "div", "span", etc.
    class_tag:str
        the specific tag to search for, e.g. "css-or7ouu"
        (these are defined in sephora_setup.py)

    Returns
    -------
    bs4.element.ResultSet object (iterable)
    """
    page = requests.get(url)
    soup = bs(page.content, "html.parser")
    result = soup.find_all(class_type, class_ = class_tag)
    return result



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

        Currently accepts category_name = "skincare" or "makeup-cosmetics"

        Parameters
        ----------
        category_name: str
            name of the category

        Returns
        -------
        Updates self.subcategory_links to include links for specified category
        """

        assert category_name in ["skincare", "makeup-cosmetics"], (
            "category_name must be skincare or makeup-cosmetics.")

        categories = search_url(
            url = BASE_URL + "shop/" + category_name,
            class_type = "a",
            class_tag = PRODUCT_CATEGORY_CLASS
        )

        # list of subcategories to skip
        exclude = [
            "/shop/skin-care-sets-travel-value",
            "/shop/mini-skincare",
            "/shop/wellness-skincare",
            "/shop/skin-care-tools",
            "/shop/makeup-kits-makeup-sets",
            "/shop/mini-makeup",
            "/shop/makeup-applicators",
            "/shop/makeup-accessories",
            "/shop/nails-makeup"
        ]

        links = [c["href"] for c in categories if c not in exclude]
        self.subcategory_links += links


    def get_product_links(self, subcategory_link):
        """
        Description
        -----------
        Get links to every product on a given subcategory page

        Parameters
        ----------
        subcategory_link: str
            link suffix for a subcategory page, e.g. "/shop/cleanser"

        Returns
        -------
        Updates self.product_links to include links for specified subcategory
        """

        products = search_url(
            url = BASE_URL + subcategory_link,
            class_type = "a",
            class_tag = PRODUCT_LINK_CLASS
        )

        links = [c["href"] for c in products]
        self.product_links += links



    def get_product_info(self, product_link):
        """
        Description
        -----------
        Get product info for a given product on a given subcategory page

        Parameters
        ----------
        product_link:str
            link suffix for a product page, e.g.
            "/product/fablantis-P447792?icid2=products grid:p447792"

        Returns
        -------
        Updates self.product_info to include a dictionary
        for the specified product
        """

        url = BASE_URL + product_link
        page = requests.get(url)
        soup = bs(page.content, 'html.parser')

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

        if len(product_details) > 0:
            description = product_details[0].get_text()

        if len(product_details) > 1:
            usage = product_details[1].get_text()

        if len(product_details) > 2:
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


    def format_ingredients(self, raw_ingredients) -> list:
        """
        Description
        -----------
        TODO: Update this function to better handle all ingredient lists

        Create a list of formatted ingredients from the raw_ingredients string
        e.g. raw_ingredients = "Aqua (Water), Glycerin, Niacinamide"
             formatted_ingredients = ["aqua", "glycerin", "nicacinamide"]

        Parameters
        ----------
        raw_ingredients:str
            string listing all ingredients, e.g.
            "Water, Simmondsia Chinensis (Jojoba) Seed Oil,
                Butyrospermum Parkii (Shea) Butter, ..."

        Returns
        -------
        formatted_ingredients:list of str
            List of formatted ingredient strings
        """

        ingredients = []

        # remove parentheticals
        # e.g. Titanium Dioxide (CI 77891) -> Titanium Dioxide
        regex = r"\({1}.{1,20}\){1}\s"
        raw_ingredients = re.sub(regex, "", raw_ingredients)

        # remove hyphens
        regex = r"\-"
        raw_ingredients = re.sub(regex, " ", raw_ingredients)

        # remove weird line breaks / characters
        for pattern in [u"\xa0", u"\u2028", u"\r", u"\t", u"\n"]:
            raw_ingredients = raw_ingredients.replace(pattern, u"")

        # because of the way the ingredient lists are set up on Sephora.com,
        # we need special regex to identify where the first ingredient begins.
        # we then use that as the starting point to identify the rest
        first_ingredient_regex = r"\.([A-Z]+[\w\s]*)\,|[\.\s?]\s([A-Z]+[\w\s]*)\,"
        remaining_ingredients_regex = r"[\,]\s([A-Z]+[\w\s]*)"

        # TODO: make this a try/except
        first_ingredient = re.search(first_ingredient_regex, raw_ingredients)

        # if the above regex didn't work, try another way
        if not first_ingredient:
            first_ingredient = re.search(r"([A-Z][a-z]*)\,", raw_ingredients)

        ingredients.append(first_ingredient.group().strip("., \r"))

        ingredients += re.findall(remaining_ingredients_regex, raw_ingredients)

        clean_ingredients = [ingr.strip().lower() for ingr in ingredients]
        return clean_ingredients







def make_ingredient_table(product_info: list):
    product_names = []
    product_ingredients = []

    for product in product_info:
        ingredients = product["ingredients"]
        product_ingredients.append(ingredients)
        product_names.append([product["name"]] * len(ingredients))

    product_names = [x for lst in product_names for x in lst]
    product_ingredients = [x.lower() for lst in product_ingredients for x in lst]

    df = pd.DataFrame(list(zip(product_names, product_ingredients)),
                      columns =['name', 'ingredient'])

    # add ingredient rank
    df["rank"] = df.groupby(["name"]).cumcount()+1

    return(df)



def make_product_table(product_info: list):
    products = product_info

    for p in products: #FIXME
        p.pop("ingredients")
        p.pop("raw ingredients")

    product_df = pd.DataFrame(products)

    return product_df



def main():
    sephora = Sephora()

    #for subcategory in SUBCATEGORIES: idk why this doesn't work
    for subcategory in ["makeup-cosmetics", "skincare"]:
        sephora.get_subcategory_links(subcategory)

    for i, subcategory in enumerate(sephora.subcategory_links[15:16]): # subsetting to test
        print(f"getting product links for subcategory {i+1} of {len(sephora.subcategory_links[15:16])}")
        sephora.get_product_links(subcategory)

    print("")

    for i, product in enumerate(sephora.product_links):
        print(f"getting product info for product {i+1} of {len(sephora.product_links)}")
        sephora.get_product_info(product)

    #ingredient_table = make_ingredient_table(sephora.product_info)
    #ingredient_table.to_csv("ingredient_table.csv", index = False)
    #product_table = make_product_table(sephora.product_info)
    #product_table.to_csv("product_table.csv", index = False)




if __name__ == '__main__':
    main()



# TODO:
    # improve the table functions
    # document table functions
    # create a main() function
