from __future__ import annotations



from typing import Optional, List, Dict, Sequence, Set, TypedDict
from pydantic import BaseModel, field_validator, validator
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
from vedicastro import VedicAstro, horary_chart
from vedicastro.utils import pretty_data_table
from vedicastro.astrocartography import AstrocartographyCalculator
from vedicastro.compute_dasha import compute_vimshottari_dasa_enahanced, filter_vimshottari_dasa_by_years, flatten_vimshottari_dasa
from d_chart_calculation import (calculate_d2_position,
                                 calculate_d3_position,
                                 calculate_d4_position,
                                 calculate_d5_position,
                                 calculate_d7_position,
                                 calculate_d9_position,
                                 calculate_d10_position,
                                 calculate_d12_position,
                                 calculate_d16_position,
                                 calculate_d20_position,
                                 calculate_d24_position,
                                 calculate_d27_position,
                                 calculate_d30_position,
                                 calculate_d40_position)
import os
import csv
from datetime import datetime, timedelta, date
import io
from flatlib import const
from flatlib import aspects
import concurrent.futures
from vedicastro.yogas import check_raj_yogas, check_dhana_yogas, check_pancha_mahapurusha_yogas, check_nabhasa_yogas, check_other_yogas
from vedicastro.extended_yogas import check_additional_benefic_yogas, check_malefic_yogas, check_intellectual_yogas
import json
import pandas as pd
import numpy as np
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from transit_tools import merge_transits_for_dasha

app = FastAPI()

zodiac_signs = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

class ChartInput(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    utc: str = None
    latitude: float
    longitude: float
    ayanamsa: str = "Krishnamurti"
    house_system: str = "Placidus"
    return_style: Optional[str] = None

class HoraryChartInput(BaseModel):
    horary_number: int
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    utc: str
    latitude: float
    longitude: float
    ayanamsa: str = "Krishnamurti"
    house_system: str = "Placidus"
    return_style: Optional[str] = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to VedicAstro FastAPI Service!",
            "info": "Visit http://127.0.0.1:8088/docs to test the API functions"}


@app.post("/get_vimshottari_dasa")
async def get_chart_data(horo_input: ChartInput):
    """
    Generates all data for a given time and location, based on the selected ayanamsa & house system
    """

    vimshottari_dasa = compute_vimshottari_dasa_enahanced(
        horo_input.year,
        horo_input.month,
        horo_input.day,
        horo_input.hour,
        horo_input.minute,
        horo_input.second,
        horo_input.latitude,
        horo_input.longitude,
        horo_input.utc,
        horo_input.ayanamsa,
        horo_input.house_system
    )

    return vimshottari_dasa

class VimshottariDasaDataRequest(BaseModel):
    horo_input:ChartInput
    start_year:int
    end_year:int
    birth_date:str


@app.post("/get_vimshottari_dasa_data")
async def get_vimshottari_dasa_data(vimshottari_dasa_data_request: VimshottariDasaDataRequest):
    """
    Generates vimshottari dasa data for a given time and location, filtered by the specified start and end years.
    Returns a flattened list of dashas with only entries where mahadasha, antardasha, and pratyantardasha are all present.
    Includes age_at_start for each dasha period.
    """
    # Get complete vimshottari dasa data
    vimshottari_dasa = compute_vimshottari_dasa_enahanced(
        vimshottari_dasa_data_request.horo_input.year,
        vimshottari_dasa_data_request.horo_input.month,
        vimshottari_dasa_data_request.horo_input.day,
        vimshottari_dasa_data_request.horo_input.hour,
        vimshottari_dasa_data_request.horo_input.minute,
        vimshottari_dasa_data_request.horo_input.second,
        vimshottari_dasa_data_request.horo_input.latitude,
        vimshottari_dasa_data_request.horo_input.longitude,
        vimshottari_dasa_data_request.horo_input.utc,
        vimshottari_dasa_data_request.horo_input.ayanamsa,
        vimshottari_dasa_data_request.horo_input.house_system
    )

    # Filter the dasa data by start and end years
    filtered_dasa = filter_vimshottari_dasa_by_years(
        vimshottari_dasa,
        vimshottari_dasa_data_request.start_year,
        vimshottari_dasa_data_request.end_year
    )

    # Flatten the dasa data structure
    flattened_dasa = flatten_vimshottari_dasa(filtered_dasa)

    # Filter to include only entries with all three levels present
    complete_entries = [dasa for dasa in flattened_dasa if dasa['mahadasha'] and dasa['antardasha'] and dasa['pratyantardasha']]

    # Parse birth date
    birth_date = datetime.strptime(vimshottari_dasa_data_request.birth_date, "%Y-%m-%d")

    # Calculate age at start for each period and convert dates to ISO format
    for dasa in complete_entries:
        # Calculate age at start (in years with decimal precision)
        days_diff = (dasa['start_date'] - birth_date).days
        dasa['age_at_start'] = round(days_diff / 365.25, 2)

        # Convert datetime objects to ISO strings
        dasa['start_date'] = dasa['start_date'].strftime('%Y-%m-%d')
        dasa['end_date'] = dasa['end_date'].strftime('%Y-%m-%d')

    # Filter out dashas where age was smaller than 20
    filtered_entries = [dasa for dasa in complete_entries if dasa['age_at_start'] >= 18 and dasa['age_at_start'] <=35]


    return filtered_entries


@app.post("/get_dasha_data")
async def get_chart_data(horo_input: ChartInput):
    """
    Generates all data for a given time and location, based on the selected ayanamsa & house system
    """

    vimshottari_dasa = compute_vimshottari_dasa_enahanced(
        horo_input.year,
        horo_input.month,
        horo_input.day,
        horo_input.hour,
        horo_input.minute,
        horo_input.second,
        horo_input.latitude,
        horo_input.longitude,
        horo_input.utc,
        horo_input.ayanamsa,
        horo_input.house_system
    )

    return vimshottari_dasa


@app.post("/get_chart_data")
async def get_chart_data(horo_input: ChartInput):
    """
    Generates all data for a given time and location as per KP Astrology system
    Returns data as a list of dictionaries with named fields for each planet/point
    """
    horoscope = VedicAstro.VedicHoroscopeData(year=horo_input.year, month=horo_input.month, day=horo_input.day,
                                           hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
                                           tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
                                           ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system)
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)
    houses_data = horoscope.get_houses_data_from_chart(chart)
    consolidated_chart_data = horoscope.get_consolidated_chart_data(planets_data=planets_data,
                                                                    houses_data=houses_data,
                                                                    return_style = horo_input.return_style)

    return format_consolidated_chart_data(consolidated_chart_data)
    # # Convert NamedTuple to list of dictionaries with named fields
    # formatted_data = []
    # for planet in planets_data:
    #     planet_dict = {
    #         "Object": planet.Object,
    #         "Rasi": planet.Rasi,
    #         "isRetroGrade": planet.isRetroGrade,
    #         "LonDecDeg": planet.LonDecDeg,
    #         "SignLonDMS": planet.SignLonDMS,
    #         "SignLonDecDeg": planet.SignLonDecDeg,
    #         "LatDMS": planet.LatDMS,
    #         "Nakshatra": planet.Nakshatra,
    #         "Rasi Lord": planet.RasiLord,
    #         "Nakshatra Lord": planet.NakshatraLord,
    #         "Sub Lord": planet.SubLord,
    #         "Sub Sub Lord": planet.SubSubLord,
    #         "Cusp Number": planet.HouseNr
    #     }
    #     formatted_data.append(planet_dict)

    # return (formatted_data)


@app.post("/get_rashi_chart_data")
async def get_rashi_chart_data(horo_input: ChartInput):
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year,
        month=horo_input.month,
        day=horo_input.day,
        hour=horo_input.hour,
        minute=horo_input.minute,
        second=horo_input.second,
        tz=horo_input.utc,
        latitude=horo_input.latitude,
        longitude=horo_input.longitude,
        ayanamsa="Lahiri",
        house_system="Equal"
    )

    # Generate the chart
    chart = horoscope.generate_chart()

    # Get planets and houses data
    planets_data = horoscope.get_planets_data_from_chart(chart)
    houses_data = horoscope.get_houses_data_from_chart(chart)

    # Add consolidated chart data by sign (rasi)
    consolidated_chart_data = horoscope.get_consolidated_chart_data(
        planets_data=planets_data,
        houses_data=houses_data,
        return_style="dataframe_records"
    )

    # Reformat the consolidated chart data to be more readable
    reformatted_chart_data = []
    for sign_data in consolidated_chart_data:
        # Create a better structured entry for each sign
        formatted_sign = {
            "Rasi": sign_data["Rasi"],
            "Houses": [],
            "Planets": []
        }

        # Separate houses (Roman numerals) from planets
        for i, obj in enumerate(sign_data["Object"]):
            is_retrograde = sign_data["isRetroGrade"][i] if i < len(sign_data["isRetroGrade"]) else False
            longitude = sign_data["SignLonDecDeg"][i] if i < len(sign_data["SignLonDecDeg"]) else 0

            if obj in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "Asc"]:
                formatted_sign["Houses"].append({
                    "Name": obj,
                    "Longitude": longitude,
                    "LongitudeDMS": sign_data["SignLonDMS"][i] if i < len(sign_data["SignLonDMS"]) else ""
                })
            else:
                formatted_sign["Planets"].append({
                    "Name": obj,
                    "Longitude": longitude,
                    "LongitudeDMS": sign_data["SignLonDMS"][i] if i < len(sign_data["SignLonDMS"]) else "",
                    "isRetrograde": is_retrograde
                })

        reformatted_chart_data.append(formatted_sign)

    rashi_chart = reformatted_chart_data

    return rashi_chart

