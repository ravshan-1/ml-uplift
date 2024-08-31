import streamlit as st
import pandas as pd

@st.dialog(title="Filter", width="large")
def filter_df():
    """
    """
    st.session_state["available_brands"] = st.session_state["df"]["Бренд"].unique()
    st.session_state["available_products"] = st.session_state["df"]["Наименование"].unique()

    selected_brands = st.multiselect(
        label="Choose brand",
        options=st.session_state.get("available_brands"),
        default=st.session_state.get("selected_brands"),
    )

    selected_products = st.multiselect(
        label="Choose product name",
        options=st.session_state.get("available_products"),
        default=st.session_state.get("selected_products"),
    )

    temp1, temp2, _ = st.columns([0.15, 0.15, 0.7])
    
    with temp1:
        apply = st.button(
            label="Apply",
            on_click=lambda: st.session_state.update(
                {
                    "selected_brands": selected_brands,
                    "selected_products": selected_products,
                }
            ),
            use_container_width=True
        )
    
    with temp2:
        reset = st.button(
            label="Reset",
            on_click=lambda: st.session_state.update(
                {
                    "df": pd.read_excel(st.session_state.get("xlsx_file")),
                    "selected_brands": [],
                    "selected_products": [],
                }
            ),
            use_container_width=True,
        )
    
    if apply or reset:
        st.rerun()

@st.dialog(title="Upload file", width="large")
def upload_file():
    """
    """
    file = st.file_uploader(
        label="**None**",
        type=["xlsx"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    is_clicked = st.button(
        label="Upload",
        on_click=None,
        use_container_width=False,
    )
    
    if is_clicked:
        if file:
            st.session_state["xlsx_file"] = file
            st.session_state["df"] = pd.read_excel(file)
            st.session_state["is_file_uploaded"] = True
            st.rerun()
        else:
            st.markdown(":grey[Please choose a file to upload!]")
        
def close_file():
    """
    """
    st.session_state.clear()
