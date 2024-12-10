# ML Uplift

### Setting Up Azure Secrets
```bash
# .streamlit/secrets.toml
azure_account_url = "https://<storage-account-name>.blob.core.windows.net/<container-name>"
azure_sas_token = "<SAS-token>"
```

### Build

```bash
docker build -t streamlit .
```

### Run

```bash
docker run -p 8501:8501 streamlit
```