@app.post("/get_kp_data")
async def get_kp_data(horo_input: ChartInput):
    """
    Generates KP Astrology data for a given time and location including house cusps.
    Returns both planets and cusps with their detailed positions and lord information.
    Also includes comprehensive KP significator analysis including sub-lord relationships.
    """
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year,
        month=horo_input.month,
        day=horo_input.day,
        hour=horo_input.hour,
        minute=horo_input.minute,
        second=horo_input.second,
        tz=horo_input.utc,
        latitude=horo_input.latitude,
        longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa,
        house_system=horo_input.house_system
    )

    # Generate the chart
    chart = horoscope.generate_chart()

    # Get planets and houses data
    planets_data = horoscope.get_planets_data_from_chart(chart)
    houses_data = horoscope.get_houses_data_from_chart(chart)

    # Format both planets and houses data with detailed information
    formatted_data = {
        "planets": [],
        "cusps": []
    }

    # Process planet data
    for planet in planets_data:
        planet_dict = {
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "isRetroGrade": planet.isRetroGrade,
            "LonDecDeg": planet.LonDecDeg,
            "SignLonDMS": planet.SignLonDMS,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "LatDMS": planet.LatDMS,
            "Nakshatra": planet.Nakshatra,
            "RasiLord": planet.RasiLord,
            "NakshatraLord": planet.NakshatraLord,
            "SubLord": planet.SubLord,
            "SubSubLord": planet.SubSubLord,
            "HouseNr": planet.HouseNr
        }
        formatted_data["planets"].append(planet_dict)

    # Process house cusp data
    for house in houses_data:
        house_dict = {
            "Object": house.Object,  # Roman numeral house number
            "HouseNr": house.HouseNr,  # Numeric house number
            "Rasi": house.Rasi,
            "LonDecDeg": house.LonDecDeg,
            "SignLonDMS": house.SignLonDMS,
            "SignLonDecDeg": house.SignLonDecDeg,
            "DegSize": house.DegSize,  # Size of the house in degrees
            "Nakshatra": house.Nakshatra,
            "RasiLord": house.RasiLord,
            "NakshatraLord": house.NakshatraLord,
            "SubLord": house.SubLord,
            "SubSubLord": house.SubSubLord
        }
        formatted_data["cusps"].append(house_dict)

    # Calculate planetary aspects for KP analysis
    aspects = horoscope.get_planetary_aspects(chart)
    formatted_data["aspects"] = aspects

    formatted_data["rasi_chart"] = await get_rashi_chart_data(horo_input)

    # Generate significators for KP analysis with more descriptive names
    planet_significators = horoscope.get_planet_wise_significators(planets_data, houses_data)
    house_significators = horoscope.get_house_wise_significators(planets_data, houses_data)

    # Convert planet significators with descriptive names
    formatted_planet_significators = []
    for sig in planet_significators:
        # Collect all houses signified by this planet (without duplicates)
        all_houses = set()

        # Add star lord house
        if sig.A:  # House occupied by this planet's star lord
            all_houses.add(sig.A)

        # Add occupied house
        if sig.B:  # House occupied by the planet itself
            all_houses.add(sig.B)

        # Add houses ruled by star lord
        if sig.C:  # Houses where the star lord is also the rashi lord
            for house in sig.C:
                all_houses.add(house)

        # Add houses ruled by planet
        if sig.D:  # Houses where this planet is the rashi lord
            for house in sig.D:
                all_houses.add(house)

        # Sort the houses for consistent ordering
        sorted_houses = sorted(list(all_houses))

        formatted_sig = {
            "Planet": sig.Planet,
            "houseSignified": sorted_houses,
            # Add the original KP significator components for reference
            "starLordHouse": sig.A,  # House occupied by this planet's star lord
            "occupiedHouse": sig.B,  # House occupied by the planet itself
            "starLordRuledHouses": sig.C,  # Houses where the star lord is also the rashi lord
            "planetRuledHouses": sig.D,  # Houses where this planet is the rashi lord
        }
        formatted_planet_significators.append(formatted_sig)

    # Enhance significators with Sub-Lord analysis
    for planet_sig in formatted_planet_significators:
        planet_name = planet_sig["Planet"]
        planet_data = next((p for p in formatted_data["planets"] if p["Object"] == planet_name), None)

        if planet_data:
            sub_lord = planet_data["SubLord"]
            sub_sub_lord = planet_data["SubSubLord"]

            # Find sub-lord's significators
            sub_lord_sig = next((p for p in formatted_planet_significators if p["Planet"] == sub_lord), None)

            # Find sub-sub-lord's significators
            sub_sub_lord_sig = next((p for p in formatted_planet_significators if p["Planet"] == sub_sub_lord), None)

            # Add sub-lord analysis
            planet_sig["subLord"] = sub_lord
            planet_sig["subLordHouseSignifications"] = sub_lord_sig["houseSignified"] if sub_lord_sig else []

            # Add sub-sub-lord analysis
            planet_sig["subSubLord"] = sub_sub_lord
            planet_sig["subSubLordHouseSignifications"] = sub_sub_lord_sig["houseSignified"] if sub_sub_lord_sig else []

            # Find conjunctions (planets in same house)
            conjunctions = []
            for p in formatted_data["planets"]:
                if p["Object"] != planet_name and p["HouseNr"] == planet_data["HouseNr"]:
                    conjunctions.append(p["Object"])

            planet_sig["conjunctions"] = conjunctions

            # Find aspects - corrected to use the correct keys from the aspects data
            planet_aspects = []
            for aspect in formatted_data["aspects"]:
                if "P1" in aspect and "P2" in aspect and "AspectType" in aspect:
                    if aspect["P1"] == planet_name:
                        planet_aspects.append({
                            "planet": aspect["P2"],
                            "aspect": aspect["AspectType"]
                        })
                    elif aspect["P2"] == planet_name:
                        planet_aspects.append({
                            "planet": aspect["P1"],
                            "aspect": aspect["AspectType"]
                        })

            planet_sig["aspects"] = planet_aspects

    # Convert house significators with descriptive names
    formatted_house_significators = []
    for sig in house_significators:
        formatted_sig = {
            "House": sig.House,
            "PlanetsInStarOfOccupants": sig.A,  # Planets in the star of occupants of this house
            "OccupyingPlanets": sig.B,  # Planets occupying this house
            "PlanetsInStarOfOwner": sig.C,  # Planets in the star of owner of this house
            "HouseOwner": sig.D   # Owner/lord of this house
        }
        formatted_house_significators.append(formatted_sig)

    # Define helper function for Roman numeral conversion
    def roman_to_int(roman):
        if roman == "Asc":
            return 1

        values = {
            'I': 1, 'V': 5, 'X': 10, 'L': 50,
            'C': 100, 'D': 500, 'M': 1000
        }
        result = 0
        prev_value = 0

        for char in reversed(roman):
            if char in values:
                current_value = values[char]
                if current_value >= prev_value:
                    result += current_value
                else:
                    result -= current_value
                prev_value = current_value

        return result

    # Enhance house significators with cusp sub-lord analysis
    for house_sig in formatted_house_significators:
        house_number = roman_to_int(house_sig["House"]) if house_sig["House"] != "Asc" else 1

        # Find the cusp data for this house
        cusp_data = next((c for c in formatted_data["cusps"] if c["HouseNr"] == house_number), None)

        if cusp_data:
            sub_lord = cusp_data["SubLord"]
            sub_sub_lord = cusp_data["SubSubLord"]

            # Find sub-lord's significators
            sub_lord_sig = next((p for p in formatted_planet_significators if p["Planet"] == sub_lord), None)

            # Add cusp sub-lord analysis
            house_sig["cuspSubLord"] = sub_lord
            house_sig["cuspSubLordSignifications"] = sub_lord_sig["houseSignified"] if sub_lord_sig else []

            # Add sub-sub-lord analysis
            house_sig["cuspSubSubLord"] = sub_sub_lord
            house_sig["cuspSubSubLordSignifications"] = next(
                (p["houseSignified"] for p in formatted_planet_significators if p["Planet"] == sub_sub_lord),
                []
            )

    formatted_data["planet_significators"] = formatted_planet_significators
    formatted_data["house_significators"] = formatted_house_significators

    # Return comprehensive KP data
    return {
        "planet_significators": formatted_data["planet_significators"],
        "house_significators": formatted_data["house_significators"],
        "cusps": formatted_data["cusps"],
        "planets": formatted_data["planets"],
        "aspects": formatted_data["aspects"],
        "rasi_chart": formatted_data["rasi_chart"]
    }


from typing import Any, Dict, List, Set, Tuple

MARRIAGE_HOUSES    = {2, 7, 11}
OBSTRUCTION_HOUSES = {1, 6, 10}
SUPPORT_HOUSES     = {5, 8, 12}


async def apply_transit_to_dasa_and_chart(horo_input: ChartInput, planets: list, planet_significators_map: dict):
    """
    Applies the Vishmottari Dasa system to the given chart.
    """
    vishmottari_dasa = await get_vimshottari_dasa_data(VimshottariDasaDataRequest(
        horo_input=horo_input,
        start_year=horo_input.year + 18,
        end_year=horo_input.year + 35,
        birth_date=f"{horo_input.year}-{horo_input.month}-{horo_input.day}"
    ))

    transit_data = await generate_compact_transit_data(TransitDataRequest(
        horo_input=horo_input,
        start_year=horo_input.year + 18,
        end_year=horo_input.year + 35,
        birth_date=f"{horo_input.year}-{horo_input.month}-{horo_input.day}",
        planets=list(set(planets + ["Jupiter", "Saturn", "Rahu", "Ketu", "Sun", "Venus"]))
    ))


    rashi_chart = await get_rashi_chart_data(horo_input)

    # Extract unique mahadasha planets
    mahadasha_planets = []
    mahadasha_set = set()

    for dasa in vishmottari_dasa:
        if dasa["mahadasha"] not in mahadasha_set:
            mahadasha_set.add(dasa["mahadasha"])
            mahadasha_planets.append(dasa["mahadasha"])

    result = find_marriage_windows(vishmottari_dasa, transit_data['transit_data'], planets, rashi_chart, planet_significators_map)

    return result

