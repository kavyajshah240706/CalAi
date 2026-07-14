from google import genai

# Initialize the client with your NEW API key
client = genai.Client(api_key="")

# Make a request to the model
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Explain how API keys work in one sentence.'
)

print(response.text)