def main():
    import sys
    global shutil
    import shutil
    import argparse
    import sqlite3
    import requests
    import datetime
    from termcolor import colored

    # Argparse setup
    parser = argparse.ArgumentParser()
    parser.add_argument("-k",   "--key",       help="Set api key")
    parser.add_argument("-lat", "--latitude",  help="Set latitude")
    parser.add_argument("-lon", "--longitude", help="Set longitude")
    parser.add_argument("-a",   "--ascii",     help="Use only ascii characters", action="store_true")
    args = parser.parse_args()

    # Check whether the unicode icons or the text should be used
    # based on input the input parameter '--ascii'.
    if args.ascii:
        UP_ARROW = "Max:"
        DOWN_ARROW = "Min:"
    else:
        UP_ARROW = "▴"
        DOWN_ARROW = "▾"

    # Connect to and set up sqlite3 database
    con = sqlite3.connect(__file__.replace("main.py", "") + "fetch_info.db")
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS fetch_info(api_key, lon, lat)")
    if c.execute("SELECT * FROM fetch_info").fetchall() == []:
        c.execute("INSERT INTO fetch_info VALUES('key', 'lon', 'lat')")

    # Try to set the database values from values of the arguments '--key', '--lat' and '--lon'.
    collect_values(sys, args.key, "Key", "api_key")
    collect_values(sys, args.latitude, "Latitude", "lat")
    collect_values(sys, args.longitude, "Longitude", "lon")

    # Get the api parameters from the database.
    api_key = c.execute("SELECT api_key FROM fetch_info").fetchone()[0]
    lat = c.execute("SELECT lat FROM fetch_info").fetchone()[0]
    lon = c.execute("SELECT lon FROM fetch_info").fetchone()[0]

    try:
        # Try to send an api request.
        response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric").json()
        if response["cod"] == 200:
            # Define and format response
            city_name = response["name"]
            main_temp = response["main"]["temp"]
            weather_description = response["weather"][0]["description"].title()
            max_temp = response["main"]["temp_max"]
            min_temp = response["main"]["temp_min"]
            feels_like = response["main"]["feels_like"]
            wind_speed = str(round(response["wind"]["speed"] * 10) / 10)
            wind_dir = get_direction(response["wind"]["deg"])
            wind_gust = str(round(response["wind"]["gust"] * 10) / 10)
            sunrise = str(datetime.datetime.fromtimestamp(response["sys"]["sunrise"]))[11:-3]
            sunset = str(datetime.datetime.fromtimestamp(response["sys"]["sunset"]))[11:-3]
            sun_color = get_sun_color(sunrise, sunset)


            # Print
            print()
            printc(f"Weather in " + city_name)
            printc(
                colored(str(round(main_temp)) + "°", get_temp_color(main_temp), attrs=["bold"]) + ", " +
                weather_description, str(round(main_temp)) + "°, " + weather_description
            )
            printc(
                colored(f"{UP_ARROW} ", "green") + colored(str(round(max_temp)) + "°", get_temp_color(max_temp),
                attrs=["bold"]) + ", "+ colored(f"{DOWN_ARROW} ", "red") + colored(str(round(min_temp)) + "°",
                get_temp_color(min_temp), attrs=["bold"]), UP_ARROW + " " +
                str(round(response["main"]["temp_max"])) + "°, " + DOWN_ARROW + str(round(min_temp)) + "°"
            )
            printc(
                "Feels like "+ colored(str(round(feels_like)) + "°", get_temp_color(feels_like), attrs=["bold"]),
                "Feels like " + str(round(feels_like)) + "°"
            )
            printc(
                "Wind is blowing " + colored(wind_dir, "magenta", attrs=["bold"]) + " at " + colored(wind_speed +
                " m/s", get_wind_speed_color(wind_speed), attrs=["bold"]) + ", with gusts up to " +
                colored(wind_gust + " m/s", get_wind_speed_color(wind_gust), attrs=["bold"]),
                "Wind is blowing " + wind_dir + " at " + str(round(response["wind"]["speed"])) +
                " m/s, with gusts up to " + wind_gust
            )
            printc(
                "Sun is up from " + colored(sunrise, sun_color, attrs=["bold"]) + " to " + colored(sunset,
                sun_color, attrs=["bold"]), "Sun is up from " + sunrise + " to " + sunset
            )

        elif response["cod"] == 401:
            print("Invalid API key. Get one from https://www.openweathermap.org and use the --key option to set it")

        elif response["cod"] == "400":
            print(response["message"].capitalize())

        else: print(response)

    except(requests.exceptions.ConnectionError):
        print("Could not connect to openweathermap.org")

    except Exception as e: print(e)



def collect_values(sys, argument, argument_litteral, sql_entry):
    if argument is None: return 0

    try:
        if "\"" in argument or "'" in argument:
            print(f"{argument_litteral} can not contain \" nor '")
            sys.exit(0)

        if argument == "":
            print(f"{argument_litteral} can not be empty")
            sys.exit(0)

        c.execute(f"UPDATE fetch_info SET {sql_entry} = '{argument}'")
        con.commit()
        return 0

    except Exception as e:
        print(e)
        if check_for_sql_value(sql_entry):
            print(argument_litteral + " has to be set")
            sys.exit(0)



def check_for_sql_value(value):
    return 1 if c.execute(f"SELECT '{value}' FROM fetch_info").fetchone() is None else 0



def printc(s_color, s_no_color=False):
    print(get_spaces(s_no_color) + s_color) if s_no_color != False else print(get_spaces(s_color) + s_color)



def get_spaces(s):
    return " " * int((shutil.get_terminal_size().columns - len(s)) / 2)



def get_direction(degrees):
    if degrees < 23 or degrees >= 338:
        return "north"

    elif degrees < 68:
        return "north east"

    elif degrees < 113:
        return "east"

    elif degrees < 158:
        return "south east"

    elif degrees < 203:
        return "south"

    elif degrees < 248:
        return "south west"

    elif degrees < 293:
        return "west"

    elif degrees < 338:
        return "north west"

    else: return "in an unknown direction"



def get_temp_color(temp):
    temp = round(temp)
    if temp <= -10:
        return "magenta"

    elif temp <= -5:
        return "blue"

    elif temp <= 5:
        return "cyan"

    elif temp <= 10:
        return "blue"

    elif temp <= 20:
        return "green"

    elif temp <= 25:
        return "yellow"

    else: return "red"



def get_wind_speed_color(wind_speed):
    wind_speed = round(float(wind_speed) * 10) / 10
    if wind_speed < 10:
        return "cyan"

    elif wind_speed < 20:
        return "green"

    elif wind_speed < 30:
        return "yellow"

    else: return "red"



def get_sun_color(sunrise, sunset):
    daytime = int(sunrise[:2]) - int(sunset[:2])
    if daytime < 4 or daytime >= 20:
        return "red"

    elif daytime < 8 or daytime >= 16:
        return "yellow"

    else: return "green"



if __name__ == "__main__": main()
