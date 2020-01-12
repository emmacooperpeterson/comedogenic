import pandas as pd
import requests
import bs4

page = requests.get("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:01996D0335-20060209")
soup = bs4.BeautifulSoup(page.content, "html.parser")
table = soup.find("tbody")

data = []
rows = table.find_all('tr')
for row in rows:
    try:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele]) # Get rid of empty values
    except:
        continue

df = pd.DataFrame(data)
new_header = df.iloc[0] #grab the first row for the header
df = df[1:] #take the data less the header row
df.columns = new_header #set the header row as the df header