# UAE Flight Booking Agent 

This is a demo project for building a conversational flight booking agent using LangChain and OpenAI LLM.  
It supports:

✅ multi-turn dialogue  
✅ memory-based slot filling  
✅ fuzzy date parsing (single date or range)  
✅ user confirmation before booking

## Data Generation

Run the data generation script first:

```bash
python data_generation.py
```

This will create flights.jsonl — a fake dataset containing random flights with:

1.origin
2.destination
3.flight_number
4.date
5.price

---

## Features

- Conversational flight booking via terminal chat  
- Extracts intent fields:
  - `origin`
  - `destination`
  - `date_start`
  - `date_end`
- Supports **multi-turn updates**:
  - e.g. "change my date to next week", "change destination to Tokyo"
- Handles **fuzzy dates**:
  - "this month", "next week", "June 30"
- Keeps **memory** of previous slots
- Asks for **explicit confirmation** before booking
- Returns **cheapest matching flight**

---

## Run the Agent

Run the agent program:

```bash
python flight_agent.py
```

Note:
You need to provide your own OpenAI API Key in the code.
In flight_agent.py, you will see the following line:

```
my_api_key = ""

llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=my_api_key
)
```
For security reasons, my_api_key is left empty in the code — you need to set your own key before running the agent.

## 🚀 Screenshots

### 🎬 Example Dialog

![Multi-turn dialogue: Change flight plans based on user needs](multi-turn.jpg)

### 🎬 Multi-turn Update

![Search within a date range](data_range.jpg)