@app.post("/get_marriage_significate_planets")
async def get_marriage_significate_planets(horo_input: ChartInput):
    """
    Generates the marriage significant planets data.
    """
    kp_data = await get_kp_data(horo_input)
    planets_data = kp_data["planets"]
    planet_significators = kp_data["planet_significators"]
    rashi_chart = kp_data["rasi_chart"]

    # loop through the planets_data to get an array of planets, their nakshartras, and their sub lords significations
    planets_with_nakshatra_and_sub_lord = []
    planet_nakshatra_sub_lord_array = []
    for planet in planets_data:
        planet_dict = {
            "planet": planet["Object"],
            "nakshatraLord": planet["NakshatraLord"],
            "subLord": planet["SubLord"]
        }
        planet_nakshatra_sub_lord_array.append(planet_dict)


    # loop through the planet_nakshatra_sub_lord_array to map their significators from the planet_significators array
    for planet in planet_nakshatra_sub_lord_array:
        planets_with_nakshatra_and_sub_lord.append({
            "planet"              : planet["planet"],
            "planet_houses"       : list({*next((p["houseSignified"] for p in planet_significators if p["Planet"] == planet["planet"]), [])}) if planet["planet"] == "Ketu" or planet["planet"] == "Rahu" else list({*next((p["planetRuledHouses"] + [p["occupiedHouse"]]
                                                 for p in planet_significators
                                                 if p["Planet"] == planet["planet"]), [])}),              # ★
            "nakshatra_lord"      : planet["nakshatraLord"],
            "nakshatra_lord_houses": list({*next((p["houseSignified"] for p in planet_significators if p["Planet"] == planet["nakshatraLord"]), [])}) if planet["nakshatraLord"] == "Ketu" or planet["nakshatraLord"] == "Rahu" else list({*next((p["planetRuledHouses"] + [p["occupiedHouse"]]
                                                   for p in planet_significators
                                                   if p["Planet"] == planet["nakshatraLord"]), [])}),     # ★
            "sub_lord"            : planet["subLord"],
            "sub_lord_houses"     : list({*next((p["houseSignified"] for p in planet_significators if p["Planet"] == planet["subLord"]), [])}) if planet["subLord"] == "Ketu" or planet["subLord"] == "Rahu" else list({*next((p["planetRuledHouses"] + [p["occupiedHouse"]]
                                                   for p in planet_significators
                                                   if p["Planet"] == planet["subLord"]), [])})            # ★
        })

    # Remove Uranus, Pluto, Neptune and Ascendant from the planets_with_nakshatra_and_sub_lord array first key is planet name
    planets_with_nakshatra_and_sub_lord = [planet_dict for planet_dict in planets_with_nakshatra_and_sub_lord
                                          if planet_dict["planet"] not in ["Uranus", "Pluto", "Neptune", "Asc","Chiron","Syzygy","Fortuna"]]

    planet_strength_data = []

    marriage_houses = [2, 7]
    obstruction_houses = [1, 6, 10]
    support_houses = [5, 8, 11, 12]

    for planet in planets_with_nakshatra_and_sub_lord:
        planet_positive =False
        nakshatra_lord_positive = False
        sub_lord_positive = False
        planet_support_only_positive = False
        nakshatra_lord_support_only_positive = False
        sub_lord_support_only_positive = False

        number_of_planet_positive = sum(1 for house in list(set(planet["planet_houses"])) if house in marriage_houses)
        number_of_planet_support = sum(1 for house in list(set(planet["planet_houses"])) if house in support_houses)
        number_of_planet_negative = sum(1 for house in list(set(planet["planet_houses"])) if house in obstruction_houses)

        number_of_nakshatra_lord_positive = sum(1 for house in list(set(planet["nakshatra_lord_houses"])) if house in marriage_houses)
        number_of_nakshatra_lord_support = sum(1 for house in list(set(planet["nakshatra_lord_houses"])) if house in support_houses)
        number_of_nakshatra_lord_negative = sum(1 for house in list(set(planet["nakshatra_lord_houses"])) if house in obstruction_houses)

        number_of_sub_lord_positive = sum(1 for house in list(set(planet["sub_lord_houses"])) if house in marriage_houses)
        number_of_sub_lord_support = sum(1 for house in list(set(planet["sub_lord_houses"])) if house in support_houses)
        number_of_sub_lord_negative = sum(1 for house in list(set(planet["sub_lord_houses"])) if house in obstruction_houses)

        # sub lord is more powerful than nakshatra lord and nakshatra lord is more powerful than planet

        # if planet positive houses are more than planet negative houses
        if number_of_planet_positive > number_of_planet_negative:
            planet_positive = True
            if number_of_planet_support > 0:
                planet_support_only_positive = True
        elif number_of_planet_support > 0 and number_of_planet_negative == 0:
            planet_support_only_positive = True
        elif number_of_planet_positive + number_of_planet_support  > number_of_planet_negative:
            if 7 in planet["planet_houses"] or 2 in planet["planet_houses"]:
                planet_positive = True
            if number_of_planet_support > number_of_planet_negative:
                planet_support_only_positive = True
        elif number_of_planet_positive > 0 and number_of_planet_negative > 0:
            if 7 in planet["planet_houses"]:
                planet_positive = True


        if number_of_nakshatra_lord_positive > number_of_nakshatra_lord_negative:
            nakshatra_lord_positive = True
            if number_of_nakshatra_lord_support > 0:
                nakshatra_lord_support_only_positive = True
        elif number_of_nakshatra_lord_support > 0 and number_of_nakshatra_lord_negative == 0:
            nakshatra_lord_support_only_positive = True
        elif number_of_nakshatra_lord_positive + number_of_nakshatra_lord_support  > number_of_nakshatra_lord_negative:
            if 7 in planet["nakshatra_lord_houses"] or 2 in planet["nakshatra_lord_houses"]:
                nakshatra_lord_positive = True
            if number_of_nakshatra_lord_support > number_of_nakshatra_lord_negative:
                nakshatra_lord_support_only_positive = True
        elif number_of_nakshatra_lord_positive > 0 and number_of_nakshatra_lord_negative > 0:
            if 7 in planet["nakshatra_lord_houses"]:
                nakshatra_lord_positive = True



        if number_of_sub_lord_positive > number_of_sub_lord_negative:
            sub_lord_positive = True
            if number_of_sub_lord_support > 0:
                sub_lord_support_only_positive = True
        elif number_of_sub_lord_support > 0 and number_of_sub_lord_negative == 0:
            sub_lord_support_only_positive = True
        elif number_of_sub_lord_positive + number_of_sub_lord_support  > number_of_sub_lord_negative:
            if 7 in planet["sub_lord_houses"] or 2 in planet["sub_lord_houses"]:
                sub_lord_positive = True
            if number_of_sub_lord_support > number_of_sub_lord_negative:
                sub_lord_support_only_positive = True
        elif number_of_sub_lord_positive > 0 and number_of_sub_lord_negative > 0:
            if 7 in planet["sub_lord_houses"]:
                sub_lord_positive = True



        planet_strength_data.append({
            "planet": planet["planet"],
            "planet_positive": planet_positive,
            "planet_support_only_positive": planet_support_only_positive,
            "planet_neutral":(number_of_planet_negative == 0 and number_of_planet_support == 0 and number_of_planet_positive == 0) or
            (number_of_planet_positive == 0 and abs(number_of_planet_negative - number_of_planet_support) == 0),
            "nakshatra_lord_positive": nakshatra_lord_positive,
            "nakshatra_lord_support_only_positive": nakshatra_lord_support_only_positive,
            "nakshatra_lord_neutral":(number_of_nakshatra_lord_negative == 0 and number_of_nakshatra_lord_support == 0 and number_of_nakshatra_lord_positive == 0) or
            (number_of_nakshatra_lord_positive == 0 and abs(number_of_nakshatra_lord_negative - number_of_nakshatra_lord_support) == 0),
            "sub_lord_positive": sub_lord_positive,
            "sub_lord_support_only_positive": sub_lord_support_only_positive,
            "sub_lord_neutral":(number_of_sub_lord_negative == 0 and number_of_sub_lord_support == 0 and number_of_sub_lord_positive == 0) or
            (number_of_sub_lord_positive == 0 and abs(number_of_sub_lord_negative - number_of_sub_lord_support) == 0),
            "house_significator": planet["planet_houses"] + planet["nakshatra_lord_houses"] + planet["sub_lord_houses"]
        })

    marriage_planets = []

    # Loop through the planet_strength_data
    # to check if 2,7 are in the house with 6, 10 is it considered nuetral or still positive
    for planet in planet_strength_data:
        if planet["planet_positive"] and planet["nakshatra_lord_positive"] and planet["sub_lord_positive"]:
            marriage_planets.append(planet["planet"])
            continue

        if planet["nakshatra_lord_positive"] and planet["sub_lord_positive"]:
            marriage_planets.append(planet["planet"])
            continue

        if (planet["nakshatra_lord_positive"] or planet["planet_support_only_positive"] or planet["planet_positive"]) and planet["nakshatra_lord_positive"] and (planet["sub_lord_positive"] or planet["sub_lord_support_only_positive"]):
            marriage_planets.append(planet["planet"])
            continue

        if (planet["sub_lord_positive"] or planet["planet_support_only_positive"] or planet["planet_positive"]) and (planet["nakshatra_lord_positive"] or planet["nakshatra_lord_support_only_positive"]) and planet["sub_lord_positive"]:
            marriage_planets.append(planet["planet"])
            continue

        if (planet["nakshatra_lord_positive"] or planet["nakshatra_lord_support_only_positive"]) and planet["sub_lord_positive"]:
            marriage_planets.append(planet["planet"])
            continue

        if planet["planet_positive"] and planet["nakshatra_lord_neutral"] and planet["sub_lord_positive"]:
            marriage_planets.append(planet["planet"])
            continue

    for planet in planets_with_nakshatra_and_sub_lord:
        planet_sum_houses = list(set(planet["planet_houses"] + planet["nakshatra_lord_houses"] + planet["sub_lord_houses"]))

        if 2 in planet_sum_houses and 7 in planet_sum_houses and 11 in planet_sum_houses:
            marriage_planets.append(planet["planet"])
            continue

        if 7 in planet["sub_lord_houses"] and 2 in planet["sub_lord_houses"] and 11 in planet["nakshatra_lord_houses"]:
            marriage_planets.append(planet["planet"])
            continue

        if 7 in planet["sub_lord_houses"]:
            if 2 in planet["nakshatra_lord_houses"] and 11 in planet["nakshatra_lord_houses"]:
                marriage_planets.append(planet["planet"])
                continue


        if 7 in planet["sub_lord_houses"] and 2 in planet["sub_lord_houses"]:
            if 11 in planet["nakshatra_lord_houses"]:
                marriage_planets.append(planet["planet"])
                continue

        if 7 in planet["sub_lord_houses"] and 2 in planet["planet_houses"] and 11 in planet["planet_houses"]:
            marriage_planets.append(planet["planet"])
            continue

        if planet["planet"] == "Venus":
            venus_sum_houses = list(set(planet["planet_houses"] + planet["nakshatra_lord_houses"] + planet["sub_lord_houses"]))
            if not any(h in venus_sum_houses for h in obstruction_houses):
                marriage_planets.append(planet["planet"])
            elif 1 in venus_sum_houses and 6 in venus_sum_houses and 10 in venus_sum_houses:
                pass
            else:
                # Count houses by category
                venus_marriage_houses = [h for h in venus_sum_houses if h in marriage_houses]
                venus_primary_marriage_houses = [h for h in venus_sum_houses if h in [2, 7]]  # Primary marriage houses
                venus_support_houses = [h for h in venus_sum_houses if h in support_houses]
                venus_obstruction_houses = [h for h in venus_sum_houses if h in obstruction_houses]

                # Check Venus based on expanded criteria:
                # 1. If Venus has primary marriage houses (2 or 7), it passes regardless of obstruction houses
                # 2. If Venus has marriage houses and support houses, it passes
                # 3. If Venus has support houses without obstruction houses, it passes
                if len(venus_primary_marriage_houses) > 0 or \
                    (len(venus_marriage_houses) > 0 and len(venus_support_houses) > 0) or \
                    (len(venus_support_houses) > 0 and len(venus_obstruction_houses) == 0):
                    marriage_planets.append(planet["planet"])

        if planet["planet"] == "Rahu":
            rahu_sum_houses = planet["planet_houses"] + planet["nakshatra_lord_houses"] + planet["sub_lord_houses"]
            if obstruction_houses not in rahu_sum_houses:
                marriage_planets.append(planet["planet"])
            else:
                # Count houses by category
                rahu_marriage_houses = [h for h in rahu_sum_houses if h in marriage_houses]
                rahu_primary_marriage_houses = [h for h in rahu_sum_houses if h in [2, 7]]  # Primary marriage houses
                rahu_support_houses = [h for h in rahu_sum_houses if h in support_houses]
                rahu_obstruction_houses = [h for h in rahu_sum_houses if h in obstruction_houses]

                # Check Venus based on expanded criteria:
                # 1. If Venus has primary marriage houses (2 or 7), it passes regardless of obstruction houses
                # 2. If Venus has marriage houses and support houses, it passes
                # 3. If Venus has support houses without obstruction houses, it passes
                if len(rahu_primary_marriage_houses) > 0 or \
                    (len(rahu_marriage_houses) > 0 and len(rahu_support_houses) > 0) or \
                    (len(rahu_support_houses) > 0 and len(rahu_obstruction_houses) == 0):
                    marriage_planets.append(planet["planet"])

    # Get unique marriage planets
    unique_marriage_planets = list(dict.fromkeys(marriage_planets))

    # Get unique mahadasha planets
    result= await apply_transit_to_dasa_and_chart(horo_input, unique_marriage_planets,planets_with_nakshatra_and_sub_lord)
    return result
    return {
        "number_of_periods": len(result),
        "result": result
    }
    return {
       "planets_with_nakshatra_and_sub_lord": planets_with_nakshatra_and_sub_lord,
       "planet_strength_data": planet_strength_data,
       "marriage_planets": unique_marriage_planets,
    }




