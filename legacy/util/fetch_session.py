from requests_html import HTMLSession


def fetch_url(url):
    # Start a session
    session = HTMLSession()

    # Make a request to the page
    response = session.get(url)
    # response.html.arender()
    response.html.arender(sleep=20, timeout=0)

    # Check the status code of the response
    print(f"Status Code: {response.status_code}")

    # Print the content of the r`esponse
    # print(f"Response Content:\n{response.text[:200]}...") # Print first 200 characters
    if response.status_code == 200:
        return response.content
    else:
        return None
