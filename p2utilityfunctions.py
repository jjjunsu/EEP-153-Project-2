import fooddatacentral as fdc
import pandas as pd
from eep153_tools.sheets import read_sheets
import numpy as np
from  scipy.optimize import linprog as lp
def nutrition(age, sex, activity_level = False):
    # possible additional args pregnant, activity_level
    """
    takes the following
    age: integer from 2 through 120
    sex: either "F" for female or "M" for male
    activity_level: "Sedentary", "Moderately
Active", or "Active".
    outputs:
    bmin: A series object indexed by nutrition category with the series being the values respective to the age range from input.
    to the age range from input
    A series object indexed by nutrition category with the series being the values respective 
    to the age range from input. Energy is changed based on activity level or baseline activity which is sedentary I believe.
    """
    if age<2 or age > 120:
        return "not valid age"
    RDIs = read_sheets('https://docs.google.com/spreadsheets/d/1xqixhrAoDq9rWJf_FC3Y2eXdd010DTLPCS7JJMCfwP8/edit?usp=sharing', sheet="rda")
    RDIs = RDIs.set_index('Nutrient')
    if sex == 'F':
        fullsex = 'Female'
    else: fullsex = 'Male'
    if activity_level:
        active_energy = activity(age, sex, activity_level)
    if age<4:
        bmin = RDIs.loc[RDIs['Constraint Type'].isin(['RDA', 'AI']), 'Child_1_3']
        bmax = RDIs.loc[RDIs['Constraint Type'].isin(['UL']), 'Child_1_3']
        if activity_level:
            bmin[0] = active_energy
            return bmin, bmax
        return bmin, bmax
    else:
        agerange = find_age_range(age)
        bmin = RDIs.loc[RDIs['Constraint Type'].isin(['RDA', 'AI']), f'{fullsex}_{agerange}']
        bmax = RDIs.loc[RDIs['Constraint Type'].isin(['UL']), f'{fullsex}_{agerange}']
        if activity_level:
            bmin[0] = active_energy
            return bmin, bmax
        return bmin, bmax


def activity(age, sex, activity_level):
    activities = read_sheets('https://docs.google.com/spreadsheets/d/1xqixhrAoDq9rWJf_FC3Y2eXdd010DTLPCS7JJMCfwP8/edit?usp=sharing', sheet="activity_levels")
    activities = activities.set_index('Age')
    if age>18:
        activedic = {
        '19-20': np.arange(19,21),
        '21-25': np.arange(21,26),
        '26-30': np.arange(26,31),
        '31-35': np.arange(31,36),
        '36-40': np.arange(36,41),
        '41-45': np.arange(41,46),
        '46-50': np.arange(46,51),
        '51-55': np.arange(51,56),
        '56-60': np.arange(56,61),
        '61-65': np.arange(61,66),
        '66-70': np.arange(66,71),
        '71-75': np.arange(71,76),
        '76 and up': np.arange(76,120)
        }
        ager = "None"
        for age_range, ages in activedic.items():
            if age in ages:
                ager = age_range
        return activities.loc[ager, f"{sex} - {activity_level}"]
    else:
        return activities.loc[ager, f"{sex} - {activity_level}"]


def find_age_range(age):
    agedict = {'1_3': np.arange(1,4),
          '4_8': np.arange(4,9),
          '9_13': np.arange(9,14),
          '14_18': np.arange(14,19),
          '19_30': np.arange(19,31),
          '31_50': np.arange(31,51),
          '51U': np.arange(51,120)}
    for age_range, ages in agedict.items():
        if age in ages:
            return age_range
    return "Age not in range"
#before running make sure to assign recipes to read_sheets(data_url, sheet="recipes")
#or a constrained recipes sheet for prisons! in which case assign recipes to the manipulated df!
#before running make sure to assign recipes to read_sheets(data_url, sheet="recipes")
#or a constrained recipes sheet for prisons! in which case assign recipes to the manipulated df!
#ADD THIS ONCE U FIGURE OUT THE NAME ERROR AND WHY THIS DOESNT COME THROUGH
def format_id(id,zeropadding=0):
    """Nice string format for any id, string or numeric.

    Optional zeropadding parameter takes an integer
    formats as {id:0z} where
    """
    if pd.isnull(id) or id in ['','.']: return None

    try:  # If numeric, return as string int
        return ('%d' % id).zfill(zeropadding)
    except TypeError:  # Not numeric
        return id.split('.')[0].strip().zfill(zeropadding)
    except ValueError:
        return None

