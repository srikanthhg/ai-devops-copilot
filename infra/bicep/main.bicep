targetScope = 'subscription'

param location string = resourceGroup().location
param openAiName string = 'copilot-openai-${uniqueString(resourceGroup().id)}'

resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  sku: { name: 'S0' }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: toLower(openAiName)
    apiProperties: {
      statisticsEnabled: true
    }
  }
}

// TODO: Add Azure AI Search, Container Apps, Managed Identity
