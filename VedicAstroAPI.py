from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from vedicastro import VedicAstro, horary_chart
from vedicastro.compute_dasha import compute_vimshottari_dasa_enahanced
from vedicastro.utils import pretty_data_table
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


    # Convert NamedTuple to list of dictionaries with named fields
    formatted_data = []
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
            "Rasi Lord": planet.RasiLord,
            "Nakshatra Lord": planet.NakshatraLord,
            "Sub Lord": planet.SubLord,
            "Sub Sub Lord": planet.SubSubLord,
            "House Number": planet.HouseNr
        }
        formatted_data.append(planet_dict)

    return (formatted_data)

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

    # Calculate the D-9 chart
    d9_chart = []
    for planet in formatted_data:
        current_sign = planet["Rasi"]
        sign_lon_dec_deg = planet["SignLonDecDeg"]

        # Calculate the D-9 position
        new_sign, new_degree = calculate_d9_position(current_sign, sign_lon_dec_deg)

        # Append to the D-9 chart
        d9_chart.append({
            "Object": planet["Object"],
            "Current Sign": current_sign,
            "Current Sign Index": zodiac_signs.index(current_sign) + 1,  # Add 1 for 1-based index
            "D-9 Rasi": new_sign,
            "D-9 Sign Index": zodiac_signs.index(new_sign) + 1,
            "D-9 Degree": new_degree,
            "House Number": planet["House Number"]
        })

    return d9_chart

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




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "VedicAstroAPI:app",
        host="0.0.0.0",
        port=8088,
        reload=True,           # Enable auto-reload
        reload_dirs=["./"],    # Directories to watch for changes
        workers=1              # Number of worker processes
    )
