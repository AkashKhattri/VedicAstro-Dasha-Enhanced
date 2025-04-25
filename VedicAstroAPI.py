from typing import Optional, List, Dict, Any, Union
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
from datetime import datetime, timedelta
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
    filtered_entries = [dasa for dasa in complete_entries if dasa['age_at_start'] >= 20 and dasa['age_at_start'] <=35]
    print(dasa for entry in filtered_entries if entry['mahadasha'] == "Sun" and entry["pratyantardasha"] == "Mercury" and entry["antardasha"]== "Venus")

    return {
        "dashas": filtered_entries
    }



@app.post("/get_marriage_prediction")
async def get_marriage_prediction(horo_input: ChartInput):
    """
    Generates marriage prediction for a given time and location
    """
    horoscope = VedicAstro.VedicHoroscopeData(year=horo_input.year, month=horo_input.month, day=horo_input.day,
                                           hour=horo_input.hour, minute=horo_input.minute, second=horo_input.second,
                                           tz=horo_input.utc, latitude=horo_input.latitude, longitude=horo_input.longitude,
                                           ayanamsa=horo_input.ayanamsa, house_system=horo_input.house_system)
    planets_significators_list = await get_kp_data(horo_input)
    planets_significators_list = planets_significators_list["planet_significators"]

    # Marriage Signifying Houses 2,7,11
    planet_signifying_marriage_houses = [planet for planet in planets_significators_list if any(house in [2, 7, 11] for house in planet["houseSignified"])]

    # Score marriage plantes based on the planets in the marriage houses
    house_score_points = {
        "2": 1,
        "7": 1,
        "11": 1,
    }

    planet_score_points = {}

    for planet in planet_signifying_marriage_houses:
        # Calculate score using house_score_points values
        score = 0
        for house in planet["houseSignified"]:
            if house in [2, 7, 11]:
                score += house_score_points[str(house)]
        planet_score_points[planet["Planet"]] = score

    # Sort the planets by score in descending order
    sorted_planets = sorted(planet_score_points.items(), key=lambda x: x[1], reverse=True)

    return {
        "planet_score_points": sorted_planets,
        "planet_signifying_marriage_houses": planet_signifying_marriage_houses
    }

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


@app.post("/get_kp_data")
async def get_kp_data(horo_input: ChartInput):
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

    # Add planets' aspects on signs
    # planet_aspects_on_signs = horoscope.get_planet_aspects_on_signs(chart)
    # formatted_data["planet_aspects_on_signs"] = planet_aspects_on_signs

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

    formatted_data["rasi_chart"] = reformatted_chart_data

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

    return {"planet_significators":  formatted_data["planet_significators"]}


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

    formatted_data["rasi_chart"] = reformatted_chart_data

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
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

    result = 0
    prev_value = 0

    for char in reversed(roman):
        current_value = values[char]
        if current_value >= prev_value:
            result += current_value
        else:
            result -= current_value
        prev_value = current_value

    return result


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

@app.post("/generate_json_file_transit_data")
async def generate_json_file_transit_data(
    horo_input: ChartInput = None,
    start_year: int = 1990,
    end_year: int = 2100,
    filename: str = None
):
    """
    Generates a JSON file with the transit data from start_year to end_year.
    Data is grouped by planet and sign, showing date ranges for each planet's
    stay in a sign (e.g., "Sun in Sagittarius from 1/1/2024 to 1/19/2024").

    If no chart input is provided, uses default coordinates for New Delhi, India.

    Parameters:
    ----------
    horo_input: ChartInput, optional
        The chart input data. If None, defaults to New Delhi coordinates.
    start_year: int, default=2024
        The starting year for transit calculations
    end_year: int, default=2026
        The ending year for transit calculations
    filename: str, optional
        Custom filename for the JSON output. If None, a default name will be generated.

    Returns:
    -------
    FileResponse
        A downloadable JSON file with transit data grouped by planet and sign
    """
    try:
        # Use New Delhi coordinates if no input is provided
        if horo_input is None:
            horo_input = ChartInput(
                year=2000,  # Arbitrary base year
                month=1,
                day=1,
                hour=12,
                minute=0,
                second=0,
                utc="+05:30",  # India Standard Time
                latitude=28.6139,  # New Delhi latitude
                longitude=77.2090,  # New Delhi longitude
                ayanamsa="Krishnamurti",
                house_system="Placidus"
            )

        # Validate input years
        if start_year >= end_year:
            return {"status": "error", "message": "start_year must be less than end_year"}

        # if end_year - start_year > 200:
        #     return {"status": "error", "message": "Maximum range of 200 years is allowed for transit calculations"}

        # Dictionary to track each planet's position over time
        # Structure: {planet_name: [{sign: "...", start_date: "...", end_date: "...", retrograde: bool}, ...]}
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

            # Format date string (M/D/YYYY)
            month_str = str(current_date.month)
            day_str = str(current_date.day)
            year_str = str(current_date.year)
            date_str = f"{month_str}/{day_str}/{year_str}"

            # Process each planet's transit
            for transit in transit_data:
                planet_name = transit.PlanetName
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

        # Special handling for Moon planet only - convert to compact string format
        if "Moon" in planet_transits:
            moon_data = []
            for transit in planet_transits["Moon"]:
                # Convert sign to number (1-12)
                sign_number = zodiac_signs.index(transit["sign"]) + 1

                # Calculate days in this transit period
                start_date_obj = datetime.strptime(transit["start_date"], "%Y-%m-%d")
                end_date_obj = datetime.strptime(transit["end_date"], "%Y-%m-%d")
                days = (end_date_obj - start_date_obj).days

                # Format as "sign:start_date:days:is_retrograde"
                is_retro_int = 1 if transit["isRetrograde"] else 0
                moon_data.append(f"{sign_number}:{transit['start_date']}:{days}:{is_retro_int}")

            # Replace the Moon's data with the compact string format
            planet_transits["Moon"] = "|".join(moon_data)

        # Return the entire dictionary with all planets
        import json
        return json.dumps(planet_transits, separators=(',', ':'))

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {"status": "error", "message": str(e), "details": error_details}



