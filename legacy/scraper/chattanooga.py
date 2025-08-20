import pandas as pd
from bs4 import BeautifulSoup, Tag

from legacy.util.fetch import fetch_url


def parse_html_chattanooga(content):
    soup = BeautifulSoup(content, "html.parser")
    products_section = soup.find_all(
        "section", class_="list-of-products gutter-bottom-0"
    )

    # Assuming products_section is a list of BeautifulSoup Tag objects
    if products_section and len(products_section) > 0:
        product_section = products_section[0]  # Get the first section
        div_children = [
            child
            for child in product_section.children
            if isinstance(child, Tag) and child.name == "div"
        ]
        print("Immediate div children of product_section:")
        # for div in div_children:
        # print(f"  - {div.get('class')}")
    else:
        print("No product_section found.")
        return []

    # parsing
    products_data = []

    if div_children:
        for product_div in div_children:
            product_info = {}

            # Extract image URL
            img_tag = product_div.find("img")
            if img_tag:
                product_info["Image_URL"] = img_tag.get("src")

            # Extract Product Name
            title_tag = product_div.find("p", class_="product-title")
            if title_tag and title_tag.find("a"):
                product_info["Product_Name"] = title_tag.find("a").text.strip()

            # Extract Product ID (SKU)
            id_tag = product_div.find("div", class_="product-id")
            if id_tag and id_tag.find("span"):
                # Assuming the SKU is the text directly within the first span
                product_info["SKU"] = id_tag.find("span").text.strip()

            # Extract Product Properties
            properties_tag = product_div.find("p", class_="product-properties")
            if properties_tag:
                # Clean up the text and split by the pipe | separator
                properties_text = (
                    properties_tag.text.strip().replace("\n", "").replace("\r", "")
                )
                property_list = [prop.strip() for prop in properties_text.split("|")]
                properties_dict = {}
                for prop in property_list:
                    if ": " in prop:
                        key, value = prop.split(": ", 1)
                        properties_dict[key.strip()] = value.strip()
                product_info["Properties"] = properties_dict
            else:
                product_info["Properties"] = {}

            # Extract Stock Status (if needed, based on the HTML structure)
            # The provided HTML doesn't show a clear stock status, but you could add logic here
            # based on how stock status is represented on the page.
            stock_tag = product_div.find("p", class_="product-stock-status")
            if stock_tag:
                product_info["Stock_Status"] = stock_tag.text.strip()
            else:
                product_info["Stock_Status"] = "Not specified"  # Or some other default

            products_data.append(product_info)


def convert_to_df(products_data):
    # Create a DataFrame from the extracted data
    df = pd.DataFrame(products_data)
    df["Properties"] = df["Properties"].astype(str)
    return df


def scrape_chattanooga(url):
    content = fetch_url(url)
    products = parse_html_chattanooga(content)
    df = convert_to_df(products)
    return df
