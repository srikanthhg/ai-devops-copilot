# scripts/populate_search_index.py
from azure.search.documents import SearchIndexClient, SearchClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchFieldDataType
from azure.core.credentials import AzureKeyCredential
import os

index_name = "devops-runbooks"
client = SearchIndexClient(os.getenv("AZURE_SEARCH_ENDPOINT"), AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")))

# Create index if not exists
if index_name not in [i.name for i in client.list_indexes()]:
    index = SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String)
        ]
    )
    client.create_index(index)

# Upload sample runbook
search_client = SearchClient(os.getenv("AZURE_SEARCH_ENDPOINT"), index_name, AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")))
docs = [
    {"id": "1", "title": "AKS ImagePullBackOff Fix", "content": "Check ACR credentials, verify image tag exists, ensure managed identity has AcrPull role."},
    {"id": "2", "title": "Terraform State Lock Error", "content": "Run 'terraform force-unlock <LOCK_ID>' after verifying no concurrent runs. Check Azure Blob lease."}
]
search_client.upload_documents(documents=docs)
print("✅ Index populated")
