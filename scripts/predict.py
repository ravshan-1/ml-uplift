import zipfile
from io import BytesIO

import joblib
import pandas as pd
import streamlit as st

from utils.azure import blob_service
from .prepare import prepare_data
from .preprocess import preprocess


def is_big_demand(row: pd.Series):
    if row["demand_daily_before"] > 50:
        row["big_demand"] = 1
    else:
        row["big_demand"] = 0

    return row

def is_big_percentage(row: pd.Series):
    if row["discount_percentage"] >= 0.35:
        row["big_percentage"] = 1
    else:
        row["big_percentage"] = 0
    
    return row

def predict_1(df: pd.DataFrame, promo_type: str, week_num: int):
    FEATURE_COLUMNS = [
        'category_group', 'analogs_group', 'brand_group', 'big_percentage', 'big_demand', 'demand_daily_before'
    ]

    if promo_type == "СВП":
        type_name = "svp"
        model = joblib.load("./models/svp/svp_xgb_001.joblib")
    elif promo_type == "АБА":
        type_name = "aba"
        model = joblib.load("./models/aba/aba_lgb_003.joblib")

    df = df.apply(is_big_demand, axis=1)
    df = df.apply(is_big_percentage, axis=1)

    X = df[FEATURE_COLUMNS]
    predictions = model.predict(X)

    df.loc[:, "demand_daily_during"] = predictions
    df.loc[:, "uplift"] = df["demand_daily_during"] / df["demand_daily_before"]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    excel_data = output.read()

    blob_service.upload_blob(file=excel_data, blob_path=f"predictions/{type_name}{week_num}.xlsx")


@st.dialog(title="Predict", width="large")
def predict(week_num: str):
    """
    """

    with st.status(label="Processing...", expanded=True) as status:
        st.write("Preparing data...")
                
        prepare_data(st.session_state.get("week_num"))

        st.write("Loading preprocessed data...")
        preprocess(int(week_num))

        svp_preprocessed = blob_service.get_blob(blob_path=f"data_for_predictions/svp{week_num}.xlsx")
        aba_preprocessed = blob_service.get_blob(blob_path=f"data_for_predictions/aba{week_num}.xlsx")

        st.write("Predicting...")
        svp_df = pd.read_excel(svp_preprocessed)
        aba_df = pd.read_excel(aba_preprocessed)

        predict_1(svp_df, promo_type="СВП", week_num=int(week_num))
        predict_1(aba_df, promo_type="АБА", week_num=int(week_num))

        status.update(label="Complete!", state="complete", expanded=False)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        svp_blob = blob_service.get_blob(blob_path=f"predictions/svp{week_num}.xlsx")
        svp_data = svp_blob.read()
        zf.writestr(f"svp_{week_num}.xlsx", svp_data)

        aba_blob = blob_service.get_blob(blob_path=f"predictions/aba{week_num}.xlsx")
        aba_data = aba_blob.read()
        zf.writestr(f"aba_{week_num}.xlsx", aba_data)

    zip_buffer.seek(0)

    @st.fragment
    def download_button():
        """
        """
        st.download_button(
            label="Download All Predictions",
            data=zip_buffer,
            file_name=f"predictions_week_{week_num}.zip",
            mime="application/zip"
        )

    download_button()