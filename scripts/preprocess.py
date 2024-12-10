from io import BytesIO

import pandas as pd

from utils.azure import blob_service


def get_shelflife_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorizes the 'shelflife' of items into distinct groups and adds a new column to the DataFrame to reflect these groups.
    """
    df = df.reset_index(drop=True)
    df = df.assign(shelflife_group=0)
    df.loc[(df['shelflife'] == 0) | (df["shelflife"] > 90), "shelflife_group"] = 1
    df.loc[(df['shelflife'] > 25) & (df["shelflife"] <= 90), "shelflife_group"] = 2
    df.loc[(df['shelflife'] > 0) & (df["shelflife"] <= 25), "shelflife_group"] = 3
    df["shelflife_group"].value_counts()

    return df

def get_analogs_group(row: pd.Series) -> pd.Series:
    """
    Categorizes the number of promoted analogs into distinct groups.
    """
    if row["analogs_count"] == 1:
        row["analogs_group"] = 1
    elif row["analogs_count"] > 1 and row["analogs_count"] <= 9:
        row["analogs_group"] = 2
    else:
        row["analogs_group"] = 3

    return row

def get_demand_daily_before(df: pd.DataFrame, week_num: int) -> pd.DataFrame:
    """
    Calculates the daily demand for items based on historical autoorder data.
    """
    autoorder_before = blob_service.get_blob(blob_path=f"item_autoorders/svp{week_num - 1}_autoorder_period.xlsx")
    autoorder_before_before = blob_service.get_blob(blob_path=f"item_autoorders/svp{week_num - 2}_autoorder_period.xlsx")

    auto_df_before = pd.read_excel(autoorder_before)
    auto_df_before_before = pd.read_excel(autoorder_before_before)

    df = df.merge(
        auto_df_before[['item_id', 'autoorder_total']], 
        left_on='id',
        right_on='item_id',
        how='left'
    )
    df.rename(columns={'autoorder_total': 'autoorder_total_before'}, inplace=True)


    df = df.merge(
        auto_df_before_before[['item_id', 'autoorder_total']], 
        left_on='id', 
        right_on='item_id', 
        how='left'
    )
    df.rename(columns={'autoorder_total': 'autoorder_total_before_before'}, inplace=True)
    

    # Calculate daily demands
    df['demand_daily_before'] = df['autoorder_total_before'] / 7
    df['demand_daily_before_before'] = df['autoorder_total_before_before'] / 7

    # Calculate uplift
    df['uplift_before'] = df['demand_daily_before'] / df['demand_daily_before_before']

    # Adjust demand if uplift is too high
    df.loc[df['uplift_before'] >= 1.6, 'demand_daily_before'] = df['demand_daily_before_before']

    # Drop unnecessary columns
    df.drop(columns=['item_id_x', 'item_id_y', 'autoorder_total_before', 'autoorder_total_before_before'], inplace=True)

    return df

def preprocess_for_model(promo_name: str, week_num: int) -> pd.DataFrame:
    """
    Preprocesses promotional data for model input by applying various transformations and mappings.
    """
    brand_groups = blob_service.get_blob(blob_path="feature_maps/brand_groups_map.csv")
    category_groups = blob_service.get_blob(blob_path="feature_maps/category_groups_map.csv")

    brand_map = pd.read_csv(brand_groups).set_index('brand')['brand_group'].to_dict()
    category_map = pd.read_csv(category_groups).set_index('item_subcategorylvl5')['category_group'].to_dict()

    promo_week = blob_service.get_blob(blob_path=f"prepared_to_preprocess/{promo_name}{week_num}_prep.xlsx")
    promo_df = pd.read_excel(promo_week)

    promo_df.loc[:, "brand_group"] = promo_df["brand"].str.lower().map(brand_map)
    promo_df.loc[:, "category_group"] = promo_df["item_subcategorylvl5"].map(category_map)
    
    promo_df = get_shelflife_group(promo_df)
    promo_df = promo_df.apply(get_analogs_group, axis=1)
    
    promo_df.fillna(
        {
        "shelflife": 1,
        "brand_group": 1,
        "category_group": 1,
        "discount_percentage": 0.20,
        }, 
        inplace=True,
    )

    promo_df = get_demand_daily_before(promo_df.copy(), week_num=week_num)

    return promo_df


def save_and_upload_to_blob(df: pd.DataFrame, blob_name: str):
    """
    Save a DataFrame to an Excel file and upload it to a blob storage.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    output.seek(0)
    excel_data = output.read()

    blob_service.upload_blob(file=excel_data, blob_path=f"data_for_prediction/{blob_name}")


def preprocess(week_num: int):
    """
    Preprocesses and uploads promotional data for 'aba' and 'svp' containers for the given week number.
    """
    for container in ["aba", "svp"]:
        df = preprocess_for_model(container, week_num)
        blob_name = f"{container}{week_num}.xlsx"
        save_and_upload_to_blob(df, blob_name)
