# weather.py

import argparse
import datetime
import json
import sys
from configparser import ConfigParser
from pathlib import Path
from urllib import error, parse, request

import style

BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# Weather Condition Codes
# https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
THUNDERSTORM = range(200, 300)
DRIZZLE = range(300, 400)
RAIN = range(500, 600)
SNOW = range(600, 700)
ATMOSPHERE = range(700, 800)
CLEAR = range(800, 801)
CLOUDY = range(801, 900)

def read_user_cli_args():
    """Handles the CLI user interactions.

    Returns:
        argparse.Namespace: Populated namespace object
    """
    parser = argparse.ArgumentParser(
        description="gets weather and temperature information for a city"
        )
    
    parser.add_argument(
        "city", nargs="+", type=str, help="enter the city name"
        )
    
    parser.add_argument(
        "-i",
        "--imperial",
        action="store_true",
        help="display the temperature in imperial units"
        )
    
    return parser.parse_args()

def _get_api_key():
    """Fetch the API key from your configuration file.

    Expects a configuration file named "secrets.ini" with structure:

        [openweather]
        api_key=<YOUR-OPENWEATHER-API-KEY>
    """
    config_path = Path(__file__).resolve().parent / "secrets.ini"

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Missing config file: {config_path}. "
            "Create secrets.ini in the same folder as weather.py."
        )

    config = ConfigParser()
    config.read(config_path)

    if not config.has_section("openweather"):
        raise KeyError(f"Missing [openweather] section in {config_path}.")

    if not config.has_option("openweather", "api_key"):
        raise KeyError(
            f"Missing 'api_key' option under [openweather] in {config_path}."
        )

    api_key = config.get("openweather", "api_key").strip()

    if not api_key:
        raise ValueError(f"The 'api_key' field in {config_path} is empty.")

    return api_key

def build_weather_query(city_input, imperial=False):
    """Builds the URL for an API request to OpenWeather's weather API.

    Args:
        city_input (List[str]): Name of a city as collected by argparse
        imperial (bool): Whether or not to use imperial units for temperature

    Returns:
        str: URL formatted for a call to OpenWeather's city name endpoint
    """
    api_key = _get_api_key()
    city_name = " ".join(city_input)
    url_encoded_city_name = parse.quote_plus(city_name)
    units = "imperial" if imperial else "metric"
    url = (
        f"{BASE_WEATHER_API_URL}?q={url_encoded_city_name}"
        f"&units={units}&appid={api_key}"
    )
    return url

def get_weather_data(query_url):
    """Makes an API request to a URL and returns the data as a Python object.

    Args:
        query_url (str): URL formatted for OpenWeather's city name endpoint

    Returns:
        dict: Weather information for a specific city
    """
    try:
        response = request.urlopen(query_url)
    except error.HTTPError as http_error:
        if http_error.code == 401: # 401 - Unauthorised
            error_msg = "Access denied. Check your API key."
        elif http_error.code == 404:  # 404 - Not found
            error_msg = "Can't find weather data for this city."
        else:
            error_msg = f"Something went wrong... ({http_error.info()})"
        sys.exit(error_msg)
        
    data = response.read()
    
    try:
        json_data = json.loads(data)
    except json.JSONDecodeError:
        sys.exit("Could not read the server response as a JSON file")
        
    return json_data
        
def display_weather_info(weather_data, imperial=False):
    """Prints formatted weather information about a city.

    Args:
        weather_data (dict): API response from OpenWeather by city name
        imperial (bool): Whether or not to use imperial units for temperature

    More information at https://openweathermap.org/current#name
    """
    
    city = weather_data["name"]
    weather_id = weather_data["weather"][0]["id"]
    temperature = weather_data["main"]["temp"]
    description = weather_data["weather"][0]["description"]
    
    weather_symbol, color = _select_weather_display_params(weather_id)
    
    print(_get_local_date_time(weather_data))
    print('The current temperature in ', end="")
    style.change_color(style.REVERSE)
    print(f'{city}', end="")
    style.change_color(style.RESET)
    print(f' is {temperature:.1f}°{"F" if imperial else "C"}.')
    print(f'{weather_symbol}\tThe weather is ', end="")
    style.change_color(color)
    print(f'{description}')
    style.change_color(style.RESET)
    
def _select_weather_display_params(weather_id):
    # Select parameters for displaying the weather, based on the type of weather in the weather_id
    if weather_id in THUNDERSTORM:
        display_params = ("💥", style.RED)
    elif weather_id in DRIZZLE:
        display_params = ("💧", style.CYAN)
    elif weather_id in RAIN:
        display_params = ("💦", style.BLUE)
    elif weather_id in SNOW:
        display_params = ("⛄️", style.WHITE)
    elif weather_id in ATMOSPHERE:
        display_params = ("🌀", style.BLUE)
    elif weather_id in CLEAR:
        display_params = ("🔆", style.YELLOW)
    elif weather_id in CLOUDY:
        display_params = ("💨", style.WHITE)
    else:  # In case the API adds new weather codes
        display_params = ("🌈", style.RESET)
    return display_params

def _get_local_date_time(weather_data):
    # Returns a local data_time string based on the information in weather_data
    utc_time = weather_data["dt"]
    local_timezone_offset = weather_data["timezone"]
    
    tz = datetime.timezone(datetime.timedelta(seconds=local_timezone_offset))
    local_time = datetime.datetime.fromtimestamp(utc_time, tz)
    
    return local_time.strftime("%A, %d/%m/%y, %#I:%M %p")
    
    

if __name__ == "__main__":
    user_args = read_user_cli_args()
    query_url = build_weather_query(user_args.city, user_args.imperial)
#     print(query_url)
    weather_data = get_weather_data(query_url)
    display_weather_info(weather_data, user_args.imperial)
    
