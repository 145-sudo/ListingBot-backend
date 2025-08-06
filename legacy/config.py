from enum import Enum


# main
SHEET_ID = "1ZE7BeE26iM43x_ympaIgOdl6lXWrwXg-PZZAKuIBEIw"

# test
# SHEET_ID = "1bSC1a80TZY3wRPIf07ixn8zE8g79wPn9dLt95RUho7c"

# Environment: dev or prod
ENVIRONMENT = "dev"


class SheetName(Enum):
    STORE_PRODUCTS = "OurStoreProducts"
    SSI = "SSI"
    KROLL = "Kroll"
    # ROTCHCO = "Rotchco"
    # CHATANOGA = "Chattanooga"


# general sheet name for fetching specific sheet column
class SheetColumns(Enum):
    SKU = "SKU"
    NAME = "Name"
    DESCRIPTION = "Description"
    PRICE = "Price"
    STOCK = "Stock"
    CATEGORY = "Category"
    SUBCATEGORY = "Subcategory"
    # LIST_DELIST = "List/Delist"
    LIST_DELIST = "Action"


# print(SheetName.USERS.value)
