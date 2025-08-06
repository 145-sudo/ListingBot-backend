import pandas as pd


def scrape_rothco_categories(categories):
    """
    Scrape all categories from the given categories list.
    Returns a cleaned, merged DataFrame of all products.
    """
    # return None
    dfs = {}
    # for i, c in enumerate(categories, 1):
    #     print(c)
    #     url = c.get("url")
    #     df = scrape_kroll(url)
    #     dfs[i] = df
    #     sleep(1)
    #     # break  # Uncomment for debugging single category

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
