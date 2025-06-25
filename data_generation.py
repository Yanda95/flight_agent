import json
import random
from datetime import datetime, timedelta

cities = [
    'New York', 'Los Angeles',
    'London', 'Paris', 'Berlin',
    'Dubai', 'Singapore', 'Tokyo',
    'Shanghai', 'Hong Kong', 'Sydney', 'Toronto'
]

def generate_flights(num_flights=1000):
    flights = []
    for _ in range(num_flights):
        origin = random.choice(cities)
        destination = random.choice([c for c in cities if c != origin])
        date = datetime.today() + timedelta(days=random.randint(1, 5))
        price = random.randint(100, 1500)
        flight_number = f"{random.choice(['AA', 'BB', 'CC', 'DD', 'EE'])}{random.randint(100, 999)}"

        flight = {
            'origin': origin,
            'destination': destination,
            'date': date.strftime('%Y-%m-%d'),
            'price': price,
            'status': 'available',
            'flight_number': flight_number
        }
        flights.append(flight)
    return flights

if __name__ == "__main__":
    flights = generate_flights(1000)
    with open('flights.jsonl', 'w', encoding='utf-8') as f:
        for flight in flights:
            json.dump(flight, f)
            f.write('\n')

    print("Generated 1000 flights and saved to flights.jsonl")