def generate_transit_markdown(transits_data):
    markdown = "# Planetary Transits\n\n"

    for planet_data in transits_data:
        planet = planet_data["planet"]
        markdown += f"## {planet}\n\n"

        for transit in planet_data["transits"]:
            sign = transit["sign"]
            start = transit["start_date"]
            end = transit["end_date"]
            retrograde = "♺ Retrograde" if transit["isRetrograde"] else "Direct"

            markdown += f"- **{sign}**: {start} to {end} ({retrograde})\n"

        markdown += "\n"

    return markdown

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

        print(start_year, end_year, planets)
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




def generate_transit_markdown(transits_data):
    markdown = "# Planetary Transits\n\n"

    for planet_data in transits_data:
        planet = planet_data["planet"]
        markdown += f"## {planet}\n\n"

        for transit in planet_data["transits"]:
            sign = transit["sign"]
            start = transit["start_date"]
            end = transit["end_date"]
            retrograde = "♺ Retrograde" if transit["isRetrograde"] else "Direct"

            markdown += f"- **{sign}**: {start} to {end} ({retrograde})\n"

        markdown += "\n"

    return markdown

@app.post("/generate_markdown_transit_data")
async def generate_markdown_transit_data(
    horo_input: ChartInput = None,
    start_year: int = 1993,
    end_year: int = 2025,
    planets: List[str] = None  # New parameter to specify which planets to include
):
    """
    Generates highly optimized markdown transit data using minimal tokens.
    Excludes Uranus, Neptune, and Pluto from results.

    Parameters:
    ----------
    horo_input: ChartInput, optional
        The chart input data. If None, defaults to New Delhi coordinates.
    start_year: int, default=1993
        The starting year for transit calculations
    end_year: int, default=2025
        The ending year for transit calculations
    planets: List[str], optional
        List of planets to include in the results (e.g., ["Sun", "Moon", "Saturn"]).
        If not provided, all planets except Uranus, Neptune, and Pluto will be included.
    """
    try:
        # Use New Delhi coordinates if no input is provided
        if horo_input is None:
            horo_input = ChartInput(
                year=2000,
                month=1,
                day=1,
                hour=12,
                minute=0,
                second=0,
                utc="+05:30",
                latitude=28.6139,
                longitude=77.2090,
                ayanamsa="Krishnamurti",
                house_system="Placidus"
            )

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
                        "end_date": date_str,
                        "isRetrograde": prev_retro
                    })

                    # Update current state with new sign
                    current_planet_states[planet_name] = (sign, date_str, is_retrograde)

            # Move to the next day
            current_date += timedelta(days=1)

        # Record final states for all planets
        end_date_str = f"{end_date.year}-{end_date.month:02d}-{end_date.day:02d}"
        for planet_name, (sign, start_date, is_retrograde) in current_planet_states.items():
            planet_transits[planet_name].append({
                "sign": sign,
                "start_date": start_date,
                "end_date": end_date_str,
                "isRetrograde": is_retrograde
            })

        # Planet and sign abbreviations
        planet_abbr = {
            "Sun": "Su", "Moon": "Mo", "Mercury": "Me",
            "Venus": "Ve", "Mars": "Ma", "Jupiter": "Ju",
            "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
        }

        sign_abbr = {
            "Aries": "1", "Taurus": "2", "Gemini": "3", "Cancer": "4",
            "Leo": "5", "Virgo": "6", "Libra": "7", "Scorpio": "8",
            "Sagittarius": "9", "Capricorn": "10", "Aquarius": "11", "Pisces": "12"
        }

        # Generate ultra-compact markdown
        markdown = "#Transits\n"

        for planet, transits in planet_transits.items():
            p_code = planet_abbr.get(planet, planet[:2])
            markdown += f"{p_code}:"

            transit_parts = []
            for t in transits:
                # Further optimize dates by using YY-MM-DD format
                start = t["start_date"].replace("-", "")[2:]  # YYYYMMDD → YYMMDD
                end = t["end_date"].replace("-", "")[2:]      # YYYYMMDD → YYMMDD

                sign_code = sign_abbr.get(t["sign"], t["sign"][:2])
                r_mark = "R" if t["isRetrograde"] else ""

                transit_parts.append(f"{sign_code}{r_mark}:{start}/{end}")

            markdown += ",".join(transit_parts) + "\n"

        return Response(content=markdown, media_type="text/markdown")

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

