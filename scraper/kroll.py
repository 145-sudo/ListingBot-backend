import re
from time import sleep

import pandas as pd
from bs4 import BeautifulSoup

from legacy.util.fetch import fetch_url


def parse_html_kroll(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all product titles (this is a placeholder, you'll need to inspect the actual HTML)
    # Example: assuming product titles are in <h2> tags with class 'product-name'
    scripts = soup.find_all("script")

    for i, scr in enumerate(scripts, 1):
        if "var dl4Objects" in scr.text:
            print(f"Found the script {i} containing dl4Objects.")
            script = scr.text.strip()
            # print(script[:1000])  # Print the first 1000 characters for inspection
            break
    else:
        script = None

    # if scripts is None or len(scripts) < 11:
    #     print("No scripts found.")
    #     return None

    # script = scripts.strip()
    # script = scripts[11].text.strip()
    # print(script[:1000])  # Print the first 1000 characters of the script for inspection


    # Use regular expression to find the dl4Objects list
    match = re.search(r"var dl4Objects = (\[.*?\]);", script, re.DOTALL)
    print(match)
    if match:
        dl4Objects_str = match.group(1)
        # Convert the string representation of the list to an actual list
        dl4Objects = eval(dl4Objects_str)
        # print(dl4Objects)
        print(f"Found {len(dl4Objects)} objects.")
        return dl4Objects
    else:
        print("dl4Objects not found in the script.")


def convert_to_df(products):
    """
    Convert the list of dictionaries to a pandas DataFrame
    """
    df = pd.DataFrame(products[1]["ecommerce"]["items"])
    df.drop(["affiliation", "item_list_name"], axis=1, inplace=True)
    return df


def scrape_kroll(url):
    content = fetch_url(url)
    products = parse_html_kroll(content)
    df = convert_to_df(products)
    return df


def scrape_kroll_categories(categories):
    """
    Scrape all categories from the given categories list.
    Returns a cleaned, merged DataFrame of all products.
    """
    dfs = {}
    for i, c in enumerate(categories, 1):
        print(c)
        url = c.get("url")
        df = scrape_kroll(url)
        dfs[i] = df
        sleep(1)
        # break  # Uncomment for debugging single category

    merged_df = pd.concat(dfs.values(), ignore_index=True)

    # Data cleaning
    merged_df["category"] = merged_df["item_category"]
    merged_df["sub_category"] = merged_df["item_category2"]

    remove_columns = [
        "item_category",
        "item_category2",
        "item_list_id",
        "index",
    ]

    # Only drop columns that exist in merged_df
    merged_df = merged_df.drop(
        columns=[col for col in remove_columns if col in merged_df.columns]
    )

    return merged_df
