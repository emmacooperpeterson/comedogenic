*This is a work in progress.*

Provide a list of skincare/makeup ingredients as a string, and receive
a dataframe with any comedogenic ingredients in that list, along with
their location within the list.

**Sources:**
- Comedogenic ingredients were found [here](https://www.acne.org/comedogenic-list.html) and [here](http://www.caryskincare.com/acnecomedogeniclist.html).

# Example:

**Clinique Liquid Facial Soap - Mild**

- This product is described as "oil-free", "dermatologist developed", and "non-comedogenic".
- However, it's second ingredient (see below) is comedogenic.

```python
ingredients = 'Water / Aqua / Eau, Sodium Laureth Sulfate, Sodium Chloride, Cocamidopropyl Hydroxysultaine, Lauramidopropyl Betaine, Sodium Cocoyl Sarcosinate, Tea-Cocoyl Glutamate, Di-PPG-2 Myreth-10 Adipate, Aloe Barbadensis Leaf Juice, PEG-120 Methyl Glucose Dioleate, Sucrose, Sodium Hyaluronate, Cetyl Triethylmonium Dimethicone PEG-8 Succinate, Butylene Glycol, Hexylene Glycol, Polyquaternium-7, Laureth-2, Caprylyl Glycol, Sodium Sulfate, Tocopheryl Acetate, EDTA, Disodium EDTA, Phenoxyethanol'
```

```python
comedogenic(ingredients)
```

Output:

| index   | ingredient             |
| :------ | :--------------------- |
| 15      | hexylene glycol        |
| 2       | sodium laureth sulfate |


# Next Steps:
- This currently tests only for exact matches of ingredient names. I'd like to add fuzzy matching, since the ingredient names are so complicated and typos therefore seem likely.