from utility import *
# === Main Function ===
def find_marriage_windows(dasha_list, transit_list, marriage_significators_planets, rashi_chart, planet_significators_list):
    # Find the rashi lord of 2nd, 7th and 11th house
    rashi_lords_map = {}

    for rashi in rashi_chart:
        for house in rashi["Houses"]:
            house_number = roman_to_int(house["Name"])
            rashi_lords_map[house_number] =rashi["Rasi"]

    # find the valid Mahadasha antardasha and pratyantardasha
    valid_dasha_list = []
    for dasha in dasha_list:
        # Check if both antardasha and pratyantardasha are in marriage_significators_planets
        if (dasha["antardasha"] in marriage_significators_planets and
            dasha["pratyantardasha"] in marriage_significators_planets):

            # Create a new entry with the combination
            valid_dasha = {
                "mahadasha": dasha["mahadasha"],
                "antardasha": dasha["antardasha"],
                "pratyantardasha": dasha["pratyantardasha"],
                "start_date": dasha["start_date"],
                "end_date": dasha["end_date"],
                "age_at_start": dasha["age_at_start"],
            }

            valid_dasha_list.append(valid_dasha)

            # valid_dasha_list.append(valid_dasha)
    slow_moving_planets = ["Jupiter", "Saturn", "Rahu", "Ketu"]
    fast_moving_planets = [planet for planet in marriage_significators_planets if planet not in slow_moving_planets]

    slow_moving_planets = slow_moving_planets + fast_moving_planets

    for dasha in valid_dasha_list:
        uniq, simult = merge_transits_for_dasha(
            transit_list=transit_list,
            dasha=dasha,
            slow_moving_planets=slow_moving_planets,
            rashi_lords_map=rashi_lords_map,
            min_duration_days=10,
            min_simult_planets=2,
            filter_houses=MARRIAGE_HOUSES
        )
        dasha["simultaneous_windows"] = simult

        # Analyze double transits of Jupiter and Saturn on marriage houses
        dasha["double_transits"] = []
        for window in simult:
            # Get details of Jupiter and Saturn in this window
            jupiter_details = window.get("planet_details", {}).get("Jupiter", {})
            saturn_details = window.get("planet_details", {}).get("Saturn", {})

            # Skip if either planet is missing
            if not jupiter_details or not saturn_details:
                continue

            # Get houses affected by Jupiter (direct + aspects)
            jupiter_houses = [jupiter_details.get("transiting_house", 0)]
            jupiter_houses.extend(jupiter_details.get("aspecting_houses", []))

            # Get houses affected by Saturn (direct + aspects)
            saturn_houses = [saturn_details.get("transiting_house", 0)]
            saturn_houses.extend(saturn_details.get("aspecting_houses", []))

            # Find common houses between Jupiter and Saturn that are marriage houses
            common_marriage_houses = [h for h in MARRIAGE_HOUSES if h in jupiter_houses and h in saturn_houses]

            if common_marriage_houses:
                dasha["double_transits"].append({
                    "window_start": window.get("start_date"),
                    "window_end": window.get("end_date"),
                    "duration_days": window.get("duration_days", 0),
                    "affected_houses": common_marriage_houses,
                    "jupiter_houses": jupiter_houses,
                    "saturn_houses": saturn_houses
                })

    HOUSE_WT = {7:1.0, 2:0.8, 11:0.6}
    for dasha in valid_dasha_list:
        dasha_points = 0

        # Add points for double transits (Jupiter + Saturn on same marriage house)
        double_transit_points = 0
        double_transit_houses = set()

        for dt in dasha.get("double_transits", []):
            # Points based on duration and houses
            duration_factor = min(1.0, dt.get("duration_days", 0) / 30.0)  # Cap at 1.0 for 30+ days

            for house in dt.get("affected_houses", []):
                # Weight by house importance
                house_weight = HOUSE_WT.get(house, 0.5)
                # Double transits are considered very powerful
                double_transit_points += 3.0 * house_weight * duration_factor
                double_transit_houses.add(house)

        # Add double transit points
        dasha_points += double_transit_points

        # Check if we have multiple marriage houses under double transit
        if len(double_transit_houses) >= 2:
            # Significant bonus for having 2+ marriage houses under double transit
            dasha_points += 4.0
        elif len(double_transit_houses) == 1:
            # If only one house has double transit, check if dasha lords activate other houses
            remaining_houses = [h for h in MARRIAGE_HOUSES if h not in double_transit_houses]
            dasha_houses = dasha.get("combined_significators", [])

            # If dasha lords activate at least one of the remaining marriage houses
            if any(h in dasha_houses for h in remaining_houses):
                dasha_points += 2.0

        # Add regular window points as calculated before
        for window in dasha.get("simultaneous_windows", []):
            # Calculate normalized duration factor (0.5-1.0) based on window duration
            # Cap at 60 days (2 months) for max effect
            d = window.get("duration_days", 0)
            duration_factor = 1 - 0.5 * (0.9 ** d)  # 3 d→0.14, 14 d→0.38, 60 d→0.49
            duration_factor += 0.5  # shift to 0.5-1.0 band

            # Count planets in marriage houses in this window
            marriage_house_planets = set()
            marriage_aspecting_planets = set()

            marriage_houses_affected = 0

            # Check which marriage houses are affected
            for house in window.get("houses_affected", []):
                if house in HOUSE_WT:
                    marriage_houses_affected += HOUSE_WT[house]

            # Check planets
            for planet_name, details in window.get("planet_details", {}).items():
                # Check if planet is transiting marriage houses
                if details.get("transiting_house") in MARRIAGE_HOUSES:
                    marriage_house_planets.add(planet_name)

                # Check if planet aspects marriage houses
                if any(house in MARRIAGE_HOUSES for house in details.get("aspecting_houses", [])):
                    marriage_aspecting_planets.add(planet_name)

            # Award points based on:

            # 1. Number of marriage houses affected
            dasha_points += marriage_houses_affected * 0.5 * duration_factor

            # 2. Number of planets in marriage houses
            dasha_points += len(marriage_house_planets) * 0.75 * duration_factor

            # 3. Number of planets aspecting marriage houses
            dasha_points += len(marriage_aspecting_planets) * 0.5 * duration_factor

            # 4. Special combos - Jupiter and Venus involvement
            if "Jupiter" in marriage_house_planets and "Venus" in marriage_house_planets:
                dasha_points += 2 * duration_factor  # Both in marriage houses
            elif "Jupiter" in marriage_house_planets or "Venus" in marriage_house_planets:
                dasha_points += 1 * duration_factor  # One in marriage houses

            # 5. Bonus for multiple planets in transit window
            num_planets = len(window.get("planets", []))
            if num_planets >= 4:
                dasha_points += 1.5 * duration_factor  # Many planets active together
            elif num_planets == 3:
                dasha_points += 1 * duration_factor  # Three planets active together

            # 6. Add points for benefic planets aspecting
            if "Jupiter" in marriage_aspecting_planets:
                dasha_points += 0.75 * duration_factor
            if "Venus" in marriage_aspecting_planets:
                dasha_points += 0.75 * duration_factor

        dasha["dasha_points"] = round(dasha_points, 2)
        dasha["double_transit_count"] = len(double_transit_houses)

        # Simplify combining significators
        lords = [dasha['mahadasha'], dasha['antardasha'], dasha['pratyantardasha']]
        significators = [next((s for s in planet_significators_list if s['planet'] == lord), None) for lord in lords]

        # Combine all significations from the three periods
        all_significations = []
        for sig in significators:
            if sig:  # Check if significator was found
                all_significations.extend(sig['planet_houses'])
                all_significations.extend(sig['nakshatra_lord_houses'])
                all_significations.extend(sig['sub_lord_houses'])

        dasha["combined_significators"] = list(set(all_significations))

        # Store whether this dasha has the ideal "perfect trigger" condition
        dasha["is_perfect_trigger"] = (len(double_transit_houses) >= 2) or (
            len(double_transit_houses) == 1 and
            any(h in dasha.get("combined_significators", []) for h in MARRIAGE_HOUSES if h not in double_transit_houses)
        )

    # Sort the valid_dasha_list by dasha_points in descending order
    sorted_dasha_list = sorted(valid_dasha_list, key=lambda x: x.get("dasha_points", 0), reverse=True)

    # get the top 15 dashas
    top_15_dashas = sorted_dasha_list[:15]

    # Calculate marriage compatibility score for each dasha
    for dasha in top_15_dashas:
        combined_houses = dasha.get("combined_significators", [])

        # Calculate a house-based marriage score
        # Strong weight for marriage houses (especially 7th house)
        marriage_score = 0
        for house in MARRIAGE_HOUSES:
            if house in combined_houses:
                # 7th house is the primary marriage house, give it extra weight
                weight = 3.0 if house == 7 else 2.0
                marriage_score += weight

        # Medium weight for support houses
        support_score = sum(1.0 for house in combined_houses if house in SUPPORT_HOUSES)

        # Negative weight for obstruction houses
        obstruction_score = sum(-1.5 for house in combined_houses if house in OBSTRUCTION_HOUSES)

        # Total house-based score
        house_score = marriage_score + support_score + obstruction_score

        # Store the house analysis
        dasha["house_analysis"] = {
            "marriage_houses": [h for h in combined_houses if h in MARRIAGE_HOUSES],
            "support_houses": [h for h in combined_houses if h in SUPPORT_HOUSES],
            "obstruction_houses": [h for h in combined_houses if h in OBSTRUCTION_HOUSES],
            "house_score": round(house_score, 2)
        }

        # Combined score with house score prioritized (80% house, 20% transit)
        dasha["combined_score"] = round(
            0.7 * house_score +
            0.3 * dasha.get("dasha_points", 0),
            2
        )

    # Re-sort based on combined score
    top_15_dashas.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

    # Add ranking to each dasha
    for i, dasha in enumerate(top_15_dashas):
        dasha["rank"] = i + 1  # Add 1-based ranking

    # Now sort it with start and end date
    # top_15_dashas.sort(key=lambda x: x.get("start_date", 0), reverse=False)

    return {
        "number_of_periods": len(top_15_dashas),
        "result": top_15_dashas
    }



