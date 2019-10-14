
# base URL for all requests to Sephora website
BASE_URL = "https://www.sephora.com/"

# html tags to identify various parts of sephora website
# (found these by manually inspecting product pages)
PRODUCT_CATEGORY_CLASS = "css-or7ouu" #a (e.g. Moisturizers)
PRODUCT_LINK_CLASS = "css-ix8km1" #a (link to product page)
NAME_CLASS = "css-0" #span (e.g. A-Passioni™ Retinol Cream)
BRAND_CLASS = "css-euydo4" #span (e.g. Drunk Elephant)
PRICE_CLASS = "css-14hdny6" #div (e.g. $74.00)
PRODUCT_CLASS = "css-pz80c5" #div (contains description, usage, ingredients)
PRODUCT_TYPE_CLASS = "css-iasgl9" #a (e.g. Eye Masks)

# categories to search for products
# add to this list as needed
SUBCATEGORIES = ["skincare", "makeup-cosmetics"] # why doesn't this work?

EXCLUDE_SUBCATEGORIES = [ # why doesn't this work?
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
