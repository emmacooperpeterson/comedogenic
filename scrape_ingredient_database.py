import pandas as pd
import requests
import bs4


def get_page():
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:01996D0335-20060209"
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    return soup


def make_ingredient_table(soup) -> pd.DataFrame:
    """
    Description
    -----------
    Find the HTML table of ingredient descriptions, parse it into a DataFrame,
    and save a .csv

    Parameters
    ----------
    soup: bs4 object returned by bs4.BeautifulSoup()

    Returns
    -------
    inci_df: DataFrame
    """
    table = soup.find("tbody")
    rows = table.find_all('tr')

    data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [c.text.strip() for c in cols]
        data.append(cols) # drop empty values

    inci_df = pd.DataFrame(data)[1:] # remove headers from first row
    inci_df = inci_df[[0, 5, 7]]
    inci_df.columns = ["name", "description", "function"]

    # uppercase the functions so they align with the category table
    inci_df["function"] = inci_df["function"].str.upper()

    # the "function" column lists all relevant functions, separated by "/"
    # below, we separate each function into its own column, and then gather
    # right now, the max number of functions for an ingredient is 11
    functions = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    inci_df[functions] = inci_df.function.str.split("/", expand = True)

    inci_df = pd.melt(
        inci_df,
        id_vars = ['name', "description"],
        value_vars = functions,
        var_name ='function_number',
        value_name ='function'
    )

    inci_df.to_csv("data/inci_descriptions.csv", index = False)
    return inci_df


def make_category_table(soup) -> pd.DataFrame:
    """
    Description
    -----------
    Find the list of ingredient categories, parse it into a DataFrame,
    and save a .csv

    Parameters
    ----------
    soup: bs4 object returned by bs4.BeautifulSoup()

    Returns
    -------
    category_df: DataFrame
    """
    categories = soup.find_all("p", class_ = "norm")[47:173]

    category_names = []
    category_descriptions = []
    for c in categories:
        text = c.text
        if text.upper() == text: # the names are all uppercase
            category_names.append(text)
        else:
            category_descriptions.append(text)

    category_df = pd.DataFrame(
        list(zip(category_names, category_descriptions)),
        columns =['category', 'description']
    )

    category_df.to_csv("data/inci_categories.csv", index = False)
    return category_df


if __name__ == '__main__':
    soup = get_page()
    inci_df = make_ingredient_table(soup)
    category_df = make_category_table(soup)
