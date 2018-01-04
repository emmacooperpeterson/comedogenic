from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

urls = ['https://facerealityacneclinic.com/acne-information/pore-clogging-ingredients/']

def get_soup(url):
    r  = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, "html5lib")
    return soup

def create_list():

    ingredients = []

    #first URL
    soup = get_soup('http://www.caryskincare.com/acnecomedogeniclist.html')
    tags = soup.findAll('td', class_='mceVisualAid')

    for tag in tags:
        ingredient = tag.text.replace('-', ' ')
        ingredient = ingredient.replace('&', '')
        ingredient = ingredient.replace('#', '')
        ingredient = ingredient.replace('  ', ' ')

        if ingredient in ['High', 'Medium']:
            continue
        ingredients.append(ingredient.lower())

    ingredients = ingredients[4:132]

    #second URL
    soup = get_soup('https://www.acne.org/comedogenic-list.html')
    tags = soup.findAll('span', class_ = 'pull-right')

    for tag in tags:
        ingredient = tag.parent.text.lower()[2:]
        ingredient = ingredient.replace('-', ' ')
        ingredient = ingredient.replace('&', ' ')
        ingredient = ingredient.replace('#', '')
        ingredients.append(ingredient)

    #fix the list
    ingredients[14] = 'bismuth oxychloride'
    ingredients[16] = 'butylated hydroxyanisole'
    ingredients[23] = 'ceteareth 20'
    ingredients[49] = 'glyceryl stearate se'
    ingredients[50] = 'glyceryl 3 disostearate'
    ingredients[51] = 'grape seed oil'
    ingredients[83] = 'olive oil'
    ingredients[97] = 'polyglyceryl 3 disostearate'
    ingredients[105] = 'salt'
    ingredients[107] = 'sodium lauryl sulfate'
    ingredients[120] = 'sulfated jojoba oil'
    ingredients[122] = 'tocopherol'
    ingredients[124] = 'vitamin a palmitate'
    ingredients[133] = 'coconut butter'

    return ingredients

def format_ingredients(ings):
    ings = ings.split(',')

    ingredients = []

    for ing in ings:
        if ing[0] == ' ':
            ing = ing[1:]

        ing = ing.lower()
        ing = ing.replace('-', ' ')
        ing = ing.replace('(', '')
        ing = ing.replace(')', '')
        ing = ing.replace('&', ' ')
        ing = ing.replace('.', '')

        ingredients.append(ing)

    return ingredients


def comedogenic(ings):
    com_ingredients = create_list()
    product_ingredients = format_ingredients(ings)

    com_set = set(com_ingredients)
    prod_set = set(product_ingredients)

    comedogenic = list(com_set.intersection(prod_set))

    indices = []
    violators = False

    if len(comedogenic):
        for c in comedogenic:
            indices.append(product_ingredients.index(c) + 1)

        violators = pd.DataFrame(comedogenic, indices)
        violators.columns = ['ingredient']

    return violators
