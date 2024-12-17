from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from vedicastro import VedicAstro, horary_chart
from vedicastro.compute_dasha import compute_vimshottari_dasa_enahanced
from vedicastro.utils import pretty_data_table


app = FastAPI()

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


    # chart = horoscope.generate_chart()

    # planets_data = horoscope.get_planets_data_from_chart(chart)
    # houses_data = horoscope.get_houses_data_from_chart(chart)
    # planet_significators = horoscope.get_planet_wise_significators(planets_data, houses_data)
    # planetary_aspects = horoscope.get_planetary_aspects(chart)
    # house_significators = horoscope.get_house_wise_significators(planets_data, houses_data)
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
    # consolidated_chart_data = horoscope.get_consolidated_chart_data(planets_data=planets_data,
    #                                                                 houses_data=houses_data,
    #                                                                 return_style = horo_input.return_style)

    return vimshottari_dasa

    # return {
    #     "vimshottari_dasa": vimshottari_dasa,
    #     # "planets_data": [planet._asdict() for planet in planets_data],
    #     # "houses_data": [house._asdict() for house in houses_data],
    #     # "planet_significators": planet_significators,
    #     # "planetary_aspects": planetary_aspects,
    #     # "house_significators": house_significators,
    #     # "consolidated_chart_data": consolidated_chart_data
    # }


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

    return str(consolidated_chart_data)

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
