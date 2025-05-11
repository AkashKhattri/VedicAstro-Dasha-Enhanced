from typing import List
# === Utility Functions ===
from datetime import datetime
def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def date_ranges_overlap(start1, end1, start2, end2):

    return not (end1 < start2 or end2 < start1)

def get_house_planets_map(rashi_chart):
    """Return a dict of {house: [planets]} from Rashi chart"""
    house_planets = {}
    for entry in rashi_chart:
        for house in entry["Houses"]:
            house_name = house["Name"]
            if house_name not in house_planets:
                house_planets[house_name] = []
            for planet in entry.get("Planets", []):
                house_planets[house_name].append(planet["Name"])
    return house_planets

def get_planet_positions(rashi_chart):
    """Returns {planet_name: rasi} from Rashi data"""
    positions = {}
    for entry in rashi_chart:
        rasi = entry["Rasi"]
        for planet in entry.get("Planets", []):
            positions[planet["Name"]] = rasi
    return positions

def is_marriage_house(house_name):
    return house_name in ["II", "VII", "XI"]

def get_planets_aspecting_houses(planet: str, current_house: int) -> List[int]:
    """
    Calculate the houses that a planet aspects based on its current house position.

    Args:
        planet (str): Name of the planet
        current_house (int): Current house position (1-12)

    Returns:
        List[int]: List of houses that the planet aspects
    """
    def get_house_number(base: int, offset: int) -> int:
        house = base + offset
        while house > 12:
            house -= 12
        while house < 1:
            house += 12
        return house

    # Define aspect patterns for different planets
    aspect_patterns = {
        "Jupiter": [4, 6, 8],  # 5th, 7th, and 9th houses from its position
        "Saturn": [2, 6, 9],   # 3rd, 7th, and 10th houses from its position
        "Mars": [3, 5, 7],     # 4th, 6th, and 8th houses from its position
        "Sun": [6],            # 7th house from its position
        "Moon": [6],           # 7th house from its position
        "Mercury": [6],        # 7th house from its position
        "Venus": [6],          # 7th house from its position
        "Rahu": [],            # No aspects
        "Ketu": []             # No aspects
    }

    if planet not in aspect_patterns:
        return []

    # Calculate aspecting houses based on the planet's pattern
    aspecting_houses = [
        get_house_number(current_house, offset)
        for offset in aspect_patterns[planet]
    ]

    return aspecting_houses