@app.post("/get_kp_chart_with_cusps")
async def get_kp_chart_with_cusps(horo_input: ChartInput):
    """
    Generates KP Astrology data for a given time and location including house cusps.
    Returns both planets and cusps with their detailed positions and lord information.
    """
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year,
        month=horo_input.month,
        day=horo_input.day,
        hour=horo_input.hour,
        minute=horo_input.minute,
        second=horo_input.second,
        tz=horo_input.utc,
        latitude=horo_input.latitude,
        longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa,
        house_system=horo_input.house_system
    )

    # Generate the chart
    chart = horoscope.generate_chart()

    # Get planets and houses data
    planets_data = horoscope.get_planets_data_from_chart(chart)
    houses_data = horoscope.get_houses_data_from_chart(chart)

    # Format both planets and houses data with detailed information
    formatted_data = {
        "planets": [],
        "cusps": []
    }

    # Process planet data
    for planet in planets_data:
        planet_dict = {
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "isRetroGrade": planet.isRetroGrade,
            "LonDecDeg": planet.LonDecDeg,
            "SignLonDMS": planet.SignLonDMS,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "LatDMS": planet.LatDMS,
            "Nakshatra": planet.Nakshatra,
            "RasiLord": planet.RasiLord,
            "NakshatraLord": planet.NakshatraLord,
            "SubLord": planet.SubLord,
            "SubSubLord": planet.SubSubLord,
            "HouseNr": planet.HouseNr
        }
        formatted_data["planets"].append(planet_dict)

    # Process house cusp data
    for house in houses_data:
        house_dict = {
            "Object": house.Object,  # Roman numeral house number
            "HouseNr": house.HouseNr,  # Numeric house number
            "Rasi": house.Rasi,
            "LonDecDeg": house.LonDecDeg,
            "SignLonDMS": house.SignLonDMS,
            "SignLonDecDeg": house.SignLonDecDeg,
            "DegSize": house.DegSize,  # Size of the house in degrees
            "Nakshatra": house.Nakshatra,
            "RasiLord": house.RasiLord,
            "NakshatraLord": house.NakshatraLord,
            "SubLord": house.SubLord,
            "SubSubLord": house.SubSubLord
        }
        formatted_data["cusps"].append(house_dict)

    # Calculate planetary aspects for KP analysis
    aspects = horoscope.get_planetary_aspects(chart)
    formatted_data["aspects"] = aspects


    formatted_data["rasi_chart"] = await get_rashi_chart_data(horo_input)

    # Generate significators for KP analysis with more descriptive names
    planet_significators = horoscope.get_planet_wise_significators(planets_data, houses_data)
    house_significators = horoscope.get_house_wise_significators(planets_data, houses_data)

    # Convert planet significators with descriptive names
    formatted_planet_significators = []
    for sig in planet_significators:
        # Collect all houses signified by this planet (without duplicates)
        all_houses = set()

        # Add star lord house
        if sig.A:  # House occupied by this planet's star lord
            all_houses.add(sig.A)

        # Add occupied house
        if sig.B:  # House occupied by the planet itself
            all_houses.add(sig.B)

        # Add houses ruled by star lord
        if sig.C:  # Houses where the star lord is also the rashi lord
            for house in sig.C:
                all_houses.add(house)

        # Add houses ruled by planet
        if sig.D:  # Houses where this planet is the rashi lord
            for house in sig.D:
                all_houses.add(house)

        # Sort the houses for consistent ordering
        sorted_houses = sorted(list(all_houses))

        formatted_sig = {
            "Planet": sig.Planet,
            "houseSignified": sorted_houses
        }
        formatted_planet_significators.append(formatted_sig)

    # Convert house significators with descriptive names
    formatted_house_significators = []
    for sig in house_significators:
        formatted_sig = {
            "House": sig.House,
            "PlanetsInStarOfOccupants": sig.A,  # Planets in the star of occupants of this house
            "OccupyingPlanets": sig.B,  # Planets occupying this house
            "PlanetsInStarOfOwner": sig.C,  # Planets in the star of owner of this house
            "HouseOwner": sig.D   # Owner/lord of this house
        }
        formatted_house_significators.append(formatted_sig)

    formatted_data["planet_significators"] = formatted_planet_significators
    formatted_data["house_significators"] = formatted_house_significators

    return formatted_data

@app.post("/get_d2_chart_data")
async def get_chart_data(horo_input: ChartInput, method: str = "yavana"):
    """
    Generates the Hora (D-2) chart data as per the selected method.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })



    # Calculate the D-2 chart
    d2_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-2 position
        new_sign, new_degree = calculate_d2_position(current_sign, sign_lon_dec_deg)

        # Append to the D-2 chart
        d2_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,
            "D-2 Rasi": new_sign,
            "D-2 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d2_chart

@app.post("/get_d3_chart_data")
async def get_d3_chart_data(horo_input: ChartInput, method: str = "yavana"):
    """
    Generates the Drekkana (D-3) chart data as per the selected method.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })


    # Calculate the D-3 chart
    d3_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-3 position
        new_sign, new_degree = calculate_d3_position(current_sign, sign_lon_dec_deg)

        # Append to the D-3 chart
        d3_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,
            "D-3 Rasi": new_sign,
            "D-3 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d3_chart

