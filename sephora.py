from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
import re

PRODUCT_CLASS = "css-pz80c5" #div
BRAND_CLASS = "css-euydo4" #span
NAME_CLASS = "css-0" #span
PRICE_CLASS = "css-14hdny6" #div
PRODUCT_TYPE_CLASS = "css-or7ouu" #a
PRODUCT_LINK_CLASS = "css-ix8km1" #a



class Sephora:
    def __init__(self):
        self.product_type_link_class = PRODUCT_TYPE_CLASS
        self.base_url = "https://www.sephora.com/"
        self.category_links = []
        self.product_links = []
        self.product_info = []

    def get_category_links(self, category_name):
        # get links for each category page
        url = self.base_url + "shop/" + category_name
        page = requests.get(url)
        soup = bs(page.content, 'html.parser')
        categories = soup.find_all("a", class_ = self.product_type_link_class)

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
        self.category_links += links

    def get_product_links(self):
        # get links to every product listed on every category page
        products = []
        for link in self.category_links[15:16]: # subsetting for testing purposes
            category = Category(link)
            category.get_category()
            products.append(category.products)

        self.product_links = [p for lst in products for p in lst]


    def get_all_product_info(self):
        # get product info for every product listed on every category page
        for link in self.product_links:
            product = Product(link)
            product.get_product_details()
            product.clean_ingredients()

            self.product_info.append({
                "name": product.name,
                "link": product.base_url + product.link_suffix,
                "brand": product.brand,
                "price": product.price,
                "raw ingredients": product.raw_ingredients,
                "ingredients": product.ingredients
                # can we add category? e.g. moisturizer, treatment, etc.
            })



class Category:
    def __init__(self, link_suffix):
        self.base_url = "https://www.sephora.com"
        self.category_name = link_suffix
        self.product_link_class = PRODUCT_LINK_CLASS
        self.products = []
        self.test = None

    def get_category(self):
        # get links to every product in a given category
        url = self.base_url + self.category_name
        page = requests.get(url)
        soup = bs(page.content, "html.parser")
        products = soup.find_all("a", class_ = self.product_link_class)
        links = [c["href"] for c in products]

        for link in links:
            self.products.append(link)



class Product:
    def __init__(self, link_suffix):
        self.base_url = "https://www.sephora.com"
        self.link_suffix = link_suffix
        self.name = None
        self.brand = None
        self.price = None
        self.description = None
        self.usage = None
        self.ingredients = None
        self.raw_ingredients = None
        self.first = None
        self.rest = None

    def get_product_details(self):
        # get information about a given product
        page = requests.get(self.base_url + self.link_suffix)
        soup = bs(page.content, 'html.parser')

        product_details = soup.find_all("div", class_ = PRODUCT_CLASS)

        if len(product_details) > 0:
            self.description = product_details[0].get_text()

        if len(product_details) > 1:
            self.usage = product_details[1].get_text()

        if len(product_details) > 2:
            self.raw_ingredients = product_details[2].get_text()

        brand = soup.find("span", class_ = BRAND_CLASS).get_text()
        self.brand = brand

        name = soup.find("span", class_ = NAME_CLASS).get_text()
        self.name = name

        price = soup.find("div", class_ = PRICE_CLASS).get_text()
        self.price = price

    def clean_ingredients(self):
        # remove parentheticals
        regex = r"\({1}.{1,20}\){1}\s"
        self.raw_ingredients = re.sub(regex, "", self.raw_ingredients)

        # remove hyphens
        regex = r"\-"
        self.raw_ingredients = re.sub(regex, " ", self.raw_ingredients)

        # remove weird line breaks / characters
        for pattern in [u"\xa0", u"\u2028", u"\r", u"\t", u"\n"]:
            self.raw_ingredients = self.raw_ingredients.replace(pattern, u"")

        first_ingredient_regex = r"\.([A-Z]+[\w\s]*)\,|[\.\s?]\s([A-Z]+[\w\s]*)\,"
        remaining_ingredients_regex = r"[\,]\s([A-Z]+[\w\s]*)"

        ingredients = []
        first_ingredient = re.search(first_ingredient_regex, self.raw_ingredients)

        if not first_ingredient:
            first_ingredient = re.search(r"([A-Z][a-z]*)\,", self.raw_ingredients)

        if first_ingredient:
            ingredients.append(first_ingredient.group().strip("., \r"))
        else:
            print(self.raw_ingredients)

        ingredients += re.findall(remaining_ingredients_regex, self.raw_ingredients)

        self.ingredients = [ingr.strip() for ingr in ingredients]


def make_ingredient_table(product_info):
    product_names = []
    product_ingredients = []

    for product in product_info:
        ingredients = product["ingredients"]
        product_ingredients.append(ingredients)
        product_names.append([product["name"]] * len(ingredients))

    product_names = [x for lst in product_names for x in lst]
    product_ingredients = [x for lst in product_ingredients for x in lst]

    df = pd.DataFrame(list(zip(product_names, product_ingredients)),
                      columns =['name', 'ingredient'])

    # add ingredient rank
    df["rank"] = df.groupby(["name"]).cumcount()+1

    return(df)





if __name__ == '__main__':
    sephora = Sephora()
    sephora.get_category_links("makeup-cosmetics")
    sephora.get_category_links("skincare")
    sephora.get_product_links()
    sephora.get_all_product_info()
    ingredient_table = make_ingredient_table(sephora.product_info)
