from bs4 import BeautifulSoup as bs
import requests
import re

PRODUCT_CLASS = "css-pz80c5" #div
BRAND_CLASS = "css-euydo4" #span
NAME_CLASS = "css-0" #span
PRICE_CLASS = "css-14hdny6" #div
PRODUCT_TYPE_CLASS = "css-or7ouu" #a
PRODUCT_LINK_CLASS = "css-ix8km1" #a

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

    def get_product_details(self):
        page = requests.get(self.base_url + self.link_suffix)
        soup = bs(page.content, 'html.parser')

        product_details = soup.find_all("div", class_ = PRODUCT_CLASS)

        if len(product_details) > 0:
            self.description = product_details[0].get_text()

        if len(product_details) > 1:
            self.usage = product_details[1].get_text()

        if len(product_details) > 2:
            self.ingredients = product_details[2].get_text()

        brand = soup.find("span", class_ = BRAND_CLASS).get_text()
        self.brand = brand

        name = soup.find("span", class_ = NAME_CLASS).get_text()
        self.name = name

        price = soup.find("div", class_ = PRICE_CLASS).get_text()
        self.price = price

    def clean_ingredients(self):
        regex = r"-.*\:.*\.\s(.*)"
        matches = re.findall(regex, self.ingredients)
        if matches != []:
            matches_list = matches[0].split(",")
            clean_matches = [m.strip().lower().replace(".", "") for m in matches_list]
            self.ingredients = clean_matches



class Sephora:
    def __init__(self):
        self.product_type_link_class = PRODUCT_TYPE_CLASS
        self.base_url = "https://www.sephora.com/"
        self.names = {"skincare": "skincare", "makeup": "makeup-cosmetics"}
        self.categories = []

    def get_categories(self, category_type):
        url = self.base_url + "shop/" + self.names[category_type]
        page = requests.get(url)
        soup = bs(page.content, 'html.parser')
        categories = soup.find_all("a", class_ = self.product_type_link_class)
        links = [c["href"] for c in categories]

        for link in links:
            self.categories.append(link)

    def remove_categories(self):
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

        self.categories = [p for p in self.categories if p not in exclude]


class Category:
    def __init__(self, link_suffix):
        self.base_url = "https://www.sephora.com"
        self.category_name = link_suffix
        self.product_link_class = PRODUCT_LINK_CLASS
        self.products = []
        self.test = None

    def get_products(self):
        url = self.base_url + self.category_name
        page = requests.get(url)
        soup = bs(page.content, "html.parser")
        products = soup.find_all("a", class_ = self.product_link_class)
        links = [c["href"] for c in products]

        for link in links:
            self.products.append(link)



if __name__ == '__main__': # put all of this into the Sephora class
    sephora = Sephora()

    for category in ["makeup", "skincare"]:
        sephora.get_categories(category)

    sephora.remove_categories()

    products = []
    for link in sephora.categories[10:11]: # subsetting for testing purposes
        category = Category(link)
        category.get_products()
        products.append(category.products)

    products = [p for lst in products for p in lst]

    all_products = []
    for link in products:
        product = Product(link)
        product.get_product_details()
        product.clean_ingredients()
        all_products.append({product.name: {
                                "link": product.base_url + product.link_suffix,
                                "brand": product.brand,
                                "price": product.price,
                                #"description": product.description,
                                #"usage": product.description,
                                "ingredients": product.ingredients
                                }
                            })
