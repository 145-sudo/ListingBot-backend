import pandas as pd
from bs4 import BeautifulSoup, Tag

from legacy.util.fetch import fetch_url

base_url = "https://ssisports.net"


def parse_html_ssi(content):
    products = []

    soup = BeautifulSoup(content, "html.parser")
    product_list = soup.find_all("div", class_="product-list")

    if product_list is None or len(product_list) < 1:
        print("No product_list found.")
        return products

    if product_list and len(product_list) > 0:
        first_product = product_list[0]

        # Filter only Tag children (skip strings, comments, etc.)
        children_tags = [
            child
            for child in first_product.children  # type:ignore
            if isinstance(child, Tag)
        ]

        grouped_products = []

        # Process every 4 divs as one product group
        for i in range(0, len(children_tags), 4):
            group = children_tags[i : i + 4]
            if len(group) == 4:
                product_dict = {
                    "image": group[0],
                    "attributes": group[1],
                    "details": group[2],
                    "hr": group[3],
                }
                grouped_products.append(product_dict)

        # Example: print class names of each group
        for idx, product in enumerate(grouped_products, 1):
            print(f"Product {idx}:")
            print(f"  Name: {product['attributes'].find('h5').text}")
            # print(f"  Description: {'/n'.join([p.text for p in product['attributes'].find_all('ul') if p is not None])}")
            # print(f"  Price: {product['details'].find(class_='product-details-price').h3.text.strip()}")
            # print(f"  Stock: {product['details'].find(class_='product-details-available').span.contents[2].text.strip()}")
            print(
                f"  SKU: {product['details'].find(class_='product-details-item-number').contents[2].text.strip()}"
            )
            try:
                stock = (
                    product["details"]
                    .find(class_="product-details-available")
                    .span.contents[2]
                    .text.strip()
                )
            except Exception as e:
                print(
                    f"ERRROR accessing stock 'span.contents[2].text.strip()' in {product['details'].find(class_='product-details-available')}: {e}"
                )
                stock = None

            try:
                price = (
                    product["details"]
                    .find(class_="product-details-price")
                    .h3.text.strip().strip('$')
                )
            except Exception as e:
                print(
                    f"ERROR accessing price '.h3.text.strip()' in {product['details'].find(class_='product-details-price')}: {e}"
                )
                price = None
            description = "\n".join(
                [
                    p.get_text(strip=True)
                    for p in product["attributes"].find_all("ul")
                    if p is not None
                ]
            )
            name_element = product["attributes"].find("h5").find("a")
            link = f"{base_url}{name_element.get('href')}"
            products.append(
                {
                    "SKU": product["details"]
                    .find(class_="product-details-item-number")
                    .contents[2]
                    .text.strip(),
                    "Name": product["attributes"].find("h5").text,
                    "Description": description,
                    # "Image": image,
                    "Price": price,
                    "Stock": stock,
                    "Link": link,
                }
            )

            # print(f"  Image div class: {product['image'].get('class')}")
            # print(f"  Attributes div class: {product['attributes'].get('class')}")
            # print(f"  Details div class: {product['details'].get('class')}")
            # print(f"  HR div class: {product['hr'].get('class')}")
            # print()

    return products


def convert_to_df(products):
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(products)
    return df


def scrape_ssi(url):
    content = fetch_url(url)
    products = parse_html_ssi(content)
    df = convert_to_df(products)
    return df


def scrape_ssi_categories(category_list):
    """
    Scrape all categories from the given category_list and base_url.
    Returns a merged DataFrame of all products.
    """
    dfs = {}
    for i, c in enumerate(category_list, 1):
        print(c)
        url = f"{base_url}{c.get('url')}"
        df = scrape_ssi(url)
        df["category"] = c.get("category")
        df["sub_category"] = c["sub_category"].split("(")[0].strip()
        dfs[i] = df

    merged_df = pd.concat(dfs.values(), ignore_index=True)
    return merged_df