@app.post("/get_d4_chart_data")
async def get_d4_chart_data(horo_input: ChartInput):
    """
    Generates the Chaturthamsa (D-4) chart data as per Yavana Paddhati.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-4 chart
    d4_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-4 position
        new_sign, new_degree = calculate_d4_position(current_sign, sign_lon_dec_deg)

        # Append to the D-4 chart
        d4_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-4 Rasi": new_sign,
            "D-4 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d4_chart

#! Problem in D-5 chart calculation
@app.post("/get_d5_chart_data")
async def get_d5_chart_data(horo_input: ChartInput):
    """
    Generates the Panchamsha (D-5) chart data as per Yavana Paddhati.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-5 chart
    d5_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-5 position
        new_sign, new_degree = calculate_d5_position(current_sign, sign_lon_dec_deg)

        # Append to the D-5 chart
        d5_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-5 Rasi": new_sign,
            "D-5 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d5_chart

@app.post("/get_d7_chart_data")
async def get_d7_chart_data(horo_input: ChartInput):
    """
    Generates the Saptamsha (D-7) chart data based on the image logic.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-7 chart
    d7_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-7 position
        new_sign, new_degree = calculate_d7_position(current_sign, sign_lon_dec_deg)

        # Append to the D-7 chart
        d7_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,
            "D-7 Rasi": new_sign,
            "D-7 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-7 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d7_chart

@app.post("/get_d9_chart_data")
async def get_d9_chart_data(horo_input: ChartInput):
    """
    Generates the Navamsa (D-9) chart data based on the element of the signs.
    """
    try:
        # Generate the natal chart using the VedicAstro library
        horoscope = VedicAstro.VedicHoroscopeData(
            year=horo_input.year, month=horo_input.month, day=horo_input.day,
            hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
            tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
            ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
        )


        chart = horoscope.generate_chart()


        planets_data = horoscope.get_planets_data_from_chart(chart)


        formatted_data = []
        for planet in planets_data:
            formatted_data.append({
                "Object": planet.Object,
                "Rasi": planet.Rasi,
                "SignLonDecDeg": planet.SignLonDecDeg,
                "House Number": planet.HouseNr
            })

        # Calculate the D-9 chart
        d9_chart = []
        for planet in formatted_data:
            current_sign = planet["Rasi"]
            sign_lon_dec_deg = planet["SignLonDecDeg"]

            # Calculate the D-9 position with error handling
            try:

                new_sign, new_degree = calculate_d9_position(current_sign, sign_lon_dec_deg)
            except Exception as e:

                return {"error": f"Error calculating D-9 position for {planet['Object']}: {str(e)}"}

            # Append to the D-9 chart
            d9_chart.append({
                "Object": planet["Object"],
                "Current Sign": current_sign,
                "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
                "D-9 Rasi": new_sign,
                "D-9 Sign Index": zodiac_signs.index(new_sign) + 1,
                "D-9 Degree": new_degree,

            })

        return d9_chart

    except Exception as e:

        import traceback
        error_details = traceback.format_exc()

        return {"error": str(e), "details": error_details}

@app.post("/get_d10_chart_data")
async def get_d10_chart_data(horo_input: ChartInput):
    """
    Generates the Dasamsa (D-10) chart data based on the rules of odd and even signs.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-10 chart
    d10_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-10 position
        new_sign, new_degree = calculate_d10_position(current_sign, sign_lon_dec_deg)

        # Append to the D-10 chart
        d10_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-10 Rasi": new_sign,
            "D-10 Degree": new_degree,
            "D-10 Sign Index": zodiac_signs.index(new_sign) + 1,
            "House Number": planet["House Number"]
        })

    return d10_chart

@app.post("/get_d12_chart_data")
async def get_d12_chart_data(horo_input: ChartInput):
    """
    Generates the Dwadasamsa (D-12) chart data based on the specified rules.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-12 chart
    d12_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-12 position
        new_sign, new_degree = calculate_d12_position(current_sign, sign_lon_dec_deg)

        # Append to the D-12 chart
        d12_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,
            "D-12 Rasi": new_sign,
            "D-12 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-12 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d12_chart

@app.post("/get_d16_chart_data")
async def get_d16_chart_data(horo_input: ChartInput):
    """
    Generates the Shodasamsa (D-16) chart data based on the specified rules.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-16 chart
    d16_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-16 position
        new_sign, new_degree = calculate_d16_position(current_sign, sign_lon_dec_deg)

        # Append to the D-16 chart
        d16_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-16 Rasi": new_sign,
            "D-16 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-16 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d16_chart

@app.post("/get_d20_chart_data")
async def get_d20_chart_data(horo_input: ChartInput):
    """
    Generates the Vimsamsa (D-20) chart data using the mapping directly from the table.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Predefined mapping of D-20 positions
    d20_mapping = {
        "Movable": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
        "Fixed": ["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio"],
        "Dual": ["Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer"]
    }

    # Map signs to their types (movable, fixed, dual)
    sign_types = {
        "Aries": "Movable", "Taurus": "Fixed", "Gemini": "Dual",
        "Cancer": "Movable", "Leo": "Fixed", "Virgo": "Dual",
        "Libra": "Movable", "Scorpio": "Fixed", "Sagittarius": "Dual",
        "Capricorn": "Movable", "Aquarius": "Fixed", "Pisces": "Dual"
    }

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-20 chart
    d20_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Determine sign type
        sign_type = sign_types[current_sign]

        # Calculate the new sign and degree
        new_sign, new_degree = calculate_d20_position(sign_type, sign_lon_dec_deg, d20_mapping)

        # Append to the D-20 chart
        d20_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-20 Rasi": new_sign,
            "D-20 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-20 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d20_chart

@app.post("/get_d24_chart_data")
async def get_d24_chart_data(horo_input: ChartInput):
    """
    Generates the Siddhamsa (D-24) chart data based on the provided table logic.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-24 chart
    d24_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-24 position
        new_sign, new_degree = calculate_d24_position(current_sign, sign_lon_dec_deg)

        # Append to the D-24 chart
        d24_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-24 Rasi": new_sign,
            "D-24 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-24 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d24_chart

@app.post("/get_d27_chart_data")
async def get_d27_chart_data(horo_input: ChartInput):
    """
    Generates the Bhamsa (D-27) chart data based on the provided table logic.
    """
    # Generate the natal chart using the VedicAstro library
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year, month=horo_input.month, day=horo_input.day,
        hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
        tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system
    )
    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    # Format the natal chart data into a list of dictionaries
    formatted_data = []
    for planet in planets_data:
        formatted_data.append({
            "Object": planet.Object,
            "Rasi": planet.Rasi,
            "SignLonDecDeg": planet.SignLonDecDeg,
            "House Number": planet.HouseNr
        })

    # Calculate the D-27 chart
    d27_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-27 position
        new_sign, new_degree = calculate_d27_position(current_sign, sign_lon_dec_deg)

        # Append to the D-27 chart
        d27_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-27 Rasi": new_sign,
            "D-27 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-27 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d27_chart

@app.post("/get_d30_chart_data")
async def get_d30_chart_data(horo_input: ChartInput):
    """
    Generates the Trimsamsa (D-30) chart data based on Vedic astrology rules.
    Each sign is divided into 30 parts of 1° each.
    """
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year,
        month=horo_input.month,
        day=horo_input.day,
        hour=horo_input.hour,
        minute=horo_input.minute,
        second=horo_input.second,
        tz=horo_input.utc,
        latitude=horo_input.latitude,
        longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa,
        house_system=horo_input.house_system
    )

    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    d30_chart = []
    for planet in planets_data:
        current_sign = planet.Rasi
        sign_lon_dec_deg = planet.SignLonDecDeg

        new_sign, new_degree = calculate_d30_position(current_sign, sign_lon_dec_deg)

        d30_chart.append({
            "Object": planet.Object,
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,
            "D-30 Rasi": new_sign,
            "D-30 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-30 Degree": new_degree,
            "House Number": planet.HouseNr
        })

    return d30_chart

#! Problem in D-40 chart calculation, minute degree differences.
@app.post("/get_d40_chart_data")
async def get_d40_chart_data(horo_input: ChartInput):
    """
    Generates the D-40 chart data based on the provided table mapping.
    """
    horoscope = VedicAstro.VedicHoroscopeData(
        year=horo_input.year,
        month=horo_input.month,
        day=horo_input.day,
        hour=horo_input.hour,
        minute=horo_input.minute,
        second=horo_input.second,
        tz=horo_input.utc,
        latitude=horo_input.latitude,
        longitude=horo_input.longitude,
        ayanamsa=horo_input.ayanamsa,
        house_system=horo_input.house_system
    )

    chart = horoscope.generate_chart()
    planets_data = horoscope.get_planets_data_from_chart(chart)

    d40_chart = []
    for planet in planets_data:
        current_sign = planet.Rasi
        sign_lon_dec_deg = planet.SignLonDecDeg

        new_sign, new_degree = calculate_d40_position(current_sign, sign_lon_dec_deg)

        d40_chart.append({
            "Object": planet.Object,
            "Current Sign": current_sign,
            "D-40 Rasi": new_sign,
            "D-40 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-40 Degree": new_degree,
            "House Number": planet.HouseNr
        })

    return d40_chart