def solvercomplete(sex, age,recipes, nutrients, bmin, bmax, data_url = "https://docs.google.com/spreadsheets/d/1xqixhrAoDq9rWJf_FC3Y2eXdd010DTLPCS7JJMCfwP8/edit?usp=sharing"):
    """
    Constructs and solves a diet optimization problem based on recipes, nutritional data, and prices.

    Before running this function, ensure that you have assigned the `recipes` dataframe 
    using:
        recipes = read_sheets(data_url, sheet="recipes")
    and assigned the `nutrients` dataframe either by:
        nutrients = read_sheets(data_url, sheet="nutrients")
    or using a pre-manipulated/constrained nutrients sheet (e.g., for prisons).

    The function performs the following steps:
      1. Preprocesses the `recipes` dataframe by:
         - Formatting food codes (columns "parent_foodcode" and "ingred_code") using the `format_id` function.
         - Renaming "parent_desc" to "recipe".
         - Normalizing ingredient weights within each recipe to percentage terms.
      2. Preprocesses the provided `nutrients` dataframe by formatting the "ingred_code" column.
      3. Merges the recipes with their corresponding nutrient profiles and scales the nutrient values 
         according to the normalized ingredient weights.
      4. Aggregates the nutrient values for each recipe.
      5. Reads the `prices` data from the data URL (from the "prices" sheet), cleans the data, 
         and selects the most recent price information ("2017/2018").
      6. Identifies the common recipes between the aggregated nutrient data and the price data.
      7. Constructs constraint matrices by aligning the aggregated nutrient data with the provided 
         minimum (bmin) and maximum (bmax) nutrient bounds.
      8. Solves a linear programming problem (using the `lp` function with method 'highs') to 
         determine the cost-optimal diet that satisfies the nutritional constraints.
      9. Prints:
         - The daily cost of the diet.
         - The composition of the diet (amounts of each recipe in 100s of grams or milliliters).
         - A table of nutritional outcomes and an indication of which nutrient constraints are binding.
    
    Parameters:
      sex (str): The sex of the individual (e.g., 'M' or 'F'), which is used to determine the appropriate column of nutrient data.
      age (int): The age of the individual; used to select the appropriate nutritional requirements.
      recipes (pd.DataFrame): DataFrame containing recipe information. Expected columns include:
          - "parent_foodcode": Identifier for each recipe.
          - "ingred_code": Identifier for each ingredient.
          - "ingred_wt": Weight of the ingredient in the recipe.
          - "parent_desc": Description of the recipe (will be renamed to "recipe").
      nutrients (pd.DataFrame): DataFrame containing nutrient data. Must include the column "ingred_code",
          which will be formatted using `format_id`.
      bmin (pd.Series or pd.DataFrame): Lower bound(s) for the nutritional constraints.
      bmax (pd.Series or pd.DataFrame): Upper bound(s) for the nutritional constraints.
      data_url (str, optional): URL to the Google Sheets document containing the "recipes", "nutrients",
          and "prices" sheets. Defaults to the provided URL.

    Returns:
      The daily price of the minimum cost diet (formatted to two decimal places).

    Side Effects:
      - Prints the daily cost of the diet.
      - Prints the diet composition (amounts of each recipe to include).
      - Prints a table of nutritional outcomes and identifies which nutrient constraints are binding.
    """
    recipes = (recipes
               .assign(parent_foodcode = lambda df: df["parent_foodcode"].apply(format_id),
                       ingred_code = lambda df: df["ingred_code"].apply(format_id))
               .rename(columns={"parent_desc": "recipe"}))
    
    nutrition = (nutrients
                 .assign(ingred_code = lambda df: df["ingred_code"].apply(format_id)))
    
    #display(nutrition.head())
    #nutrition.columns
    # commented out example ->
    # recipes[recipes["recipe"].str.contains("Vegetable lasagna", case=False)]
    # normalize weights to percentage terms. 
    recipes['ingred_wt'] = recipes['ingred_wt']/recipes.groupby(['parent_foodcode'])['ingred_wt'].transform("sum")
    # we're going to extend the recipes data frame to include the nutrient profiles of its ingredients (in 100g)
    df = recipes.merge(nutrition, how="left", on="ingred_code")
    # multiply all nutrients per 100g of an ingredient by the weight of that ingredient in a recipe.
    numeric_cols = list(df.select_dtypes(include=["number"]).columns)
    numeric_cols.remove("ingred_wt")
    df[numeric_cols] = df[numeric_cols].mul(df["ingred_wt"], axis=0)
    # sum nutrients of food codes (over the multiple ingredients)
    # python tip: one can merge dictionaries dict1 dict2 using **, that is: dict_merge = {**dict1, **dict2}. The ** effectively "unpacks" the key value pairs in each dictionary
    df = df.groupby('parent_foodcode').agg({**{col: "sum" for col in numeric_cols},
                                            "recipe": "first"})
    df.index.name = "recipe_id"
    food_names = df["recipe"]
    #df.head()
    #AT this point food and nutrient data has been solved for
    #moving to prices now
    prices = read_sheets(data_url, sheet="prices")[["food_code", "year", "price"]]
    prices["food_code"] = prices["food_code"].apply(format_id)
    prices = prices.set_index(["year", "food_code"])
    #print(prices.index.levels[0])
    
    # we'll focus on the latest price data
    prices = prices.xs("2017/2018", level="year")
    
    # drop rows of prices where the price is "NA"
    prices = prices.dropna(subset="price")    
    common_recipes = df.index.intersection(prices.index)
    
    # python tip: given a list of indices, "loc" both subsets and sorts. 
    df = df.loc[common_recipes]
    prices = prices.loc[common_recipes]
    
    # lets remap the price dataframe index to be the actual food names.
    prices.index = prices.index.map(food_names)
    
    A_all = df.T
    
    #print(prices.head())
    #print(A_all.head())
    #putting it together
    Amin = A_all.reindex(bmin.index).dropna(how='all')
    Amax = A_all.reindex(bmax.index).dropna(how='all')
    
    b = pd.concat([bmin, -bmax])
    A = pd.concat([Amin, -Amax])
    
    #solve
    p = prices
    tol = 1e-6 # Numbers in solution smaller than this (in absolute value) treated as zeros
    result = lp(p, -A, -b, method='highs')
    finalcost = f"{result.fun:.2f}"
    print(f"Cost of diet for {sex}'s of age {age} is ${finalcost} per day.")
    diet = pd.Series(result.x,index=prices.index)
    print("\nThe diet will consist of (in 100s of grams or milliliters):")
    print(round(diet[diet >= tol], 2))
    tab = pd.DataFrame({"Outcome":A.to_numpy()@diet.to_numpy(),"Recommendation":np.abs(b)})
    print("\nWith the following nutritional outcomes of interest:")
    print(tab)
    print("\nConstraining nutrients are:")
    excess = tab.diff(axis=1).iloc[:,1]
    print(excess.loc[np.abs(excess) < tol].index.tolist())
    return finalcost

def nutrient_search(search_term, nutrients, cut = False):
    """
    Filters the nutrients DataFrame based on the presence or absence of one or more search terms in the
    'Ingredient description' column. When multiple terms are provided, the function checks that at least one
    of the terms appears in the description.

    If `cut` is False (default), the function returns only the rows where the 'Ingredient description' 
    contains any of the specified search terms. If `cut` is True, it returns only the rows where the 
    description does NOT contain any of the search terms.

    Parameters:
        search_term (str or list of str): A single term or a list of terms to search for in the 
            'Ingredient description' column.
        nutrients (pd.DataFrame): The DataFrame containing nutrient data with an 'Ingredient description' column.
        cut (bool, optional): Determines the filtering mode. If False (default), select rows containing 
            any of the search terms. If True, select rows that do NOT contain any of the search terms.

    Returns:
        pd.DataFrame: The filtered DataFrame based on the specified condition.
    """
    if isinstance(search_term, list):
        pattern = '|'.join(term.lower() for term in search_term)
    else:
        pattern = search_term.lower()
    
    if cut:
        return nutrients[~nutrients['Ingredient description'].str.contains(pattern, regex=True)]
    else:
        return nutrients[nutrients['Ingredient description'].str.contains(pattern, regex=True)]