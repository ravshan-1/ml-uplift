from io import BytesIO
from typing import Literal

import numpy as np
import pandas as pd
import streamlit as st

from utils.azure import blob_service


def adjust_promo(promo_df: pd.DataFrame, week_num: str) -> pd.DataFrame:
    """
    This function adjusts the promo names and discount values for a given promotion week DataFrame.
    """
    start_date = promo_df["start_date"].unique()[0]
    end_date = promo_df["end_date"].unique()[0]
    
    promo_name_template = f"{week_num} ({start_date}-{end_date})"
    
    promo_name_svp = f"СВП {promo_name_template}"
    promo_name_aba = f"АБА {promo_name_template}"
    
    promo_df["promo_name"] = np.where(
        promo_df["promo_type"].str.contains("СВП", na=False), 
        promo_name_svp,
        promo_name_aba,
    )
    promo_df["promo_type"] = promo_df["promo_name"].str.extract(r'(^\S{3})')

    promo_df["discount"] = promo_df["discount"].fillna(-0.20)
    promo_df["discount"] = (-promo_df["discount"]).round(2).clip(upper=0.35)

    return promo_df

def enrich_promo_with_hierarchy(promo_df: pd.DataFrame) -> pd.DataFrame:
    """
    This function enriches the promotion week data with product hierarchy details by joining it with the product hierarchy table.
    """
    try:
        product_hierarchy = blob_service.get_blob(blob_path="source_files/products_hierarchy.xlsx")
    except Exception as e:
        raise e

    product_hierarchy_df = pd.read_excel(product_hierarchy)

    promo_df = promo_df.drop(columns=['item_name'])

    enriched_df = promo_df.merge(
        product_hierarchy_df[
            ['item_id', 'product_long_desc', 'lvl3_category_name', 'lvl4_subcategory_name', 'lvl5_subsubcategory_name']
        ],
        on='item_id',
        how='left',
    )
    
    enriched_df = enriched_df.rename(columns={
        'product_long_desc': 'item_name',
        'lvl3_category_name': 'item_category',
        'lvl4_subcategory_name': 'item_subcategory',
        'lvl5_subsubcategory_name': 'item_subcategorylvl5',
        'discount': 'discount_percentage',
    })

    return enriched_df

def add_details_from_pim(promo_df: pd.DataFrame) -> pd.DataFrame:
    """
    This function further enriches the promotion week data with details from a PIM (Product Information Management) system.
    """
    try:
        pim_table = blob_service.get_blob(blob_path="source_files/pim_table.xlsx")
    except Exception as e:
        raise e

    pim_df = pd.read_excel(pim_table)

    enriched_df = promo_df.merge(
        pim_df[['id', 'shelflife', 'brand']],
        left_on='item_id',
        right_on='id',
        how='left',
    )

    enriched_df['shelflife'] = enriched_df['shelflife'].fillna(0)

    return enriched_df

def append_promo_records_to_fpi(week_num: str, promo_df: pd.DataFrame, fpi_df: pd.DataFrame, promo_type: Literal["СВП", "АБА"]) -> pd.DataFrame:
    """
    This function appends new promotion records to an existing full promo info DataFrame.
    """
    promo_df = promo_df.reindex(columns=fpi_df.columns)

    promo_name = f"{promo_type} {week_num}"

    fpi_df = fpi_df[~fpi_df["promo_name"].str.contains(promo_name, na=False)]

    combined_df = pd.concat([fpi_df, promo_df], ignore_index=True)

    return combined_df


def run_script():
    """
    This function is the main execution function that orchestrates the data adjustments and merges, and saves the result to an Excel file.
    """
    week_num = st.session_state.get("week_num")

    promo_week = blob_service.get_blob(blob_path=f"promo_week_raw/pw_37.xlsx")

    promo_df = pd.read_excel(promo_week)

    adjusted_promo = adjust_promo(promo_df, week_num)

    eniched_promo = enrich_promo_with_hierarchy(adjusted_promo)

    final_df = add_details_from_pim(eniched_promo)

    df = final_df

    # Separate new promo week's SVP and ABA records
    svp_records = df[df["promo_type"].str.contains("СВП")]
    aba_records = df[df["promo_type"].str.contains("АБА")]

    # Load the full_promo_info.xlsx
    try:
        full_promo_info = blob_service.get_blob(blob_path="source_files/full_promo_info.xlsx")
    except Exception as e:
        raise e

    fpi_df = pd.read_excel(full_promo_info)

    # Append the new svp and aba records to the fpi_df
    fpi_df = append_promo_records_to_fpi(week_num, svp_records.copy(), fpi_df.copy(), promo_type = "СВП")
    fpi_df = append_promo_records_to_fpi(week_num, aba_records.copy(), fpi_df.copy(), promo_type = "АБА")

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        fpi_df.to_excel(writer, index=False)

    output.seek(0)
    excel_data = output.read()

    blob_service.upload_blob(file=excel_data, blob_path="source_files/full_promo_info.xlsx")

    return None