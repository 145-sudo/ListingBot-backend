from config import SheetName, SheetColumns


def get_attribute(sheet_name: str, attribute_name: SheetColumns):
    if SheetName.SSI.value == sheet_name:
        if attribute_name == SheetColumns.SKU:
            return "SKU"
        elif attribute_name == SheetColumns.NAME:
            return "Name"
        elif attribute_name == SheetColumns.DESCRIPTION:
            return "Description"
        elif attribute_name == SheetColumns.PRICE:
            return "Price"
        elif attribute_name == SheetColumns.STOCK:
            return "Stock"
        elif attribute_name == SheetColumns.CATEGORY:
            return "category"
        elif attribute_name == SheetColumns.SUBCATEGORY:
            return "sub_category"
        elif attribute_name == SheetColumns.LIST_DELIST:
            return SheetColumns.LIST_DELIST.value

    elif SheetName.KROLL.value == sheet_name:
        if attribute_name == SheetColumns.SKU:
            return "item_id"
        elif attribute_name == SheetColumns.NAME:
            return "item_name"
        elif attribute_name == SheetColumns.DESCRIPTION:
            return "Description"
        elif attribute_name == SheetColumns.PRICE:
            return "price"
        elif attribute_name == SheetColumns.STOCK:
            # return "Stock"
            return None
        elif attribute_name == SheetColumns.CATEGORY:
            return "category"
        elif attribute_name == SheetColumns.SUBCATEGORY:
            return "sub_category"
        elif attribute_name == SheetColumns.LIST_DELIST:
            return SheetColumns.LIST_DELIST.value

    elif SheetName.ROTCHCO.value == sheet_name:  # TODO: Add Rotchco attributes
        if attribute_name == SheetColumns.SKU:
            return "item_id"
        elif attribute_name == SheetColumns.NAME:
            return "item_name"
        elif attribute_name == SheetColumns.DESCRIPTION:
            return "Description"
        elif attribute_name == SheetColumns.PRICE:
            return "price"
        elif attribute_name == SheetColumns.LIST_DELIST:
            return SheetColumns.LIST_DELIST.value
    else:
        return None
