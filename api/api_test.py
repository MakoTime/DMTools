import argparse

import requests


URL_BASE = "https://www.dnd5eapi.co/api/2014/"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test API requests")
    parser.add_argument(
        "endpoint",
        type=str,
        nargs="?",
        default="",
        help="API endpoint to test",
    )
    args = parser.parse_args()

    url = URL_BASE + args.endpoint

    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=10,
    )

    print(f"Status: {response.status_code}")
    print(response.text)