@app.post("/get_astrocartography_data")
async def get_astrocartography_data(horo_input: ChartInput, planets: List[str] = None):
    """
    Generate astrocartography data for a birth chart.
    Returns planetary lines data suitable for rendering on a world map.

    Parameters:
    ----------
    horo_input: ChartInput
        The chart input data (birth details)
    planets: List[str], optional
        List of planets to include in the analysis. If None, all major planets are included.

    Returns:
    -------
    JSON response containing astrocartography data:
        - status: Success or error status
        - birthLocation: The birth location coordinates
        - lines: Array of planetary line data for mapping
    """
    try:


        # Create a VedicHoroscopeData object from the input
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

        # Create an AstrocartographyCalculator instance
        try:
            astrocartography = AstrocartographyCalculator(horoscope)
            print("Successfully created AstrocartographyCalculator")
        except Exception as e:
            print(f"Error creating AstrocartographyCalculator: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"status": "error", "message": f"Error initializing astrocartography: {str(e)}"}

        # Process the planets list if provided
        planet_list = None
        if planets:
            print(f"Processing planets list: {planets}")
            # Convert common name formats to flatlib planet constants
            planet_mapping = {
                "sun": const.SUN,
                "moon": const.MOON,
                "mercury": const.MERCURY,
                "venus": const.VENUS,
                "mars": const.MARS,
                "jupiter": const.JUPITER,
                "saturn": const.SATURN,
                "uranus": const.URANUS,
                "neptune": const.NEPTUNE,
                "pluto": const.PLUTO,
                "rahu": const.NORTH_NODE,
                "ketu": const.SOUTH_NODE,
                "north node": const.NORTH_NODE,
                "south node": const.SOUTH_NODE,
                # Add capitalized versions too
                "Sun": const.SUN,
                "Moon": const.MOON,
                "Mercury": const.MERCURY,
                "Venus": const.VENUS,
                "Mars": const.MARS,
                "Jupiter": const.JUPITER,
                "Saturn": const.SATURN,
                "Uranus": const.URANUS,
                "Neptune": const.NEPTUNE,
                "Pluto": const.PLUTO,
                "Rahu": const.NORTH_NODE,
                "Ketu": const.SOUTH_NODE,
                "North Node": const.NORTH_NODE,
                "South Node": const.SOUTH_NODE
            }

            try:
                planet_list = []
                for p in planets:
                    if isinstance(p, str):
                        # First try direct mapping
                        if p in planet_mapping:
                            planet_list.append(planet_mapping[p])
                        else:
                            # Try case-insensitive match if direct mapping fails
                            p_lower = p.lower()
                            if p_lower in planet_mapping:
                                planet_list.append(planet_mapping[p_lower])
                            else:
                                print(f"Warning: Unknown planet '{p}', skipping")

                if not planet_list:
                    print("No valid planets found, using default planets")
                    planet_list = None
                else:
                    print(f"Mapped planets: {planet_list}")
            except Exception as e:
                print(f"Error mapping planets: {str(e)}")
                planet_list = None

        # Get the astrocartography data
        try:
            astro_data = astrocartography.get_astrocartography_data(planet_list)
            print("Successfully calculated astrocartography data")
            return astro_data
        except Exception as e:
            print(f"Error calculating astrocartography data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {"status": "error", "message": f"Error calculating astrocartography data: {str(e)}"}

    except Exception as e:
        print(f"Unexpected error in get_astrocartography_data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.post("/get_yogas")
async def get_yogas(horo_input: ChartInput, categorize_by_influence: bool = False):
    """
    Analyzes a birth chart to identify important Hindu astrological yogas (planetary combinations).
    Returns a list of yogas present in the chart with descriptions.

    Args:
        horo_input: Chart input data
        categorize_by_influence: If True, yogas will be categorized as benefic or malefic
                               If False (default), yogas will be categorized by traditional types
    """
    # First get the KP data which contains all planetary positions we need
    kp_data = await get_kp_data(horo_input)

    # Get the rasi chart data which uses Lahiri ayanamsa
    rasi_chart_data = kp_data["rasi_chart"]

    # Create consolidated planet positions directly from rasi chart data
    # This is more accurate for yoga calculations as it properly reflects
    # the sidereal zodiac positions
    planet_positions = {}
    houses_data = {house["HouseNr"]: house for house in kp_data["cusps"]}

    # Define sign rulerships according to Vedic astrology
    sign_lords = {
        "Aries": "Mars",
        "Taurus": "Venus",
        "Gemini": "Mercury",
        "Cancer": "Moon",
        "Leo": "Sun",
        "Virgo": "Mercury",
        "Libra": "Venus",
        "Scorpio": "Mars",
        "Sagittarius": "Jupiter",
        "Capricorn": "Saturn",
        "Aquarius": "Saturn",
        "Pisces": "Jupiter"
    }

    # Process the rasi chart data to create a proper planet_positions dictionary
    for sign_data in rasi_chart_data:
        rasi = sign_data["Rasi"]
        for planet_entry in sign_data["Planets"]:
            planet_name = planet_entry["Name"]

            # Find which house this planet is in
            house_nr = None
            for house_num, house_data in houses_data.items():
                if house_data["Rasi"] == rasi:
                    house_nr = house_num
                    break

            # If house not found, use a fallback method from planets data
            if house_nr is None:
                for planet in kp_data["planets"]:
                    if planet["Object"] == planet_name:
                        house_nr = planet["HouseNr"]
                        break

            # Skip if we couldn't determine the house
            if house_nr is None:
                continue

            # Gather retrograde information from planets data
            is_retrograde = False
            for planet in kp_data["planets"]:
                if planet["Object"] == planet_name:
                    is_retrograde = planet["isRetroGrade"]
                    break

            planet_positions[planet_name] = {
                "Object": planet_name,
                "Rasi": rasi,
                "RasiLord": sign_lords.get(rasi, ""),  # Add the rasi lord for each planet
                "HouseNr": house_nr,
                "isRetroGrade": is_retrograde,
                # Include other necessary data for yoga calculations
                "SignLonDecDeg": planet_entry.get("SignLonDecDeg", 0),
                "LonDecDeg": planet_entry.get("LonDecDeg", 0)
            }
    print(planet_positions)
    # Enhance houses_data with proper rasi lord information
    for house_num, house_data in houses_data.items():
        rasi = house_data["Rasi"]
        houses_data[house_num]["RasiLord"] = sign_lords.get(rasi, "")

    # Get all yoga results by traditional categories
    traditional_yogas = {
        "raj_yogas": check_raj_yogas(planet_positions, houses_data),
        "dhana_yogas": check_dhana_yogas(planet_positions, houses_data),
        "pancha_mahapurusha_yogas": check_pancha_mahapurusha_yogas(planet_positions),
        "nabhasa_yogas": check_nabhasa_yogas(planet_positions),
        "other_yogas": check_other_yogas(planet_positions, houses_data),
        "additional_benefic_yogas": check_additional_benefic_yogas(planet_positions, houses_data),
        "intellectual_yogas": check_intellectual_yogas(planet_positions, houses_data),
        "malefic_yogas": check_malefic_yogas(planet_positions, houses_data)
    }

    # If requested, recategorize yogas by their influence (benefic or malefic)
    if categorize_by_influence:
        benefic_yogas = []
        malefic_yogas = []

        # Categorize traditional yogas by influence
        benefic_categories = ["raj_yogas", "dhana_yogas", "pancha_mahapurusha_yogas",
                            "additional_benefic_yogas", "intellectual_yogas", "other_yogas"]

        for category in benefic_categories:
            for yoga in traditional_yogas[category]:
                # Skip some yogas from other_yogas that are actually malefic
                if category == "other_yogas" and yoga["name"] in ["Kemadruma Yoga", "Kala Sarpa Yoga", "Shakata Yoga"]:
                    malefic_yogas.append(yoga)
                else:
                    benefic_yogas.append(yoga)

        # Add malefic yogas
        malefic_yogas.extend(traditional_yogas["malefic_yogas"])

        # Some Nabhasa yogas can be either benefic or malefic depending on planets involved
        # For simplicity, we'll add them to benefic category
        benefic_yogas.extend(traditional_yogas["nabhasa_yogas"])

        # Return yogas categorized by influence
        return {
            "benefic_yogas": benefic_yogas,
            "malefic_yogas": malefic_yogas,
            "total_yogas": len(benefic_yogas) + len(malefic_yogas)
        }

    # Return yogas categorized by traditional types
    return traditional_yogas

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