@app.post("/get_all_horary_data")
async def get_horary_data(input: HoraryChartInput):
    """
    Generates all data for a given horary number, time and location as per KP Astrology system
    """
    matched_time, vhd_hora_houses_chart, houses_data  = horary_chart.find_exact_ascendant_time(input.year, input.month, input.day, input.utc, input.latitude, input.longitude, input.horary_number, input.ayanamsa)
    vhd_hora = VedicAstro.VedicHoroscopeData(input.year, input.month, input.day,
                                              input.hour, input.minute, input.second,
                                              input.utc, input.latitude, input.longitude,
                                              input.ayanamsa, input.house_system)

    vhd_hora_planets_chart = vhd_hora.generate_chart()
    planets_data = vhd_hora.get_planets_data_from_chart(vhd_hora_planets_chart, vhd_hora_houses_chart)
    planet_significators = vhd_hora.get_planet_wise_significators(planets_data, houses_data)
    planetary_aspects = vhd_hora.get_planetary_aspects(vhd_hora_planets_chart)
    house_significators = vhd_hora.get_house_wise_significators(planets_data, houses_data)
    vimshottari_dasa_table = vhd_hora.compute_vimshottari_dasa(vhd_hora_planets_chart)
    consolidated_chart_data = vhd_hora.get_consolidated_chart_data(planets_data=planets_data,
                                                                    houses_data=houses_data,
                                                                    return_style = input.return_style)

    return {
        "planets_data": [planet._asdict() for planet in planets_data],
        "houses_data": [house._asdict() for house in houses_data],
        "planet_significators": planet_significators,
        "planetary_aspects": planetary_aspects,
        "house_significators": house_significators,
        "vimshottari_dasa_table": vimshottari_dasa_table,
        "consolidated_chart_data": consolidated_chart_data
    }


def roman_to_int(roman):
    """Convert Roman numeral to integer"""
    if roman == "Asc":
        return 1

    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

    try:
        result = 0
        prev_value = 0

        for char in reversed(roman):
            if char not in values:
                raise ValueError(f"Invalid Roman numeral character: {char}")
            current_value = values[char]
            if current_value >= prev_value:
                result += current_value
            else:
                result -= current_value
            prev_value = current_value

        return result
    except Exception as e:
        print(f"Error converting Roman numeral {roman}: {str(e)}")
        return 0  # Return 0 for invalid Roman numerals


@app.post("/get_planet_transit_data")
async def get_planet_transit_data(horo_input: ChartInput, start_year: int = 2000, end_year: int = 2050, filename: str = None):
    """
    Generates the simplified planet transit data for a range of years.
    Returns only timestamp, planet name, and planet sign.
    Also stores the data as a CSV file in the current directory.

    Parameters:
    ----------
    horo_input: ChartInput
        The base chart input data (birth details)
    start_year: int, optional (default=2000)
        The starting year for transit calculations
    end_year: int, optional (default=2050)
        The ending year for transit calculations
    filename: str, optional (default=None)
        Custom filename for the CSV output. If None, a default name will be generated.
    """
    try:
        all_transit_data = []

        # Validate input years
        if start_year >= end_year:
            return {"status": "error", "message": "start_year must be less than end_year"}

        if end_year - start_year > 100:
            return {"status": "error", "message": "Maximum range of 100 years is allowed"}

        # Loop through each year in the range
        for year in range(start_year, end_year + 1):
            # Create a new VedicHoroscopeData object for each year
            horoscope = VedicAstro.VedicHoroscopeData(
                year=year,
                month=horo_input.month,
                day=horo_input.day,
                hour=horo_input.hour,
                minute=horo_input.minute,
                second=horo_input.second,
                latitude=horo_input.latitude,
                longitude=horo_input.longitude,
                tz=horo_input.utc,
                ayanamsa=horo_input.ayanamsa,
                house_system=horo_input.house_system
            )

            # Get transit details for this year
            transit_data = horoscope.get_transit_details()

            # Extract only timestamp, PlanetName, and PlanetSign
            for transit in transit_data:
                simplified_transit = {
                    "timestamp": transit.timestamp,
                    "PlanetName": transit.PlanetName,
                    "PlanetSign": transit.PlanetSign,
                    "isRetrograde": transit.isRetrograde,
                    "Nakshatra": transit.Nakshatra,
                    "NakshatraLord": transit.NakshatraLord,
                    "SubLord": transit.SubLord,
                    "SubLordSign": transit.SubLordSign
                }
                all_transit_data.append(simplified_transit)


        return {
            "status": "success",
            "transit_data": all_transit_data,
            "range": f"{start_year} to {end_year}",
            "total_records": len(all_transit_data),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}





class TransitDataRequest(BaseModel):
    horo_input:ChartInput
    start_year:int
    end_year:int
    planets:List[str]

@app.post("/generate_compact_transit_data")
async def generate_compact_transit_data(
    transit_data_request: TransitDataRequest
):
    try:
        start_year = transit_data_request.start_year
        end_year = transit_data_request.end_year
        planets = transit_data_request.planets
        horo_input = transit_data_request.horo_input

        # Validate input years
        if start_year >= end_year:
            return {"status": "error", "message": "start_year must be less than end_year"}

        # Always exclude these planets
        excluded_planets = ["Uranus", "Neptune", "Pluto"]

        # If planets parameter is provided, use it for filtering
        # Otherwise, include all valid planets by default
        include_planets = None
        if planets:
            # Convert to set for faster lookups
            include_planets = set(planets)

        # Flattened list for transit data
        transit_records = []

        # Create start and end dates
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)

        # Current state tracking for each planet
        current_planet_states = {}  # {planet_name: (sign, start_date, is_retrograde)}

        # Loop through each day in the range
        current_date = start_date
        while current_date <= end_date:
            # Create a new VedicHoroscopeData object for each day
            horoscope = VedicAstro.VedicHoroscopeData(
                year=current_date.year,
                month=current_date.month,
                day=current_date.day,
                hour=horo_input.hour,
                minute=horo_input.minute,
                second=horo_input.second,
                latitude=horo_input.latitude,
                longitude=horo_input.longitude,
                tz=horo_input.utc,
                ayanamsa=horo_input.ayanamsa,
                house_system=horo_input.house_system
            )

            # Get transit details for this day
            transit_data = horoscope.get_transit_details()

            # Format date string (YYYY-MM-DD)
            date_str = f"{current_date.year}-{current_date.month:02d}-{current_date.day:02d}"

            # Process each planet's transit
            for transit in transit_data:
                planet_name = transit.PlanetName

                # Skip excluded planets
                if planet_name in excluded_planets:
                    continue

                # Skip planets not in the include list (if specified)
                if include_planets is not None and planet_name not in include_planets:
                    continue

                sign = transit.PlanetSign
                is_retrograde = transit.isRetrograde

                # Check if this is a new entry or the sign has changed
                if planet_name not in current_planet_states:
                    # First time seeing this planet
                    current_planet_states[planet_name] = (sign, date_str, is_retrograde)
                elif current_planet_states[planet_name][0] != sign or current_planet_states[planet_name][2] != is_retrograde:
                    # Sign or retrograde status changed - record the previous state
                    prev_sign, prev_start, prev_retro = current_planet_states[planet_name]
                    transit_records.append({
                        "planet": planet_name,
                        "sign": prev_sign,
                        "start_date": prev_start,
                        "end_date": date_str,  # Yesterday's date as end date
                        "is_retrograde": prev_retro,
                    })

                    # Update current state with new sign
                    current_planet_states[planet_name] = (sign, date_str, is_retrograde)

            # Move to the next day
            current_date += timedelta(days=1)

        # Record final states for all planets (using end_date as the end)
        end_date_str = f"{end_date.year}-{end_date.month:02d}-{end_date.day:02d}"
        for planet_name, (sign, start_date, is_retrograde) in current_planet_states.items():
            transit_records.append({
                "planet": planet_name,
                "sign": sign,
                "start_date": start_date,
                "end_date": end_date_str,
                "is_retrograde": is_retrograde,
            })
        return {"transit_data": transit_records}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/generate_transit_data")
async def generate_transit_data(
    transit_data_request: TransitDataRequest,
):
    try:
        start_year = transit_data_request.start_year
        end_year = transit_data_request.end_year
        planets = transit_data_request.planets
        horo_input = transit_data_request.horo_input

        # Validate input years
        if start_year >= end_year:
            return {"status": "error", "message": "start_year must be less than end_year"}

        # Always exclude these planets
        excluded_planets = ["Uranus", "Neptune", "Pluto"]

        # If planets parameter is provided, use it for filtering
        # Otherwise, include all valid planets by default
        include_planets = None
        if planets:
            # Convert to set for faster lookups
            include_planets = set(planets)

        # Dictionary to track each planet's position over time
        planet_transits = {}

        # Create start and end dates
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)

        # Current state tracking for each planet
        current_planet_states = {}  # {planet_name: (sign, start_date, is_retrograde)}

        # Loop through each day in the range
        current_date = start_date
        while current_date <= end_date:
            # Create a new VedicHoroscopeData object for each day
            horoscope = VedicAstro.VedicHoroscopeData(
                year=current_date.year,
                month=current_date.month,
                day=current_date.day,
                hour=horo_input.hour,
                minute=horo_input.minute,
                second=horo_input.second,
                latitude=horo_input.latitude,
                longitude=horo_input.longitude,
                tz=horo_input.utc,
                ayanamsa=horo_input.ayanamsa,
                house_system=horo_input.house_system
            )

            # Get transit details for this day
            transit_data = horoscope.get_transit_details()

            # Format date string (YYYY-MM-DD)
            date_str = f"{current_date.year}-{current_date.month:02d}-{current_date.day:02d}"

            # Process each planet's transit
            for transit in transit_data:
                planet_name = transit.PlanetName

                # Skip excluded planets
                if planet_name in excluded_planets:
                    continue

                # Skip planets not in the include list (if specified)
                if include_planets is not None and planet_name not in include_planets:
                    continue

                sign = transit.PlanetSign
                is_retrograde = transit.isRetrograde

                # Initialize if this planet hasn't been seen before
                if planet_name not in planet_transits:
                    planet_transits[planet_name] = []

                # Check if this is a new entry or the sign has changed
                if planet_name not in current_planet_states:
                    # First time seeing this planet
                    current_planet_states[planet_name] = (sign, date_str, is_retrograde)
                elif current_planet_states[planet_name][0] != sign or current_planet_states[planet_name][2] != is_retrograde:
                    # Sign or retrograde status changed - record the previous state
                    prev_sign, prev_start, prev_retro = current_planet_states[planet_name]

                    planet_transits[planet_name].append({
                        "sign": prev_sign,
                        "start_date": prev_start,
                        "end_date": date_str,  # Yesterday's date as end date
                        "isRetrograde": prev_retro
                    })

                    # Update current state with new sign
                    current_planet_states[planet_name] = (sign, date_str, is_retrograde)

            # Move to the next day
            current_date += timedelta(days=1)

        # Record final states for all planets (using end_date as the end)
        end_date_str = f"{end_date.year}-{end_date.month:02d}-{end_date.day:02d}"
        for planet_name, (sign, start_date, is_retrograde) in current_planet_states.items():
            planet_transits[planet_name].append({
                "sign": sign,
                "start_date": start_date,
                "end_date": end_date_str,
                "isRetrograde": is_retrograde
            })

        # # Special handling for Moon planet only - convert to compact string format
        # if "Moon" in planet_transits:
        #     moon_data = []
        #     for transit in planet_transits["Moon"]:
        #         # Convert sign to number (1-12)
        #         sign_number = zodiac_signs.index(transit["sign"]) + 1

        #         # Calculate days in this transit period
        #         start_date_obj = datetime.strptime(transit["start_date"], "%Y-%m-%d")
        #         end_date_obj = datetime.strptime(transit["end_date"], "%Y-%m-%d")
        #         days = (end_date_obj - start_date_obj).days

        #         # Format as "sign:start_date:days:is_retrograde"
        #         is_retro_int = 1 if transit["isRetrograde"] else 0
        #         moon_data.append(f"{sign_number}:{transit['start_date']}:{days}:{is_retro_int}")

        #     # Replace the Moon's data with the compact string format
        #     planet_transits["Moon"] = "|".join(moon_data)


        return planet_transits


    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {"status": "error", "message": str(e), "details": error_details}



