import boto3
import json

# Initialize the Bedrock Runtime client
client = boto3.client("bedrock-runtime")

# Replace these with your actual values
GUARDRAIL_ID = "tobzl8izlk70"
GUARDRAIL_VERSION = "1"  # Use the current version of your guardrail (must be a number or "DRAFT")
TEXT_TO_TEST = "My name is John Smith and my SSN is 123-45-6789."
SOURCE_TYPE = "INPUT"  # or "OUTPUT"

def apply_guardrail(text, source="INPUT"):
    try:
        response = client.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[
                {
                    "text": {
                        "text": text
                    }
                }
            ]
        )
        print("✅ Guardrail applied successfully!")
        print(json.dumps(response, indent=2))
        return response

    except client.exceptions.ValidationException as ve:
        print("Validation error:", ve)
    except client.exceptions.ResourceNotFoundException as rnfe:
        print("Guardrail not found:", rnfe)
    except Exception as e:
        print("Unexpected error:", e)

if __name__ == "__main__":
    apply_guardrail(TEXT_TO_TEST, source=SOURCE_TYPE)

