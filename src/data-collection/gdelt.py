import pandas as pd
import json
from os.path import abspath, isfile as fileExists
from urllib.request import urlopen
from urllib.parse import urlencode

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
OIL_RELATED_THEMES = [
    "ENV_OIL",
    "ENV_NATURALGAS",
    "ENV_COAL",
    "ENV_BIOFUEL",
    "ENV_GREEN",
    "ENV_SOLAR",
    "ENV_WINDPOWER",
    "ENV_HYDRO",
    # "ENV_NUCLEARPOWER",
    "ENV_GEOTHERMAL",
    # "FUELPRICES",
    # "PIPELINE_INCIDENT",
    # "ECON_COST_OF_LIVING",
    # "ECON_TRADE_DISPUTE",
    # "ECON_CURRENCY_EXCHANGE_RATE",
    # "ECON_CURRENCY_RESERVES",
    # "ECON_FOREIGNINVEST",
    # "ECON_SUBSIDIES",
    # "ECON_PRICECONTROL",
    # "ECON_STOCKMARKET",
    # "ECON_BANKRUPTCY",
    # "ECON_DEBT",
    # "ECON_INTEREST_RATES",
    # "ECON_NATIONALIZE",
    # "ECON_BOYCOTT",
    # "SANCTIONS",
    # "ECON_TAXATION",
    # "POVERTY",
    # "UNEMPLOYMENT",
    # "BLOCKADE",
    # "SEIGE",
    # "MARITIME",
    # "MARITIME_INCIDENT",
    # "PIRACY",
    # "ORGANIZED_CRIME",
    # "SMUGGLING",
    # "BLACK_MARKET",
    # "MIL_SELF_IDENTIFIED_ARMS_DEAL",
    # "MILITARY_COOPERATION",
    # "POLITICAL_TURMOIL",
    # "UNREST_CHECKPOINT",
    # "UNREST_CLOSINGBORDER",
    # "UNREST_HUNGERSTRIKE",
    # "UNREST_MOLOTOVCOCKTAIL",
    # "UNREST_POLICEBRUTALITY",
    # "UNREST_STONETHROWING",
    # "UNREST_STONING",
    # "VIOLENT_UNREST",
    # "PROTEST",
    # "STRIKE",
    # "REBELLION",
    # "REBELS",
    # "INSURGENCY",
    # "TERROR",
    # "SELF_IDENTIFIED_ENVIRON_DISASTER",
    # "ENV_MINING",
    # "ENV_METALS",
    # "WATER_SECURITY",
    # "FOOD_SECURITY",
    # "FOOD_STAPLE",
    # "SHORTAGE",
    # "MOVEMENT_ENVIRONMENTAL"
]
DEBUG_FILE = abspath("./debug_file.json")


def getData(mode="ArtList", format_result="json",timespan="60m", max_records=10, debug = False):
    """
    TODO: Update with params description
    """

    # Building URL
    query = f"({" OR ".join(f'theme:{theme}' for theme in OIL_RELATED_THEMES)})"
    params = {
        "query": query,
        "format": format_result,
        "mode": mode,
        "timespan": timespan,
        "maxRecords": max_records,
    }
    formattedUrl = BASE_URL + "?" + urlencode(params)


    if debug and fileExists(DEBUG_FILE):
        with open(DEBUG_FILE, "r", encoding="utf-8") as debug_file:
            jsonData = json.loads(debug_file.read())
            articles = jsonData.get("articles", None)
            if articles is None:
                raise RuntimeError
            df = pd.DataFrame(articles)
    else:  
        with urlopen(formattedUrl) as response:
            data = response.read()
            data.decode('utf-8')

            parsed_json = json.loads(data)
            if debug:
                with open(DEBUG_FILE,"w", encoding="utf-8") as debug_file:
                    debug_file.write(json.dumps(parsed_json))
            articles = parsed_json.get("articles", None)
            if articles is None:
                raise RuntimeError
            df = pd.DataFrame(articles)
            return df    

    




def main():
    getData(debug=True)
    # print(fileExists(DEBUG_FILE))

main()