def format_consolidated_chart_data(data):
    formatted_data = []

    # First, create a mapping of signs to house numbers
    sign_to_house = {}
    sign_to_rashi_house = {}
    for sign, objects in data.items():
        for obj_name, obj_data in objects.items():
            if obj_name in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]:
                house_num = roman_to_int(obj_name)
                sign_to_house[sign] = house_num
                sign_to_rashi_house[sign] = zodiac_signs.index(sign) + 1
    # Then create entries for all planets with their house numbers
    for sign, objects in data.items():
        for obj_name, obj_data in objects.items():
            # Skip house cusps, process only planets and points
            if obj_name not in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]:
                obj_entry = {
                    "Object": obj_name,
                    "Rasi": sign,
                    "Rashi House Number": sign_to_rashi_house.get(sign),
                    "isRetrograde": obj_data.get("is_Retrograde", False)
                }
                formatted_data.append(obj_entry)

    return formatted_data


@app.post("/get_ashtakavarga_data")
async def generate_ashtakavarga_data(horo_input: ChartInput):
    """
    Generates the Ashtakavarga data for a birth chart.
    """
    try:
        # Create a VedicHoroscopeData object
        horoscope = VedicAstro.VedicHoroscopeData(
            year=horo_input.year,
            month=horo_input.month,
            day=horo_input.day,
            hour=horo_input.hour,
            minute=horo_input.minute,
            second=horo_input.second,
            latitude=horo_input.latitude,
            longitude=horo_input.longitude,
            tz=horo_input.utc,
            ayanamsa=horo_input.ayanamsa,
            house_system=horo_input.house_system
        )

        # Generate chart
        chart = horoscope.generate_chart()
        planets_data = horoscope.get_planets_data_from_chart(chart)
        houses_data = horoscope.get_houses_data_from_chart(chart)

        # Get consolidated chart data
        consolidated_chart_data = horoscope.get_consolidated_chart_data(
            planets_data=planets_data,
            houses_data=houses_data
        )


        # Calculate Ashtakavarga using the chart data
        ashtakavarga_data = get_ashtakavarga_data(consolidated_chart_data)
        return ashtakavarga_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {"status": "error", "message": str(e), "details": error_details}

def get_ashtakavarga_data(chart_data):
    """
    Calculate Ashtakavarga tables using traditional Vedic astrology rules.
    """
    # Define the planets (7 planets + Lagna)
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Ascendant"]

    # Get planetary positions from chart data
    planet_positions = {}

    # Extract planetary positions and ascendant from the chart data
    for sign, objects in chart_data.items():
        for obj_name, obj_data in objects.items():
            if obj_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
                # Store each planet's sign position (1-12)
                planet_positions[obj_name] = zodiac_signs.index(sign) + 1
            elif obj_name == "Asc" or obj_name == "I":  # The ascendant
                planet_positions["Ascendant"] = zodiac_signs.index(sign) + 1

    # Define classical benefic houses from each planet's position
    sun_benefic_houses = {
        "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon": [3, 6, 10, 11],
        "Mars": [1,2,4,7,8,9,10,11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [3, 4, 6, 10, 11, 12]
    }

    moon_benefic_houses = {
        "Sun": [3, 6, 7, 8, 10, 11],
        "Moon": [1, 3, 6, 7, 10, 11],
        "Mars": [ 2, 3, 5, 6, 9, 10, 11 ],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [ 1, 4, 7, 8, 10, 11, 12],
        "Venus": [ 3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Ascendant": [3, 6, 10, 11]
    }

    mercury_benefic_houses = {
        "Sun": [5,6,9,11, 12],
        "Moon": [2,4,6,8,10,11],
        "Mars": [1,2,4,7,8,9,10,11],
        "Mercury": [1,3,5,6,9,10,11,12],
        "Jupiter": [6,8,11,12],
        "Venus": [1,2,3,4,5,8,9,11],
        "Saturn": [1,2,4,7,8,9,10,11],
        "Ascendant": [1,2,4,6,8,10,11],
    }

    venus_benefic_houses = {
        "Sun": [8,11,12],
        "Moon": [1,2,3,4,5,8,9,11,12],
        "Mars": [3,5,6,9,11,12],
        "Mercury": [3,5,6,9,11],
        "Jupiter": [5,8,9,10,11],
        "Venus": [1,2,3,4,5,8,9,10,11],
        "Saturn": [3,4,5,8,9,10,11],
        "Ascendant": [1,2,3,4,5,8,9,11],
    }

    mars_benefic_houses = {
        "Sun": [3,5,6,10,11],
        "Moon": [3,6,11],
        "Mars": [1,2,4,7,8,10,11],
        "Mercury": [3,5,6,11],
        "Jupiter": [6,10,11,12],
        "Venus": [6,8,11,12],
        "Saturn": [1,4,7,8,9,10,11],
        "Ascendant": [1,3,6,10,11],
    }

    jupiter_benefic_houses = {
        "Sun": [1,2,3,4,7,8,9,10,11],
        "Moon": [2,5,7,9,11],
        "Mars": [1,2,4,7,8,10,11],
        "Mercury": [1,2,4,5,6,9,10,11],
        "Jupiter": [1,2,3,4,7,8,10,11],
        "Venus": [2,5,6,9,10,11],
        "Saturn": [3,5,6,12],
        "Ascendant": [1,2,4,5,6,7,9,10,11],
    }

    saturn_benefic_houses = {
        "Sun": [1,2,4,7,8,10,11],
        "Moon": [3,6,11],
        "Mars": [3,5,6,10,11,12],
        "Mercury": [6,8,9,10,11,12],
        "Jupiter": [5,6,11,12],
        "Venus": [6,11,12],
        "Saturn": [3,5,6,11],
        "Ascendant": [1,3,4,6,10,11],
    }


    # Initialize Bhinnashtakavarga tables
    bhinnashtakavarga = {planet: [0] * 12 for planet in planets}

    # Calculate bindus for each sign in each planet's Ashtakavarga
    for sign_index in range(12):
        sign_num = sign_index + 1  # Convert to 1-12 format

        # For each contributing planet
        for contributor in planets:
            contributor_pos = planet_positions.get(contributor)
            if contributor_pos is None:
                continue

            # Calculate relative position
            relative_pos = ((sign_num - contributor_pos + 1) % 12)
            if relative_pos == 0:
                relative_pos = 12

            # Check if this relative position gets a bindu
            # Use the appropriate benefic houses dictionary based on which planet's table we're calculating
            if relative_pos in sun_benefic_houses[contributor]:
                bhinnashtakavarga["Sun"][sign_index] += 1
            if relative_pos in moon_benefic_houses[contributor]:
                bhinnashtakavarga["Moon"][sign_index] += 1
            if relative_pos in mercury_benefic_houses[contributor]:
                bhinnashtakavarga["Mercury"][sign_index] += 1
            if relative_pos in venus_benefic_houses[contributor]:
                bhinnashtakavarga["Venus"][sign_index] += 1
            if relative_pos in mars_benefic_houses[contributor]:
                bhinnashtakavarga["Mars"][sign_index] += 1
            if relative_pos in jupiter_benefic_houses[contributor]:
                bhinnashtakavarga["Jupiter"][sign_index] += 1
            if relative_pos in saturn_benefic_houses[contributor]:
                bhinnashtakavarga["Saturn"][sign_index] += 1

    # Calculate Sarvashtakavarga
    sarvashtakavarga = [0] * 12
    for i in range(12):
        for planet in planets:
            sarvashtakavarga[i] += bhinnashtakavarga[planet][i]


    # Also calculate the sarvashtakavarga in the same format
    sarva_total = {zodiac_signs[i]: sarvashtakavarga[i] for i in range(12)}

    bhinnashtakavarga_data = {planet: {zodiac_signs[i]: bhinnashtakavarga[planet][i] for i in range(12)}
                             for planet in planets if planet != "Ascendant"}

    return {

        "sarvashtaka_varga": sarva_total,

        "bhinnashtaka_varga": bhinnashtakavarga_data
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "vedicastroapi:app",
        host="0.0.0.0",
        port=8088,
        reload=True,           # Enable auto-reload
        reload_dirs=["./"],    # Directories to watch for changes
        workers=1              # Number of worker processes
    )
