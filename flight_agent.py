import pandas as pd
import dateparser
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

from langchain_core.output_parsers import PydanticOutputParser
from langchain.schema import HumanMessage

my_api_key = ""
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=my_api_key
)

# Load flight data
df = pd.read_json('flights.jsonl', lines=True)


# Memory
conversation_memory = {}
pending_flight = None
pending_confirmation = False

# Main class
class FlightIntent(BaseModel):
    origin: str = Field(description="Departure city")
    destination: str = Field(description="Arrival city")
    date_start: str = Field(description="Start date in YYYY-MM-DD format, or 'unknown'")
    date_end: str = Field(description="End date in YYYY-MM-DD format, or 'unknown'")

intent_parser = PydanticOutputParser(pydantic_object=FlightIntent)

# Default prompt
intent_prompt_template = PromptTemplate(
    input_variables=["user_input", "today", "memory"],
    template="""
You are an assistant that extracts flight search parameters from user input.

Today's date is: {today}

The previous search memory is:
{memory}

User input is:
"{user_input}"

Please return the updated full flight search intent in JSON format matching this Pydantic model:

{format_instructions}

Rules:
- If user input only mentions part of the fields, fill missing fields using memory.
- If user input provides a date range (e.g. "next week"), map it to date_start and date_end.
- If user input provides a single date, set both date_start and date_end to that date.
- Use 'unknown' if you cannot determine the value.
"""
)

# Extract intent from user input
def extract_intent(user_input):
    today = datetime.today().strftime("%Y-%m-%d")
    memory_str = str(conversation_memory)

    prompt = intent_prompt_template.format(
        user_input=user_input,
        today=today,
        memory=memory_str,
        format_instructions=intent_parser.get_format_instructions()
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    intent = intent_parser.parse(response.content)
    return intent

# Date Normalization
def normalize_date(date_str):
    if date_str == "unknown" or not date_str.strip():
        return "unknown"
    parsed_date = dateparser.parse(date_str)
    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    else:
        return "unknown"

# Search flights
def search_flight(intent):
    global pending_flight, pending_confirmation

    filtered_df = df.copy()

    if intent.origin:
        filtered_df = filtered_df[filtered_df['origin'].str.lower() == intent.origin.lower()]
    if intent.destination:
        filtered_df = filtered_df[filtered_df['destination'].str.lower() == intent.destination.lower()]

    if intent.date_start != "unknown" and intent.date_end != "unknown":
        filtered_df = filtered_df[
            (filtered_df['date'] >= intent.date_start) &
            (filtered_df['date'] <= intent.date_end)
        ]

    if filtered_df.empty:
        print("No matching flights found.\n")
        return

    top_flight = filtered_df.sort_values(by='price').head(1).iloc[0]

    pending_flight = top_flight
    pending_confirmation = True

    print(f"\n--- Found a flight ---\n")
    print(f"From: {top_flight['origin']}")
    print(f"To: {top_flight['destination']}")
    print(f"Date: {top_flight['date']}")
    print(f"Price: ${top_flight['price']}")
    print(f"Flight Number: {top_flight['flight_number']}")
    print("\nWould you like to book this flight? (yes/no/change)\n")

# Main loop
if __name__ == "__main__":
    print("🇦🇪UAE Flight Booking Agent")
    print("Type your request. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        if pending_confirmation:
            if user_input.lower() in ["yes", "y", "ok", "confirm", "sure"]:
                print(f"\nBooking confirmed! 🎫")
                print(f"Flight {pending_flight['flight_number']} from {pending_flight['origin']} to {pending_flight['destination']} on {pending_flight['date']} at price ${pending_flight['price']}\n")
                print("Thank you for using the Flight Agent. Goodbye!\n")
                break
            elif user_input.lower() in ["no", "n", "change", "different"]:
                print("\nOkay, please provide new request or modify your search.\n")
                pending_flight = None
                pending_confirmation = False
            else:
                print("\nPlease reply with yes / no / change.\n")
        else:
            intent = extract_intent(user_input)

            intent.date_start = normalize_date(intent.date_start)
            intent.date_end = normalize_date(intent.date_end)

            if intent.date_start != "unknown":
                today_date = datetime.today().date()
                parsed_start = datetime.strptime(intent.date_start, "%Y-%m-%d").date()
                if parsed_start < today_date:
                    print("The date you entered is in the past. Please enter a valid future date.\n")
                    continue

            conversation_memory['origin'] = intent.origin
            conversation_memory['destination'] = intent.destination
            conversation_memory['date_start'] = intent.date_start
            conversation_memory['date_end'] = intent.date_end

            search_flight(intent)
