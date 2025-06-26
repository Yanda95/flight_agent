import pandas as pd
import dateparser
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from typing import Optional, Dict, Any

from langchain.schema import HumanMessage
import json

my_api_key = ""
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=my_api_key
)

# Load flight data
df = pd.read_json('flights.jsonl', lines=True)
df['date'] = pd.to_datetime(df['date'])
df_unique = df.drop_duplicates(subset=['origin', 'destination'])
all_routes = df_unique[['origin', 'destination']].drop_duplicates().reset_index(drop=True)

# Memory
conversation_memory: Dict[str, Any] = {}
pending_flight = None
pending_confirmation = False

# Simplified Prompt
simple_prompt = PromptTemplate(
    input_variables=["user_input", "today", "memory", "routes"],
    template="""
Today is {today}.
You are a helpful flight booking assistant.

Instructions:
1. If the user specifies any booking information (like origin, destination, or date), use it to update the intent.
2. Combine it with the memory to extract a complete intent (if possible) in JSON format like:
   Intent: {{"origin": ..., "destination": ..., "date_start": ..., "date_end": ...}}
3. If the input is general conversation, or if booking information is incomplete, reply in natural language starting with:
   Reply: ...

Use memory to preserve previous origin/destination/date values unless the user gives new ones.
Do not fabricate information. Use only user input and memory.
Override memory if user input includes valid values.
Here are valid routes:
{routes}

Memory:
{memory}

User: {user_input}
"""
)

# Date Normalization
def normalize_date(date_str):
    if date_str in ["unknown", None, ""]:
        return "unknown"
    parsed_date = dateparser.parse(date_str)
    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    else:
        return "unknown"

# Parse LLM response
def parse_response(output: str) -> Dict[str, Any]:
    if output.strip().startswith("Intent:"):
        try:
            payload = output.strip()[len("Intent:"):].strip()
            intent_dict = json.loads(payload)
            return {"intent": intent_dict, "response": None}
        except Exception:
            return {"intent": None, "response": "Sorry, I couldn't understand your request. Could you rephrase it?"}
    elif output.strip().startswith("Reply:"):
        return {"intent": None, "response": output.strip()[len("Reply:"):].strip()}
    else:
        return {"intent": None, "response": output.strip()}

# Check whether intent is fully specified
def is_complete_intent(intent):
    return all([
        intent.get("origin"),
        intent.get("destination"),
        intent.get("date_start") not in [None, "unknown"]
    ])

# Search flights
def search_flight(intent):
    global pending_flight, pending_confirmation

    filtered_df = df.copy()

    if intent.get("origin"):
        filtered_df = filtered_df[filtered_df['origin'].str.lower() == intent['origin'].lower()]
    if intent.get("destination"):
        filtered_df = filtered_df[filtered_df['destination'].str.lower() == intent['destination'].lower()]

    if intent.get("date_start") and intent['date_start'] != "unknown":
        filtered_df = filtered_df[filtered_df['date'] == intent['date_start']]

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
    print("\U0001F1E6\U0001F1EAUAE Flight Booking Agent")
    print("Type your request. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        if pending_confirmation:
            if user_input.lower() in ["yes", "y", "ok", "confirm", "sure"]:
                print(f"\nBooking confirmed! \U0001F3AB")
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
            today = datetime.today().strftime("%Y-%m-%d")
            memory_str = json.dumps(conversation_memory, indent=2)
            route_preview = all_routes.to_string(index=False)
            prompt = simple_prompt.format(
                user_input=user_input,
                today=today,
                memory=memory_str,
                routes=route_preview
            )
            raw_output = llm.invoke([HumanMessage(content=prompt)]).content
            result = parse_response(raw_output)

            if result["intent"]:
                intent = result["intent"]
                intent["date_start"] = normalize_date(intent.get("date_start"))
                intent["date_end"] = normalize_date(intent.get("date_end"))

                if intent["date_start"] != "unknown":
                    today_date = datetime.today().date()
                    parsed_start = datetime.strptime(intent["date_start"], "%Y-%m-%d").date()
                    if parsed_start < today_date:
                        print("The date you entered is in the past. Please enter a valid future date.\n")
                        continue

                for k, v in intent.items():
                    if v and v != "unknown":
                        conversation_memory[k] = v

                if is_complete_intent(conversation_memory):
                    search_flight(conversation_memory)
                else:
                    remaining = []
                    if not conversation_memory.get("origin"):
                        remaining.append("departure city")
                    if not conversation_memory.get("destination"):
                        remaining.append("destination")
                    if conversation_memory.get("date_start") in [None, "unknown"]:
                        remaining.append("travel date")

                    if remaining:
                        print(f"\nGot it! To proceed, please tell me your {', '.join(remaining)}.\n")
                    else:
                        print("\nThanks! Let me know if you'd like to search for a flight.\n")
            else:
                print("\n" + result["response"] + "\n")
