import requests


def fetch_url(url):
    response = requests.get(url)

    # Check the status code of the response
    print(f"Status Code: {response.status_code}")

    # Print the content of the r`esponse
    # print(f"Response Content:\n{response.text[:200]}...") # Print first 200 characters
    if response.status_code == 200:
        return response.content
    else:
        return None
