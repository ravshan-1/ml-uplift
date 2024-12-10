import logging
from io import BytesIO

import streamlit as st
from azure.storage.blob import BlobServiceClient


class BlobStorageService:
    def __init__(self):
        try:
            self.container_name = "ml_promo"
                        
            self.blob_service_client = BlobServiceClient(account_url=st.secrets.get("azure_account_url"), credential=st.secrets.get("azure_sas_token"))

        except Exception as e:
            logging.error(f"Error initializing BlobStorageService: {e}")
            raise

    def get_blob(self, blob_path: str):
        try:            
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_path)
            
            blob_data = blob_client.download_blob()

            return BytesIO(blob_data.readall())
        
        except Exception as e:
            logging.error(f"Error loading data from blob: {e}")
            raise
        
    def upload_blob(self, file: bytes, blob_path: str):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_path)

            blob_client.upload_blob(file, overwrite=True)

        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            raise


blob_service = BlobStorageService()


def upload_promo_raw(file):
    """
    """
    try:
        blob_service.upload_blob(file, blob_path=f"source_files/pw_{st.session_state["week_num"]}.xlsx")

        st.session_state["file_uploaded"] = True
        st.rerun()
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        raise