from json import dumps

from air import PollutionParser
from meteo import MeteoprofileParser


def main(event, context):
    point = event["queryStringParameters"].get("point")
    point_type = event["queryStringParameters"].get("type", "station")

    try:
        data = process(point, point_type)
        status = "OK"
    except RuntimeError as e:
        data = None
        message = f"Error info: {e}"
        status = "Error"

    body = {
        "point_name": point,
        "point_type": point_type,
        "status": status,
    }

    if data:
        body["data"] = data
    else:
        body["message"] = message

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'isBase64Encoded': False,
        'body': dumps(body)
    }


def process(point, point_type):
    if point is None:
        raise RuntimeError("No point specified")

    if point_type == "profiler":
        return MeteoprofileParser().parse(point)
    elif point_type in ("station", "special_station"):
        return PollutionParser().parse(point)
    else:
        raise RuntimeError("Incorrect point type")
