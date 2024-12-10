import logging
from io import BytesIO

import pandas as pd

from utils.azure import blob_service


def load_promo_data(df: pd.DataFrame, promo_type: str, week_num: str) -> None:
    if promo_type == "aba":
        filtered_df = df[df["promo_name"].str.contains(f"АБА {week_num}")]
    else:
        filtered_df = df[df["promo_name"].str.contains(f"СВП {week_num}")]

    columns = [
        "id",
        "item_name",
        "item_subcategorylvl5",
        "shelflife",
        "discount_percentage",
        "brand",
        "analogs_count"
    ]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df[columns].to_excel(writer, index=False)

    output.seek(0)
    excel_data = output.read()

    blob_service.upload_blob(file=excel_data, blob_path=f"prepared_to_preprocess/{promo_type.lower()}{week_num}_prep.xlsx")


# !TODO: Refactor.
def prepare_data(week_num: str):
    """
    Prepares and processes promotional data, calculates the count of analogous items for each entry,
    and saves the processed data into separate Excel files based on promo names.
    """
    def get_promoted_items_count(row: pd.Series) -> int:
        """
        Helper function to calculate the count of analogous items for a given row based on item subcategory
        and the date range.
        """
        item_group = row["item_subcategorylvl5"]
        start_dt = row["start_date"]
        end_dt = row["end_date"]

        filtered_df = fpi_df[fpi_df["item_subcategorylvl5"] == item_group]

        analogs_count = filtered_df[
            (filtered_df["start_date"] <= end_dt) & (filtered_df["end_date"] >= start_dt)
        ].shape[0]

        return analogs_count
    
    full_promo_info = blob_service.get_blob(blob_path="source_files/full_promo_info.xlsx")

    fpi_df = pd.read_excel(full_promo_info)

    fpi_df["start_date"] = pd.to_datetime(fpi_df["start_date"], errors='coerce')
    fpi_df["end_date"] = pd.to_datetime(fpi_df["end_date"], errors='coerce')

    fpi_df.loc[:, "analogs_count"] = fpi_df.apply(get_promoted_items_count, axis=1)

    try:
        load_promo_data(df=fpi_df, promo_type="aba", week_num=week_num)
        load_promo_data(df=fpi_df, promo_type="svp", week_num=week_num)
    
    except Exception as e:
        logging.error(f"Error {e}")
        raise