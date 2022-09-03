# Input file: urls.txt
# Usage: python3 Qualys_WAS_Onboarded_URL_Search.py 
# Output file created: output.txt

from getpass import getpass
import requests
import tldextract
import xml.etree.ElementTree as ET
import urllib3
urllib3.disable_warnings()

''' Globals '''
BASE_URL = "https://qualysapi.qualys.com/qps/rest/3.0"  # Qualys API Base URL (Change if required)
LOGIN_URL = BASE_URL + "/count/was/webapp"
FETCH_URL = BASE_URL + "/search/was/webapp"
USERNAME = ""   # Your username
PASSWORD = ""   # Your password


def are_creds_valid():

    response = requests.get(
        LOGIN_URL,
        auth=(USERNAME,PASSWORD),  # Basic authentication
        verify=False
    )

    if response.status_code == 401:
        return False

    return True


def find_all_matching_urls(input_url):

    url_found_flag = False

    url_tldextract = tldextract.extract(input_url)
    if url_tldextract.subdomain:
        input_url_tld = url_tldextract.subdomain + "." + url_tldextract.domain + "." + url_tldextract.suffix
    else:
        input_url_tld = url_tldextract.domain + "." + url_tldextract.suffix

    headers = {
        "Content-Type": "application/xml"
    }

    xml_data = f"""<ServiceRequest>
<filters>
 <Criteria field="url" operator="CONTAINS">{input_url_tld}</Criteria>
</filters>
</ServiceRequest>"""

    response = requests.post(
        FETCH_URL,
        data=xml_data,
        auth=(USERNAME,PASSWORD),
        verify=False
    )

    if response.status_code == 200:
    # Fetch all urls that match with input file url
        tree = ET.fromstring(response.text)
        data = tree.find("data")

        if int(tree.find("count").text) >= 1:
            for i in data:
                qualys_url = i.find("url").text 

                qualys_url_tldextract = tldextract.extract(qualys_url)
                if qualys_url_tldextract.subdomain:
                    qualys_url_tld = qualys_url_tldextract.subdomain + "." + qualys_url_tldextract.domain + "." + qualys_url_tldextract.suffix
                else:
                    qualys_url_tld = qualys_url_tldextract.domain + "." + qualys_url_tldextract.suffix

                if qualys_url.startswith(f'http://{input_url_tld}') or qualys_url.startswith(f'https://{input_url_tld}'):
                    if input_url_tld == qualys_url_tld:
                        url_found_flag = True
                        print("URL is already onboarded in Qualys: " + qualys_url)
                        message = "URL is already onboarded in Qualys: " + qualys_url
                        save_output_to_file(message)
                    
        
        if url_found_flag == False:
            print("URL not onboarded in Qualys: " + input_url)
            message = "URL not onboarded in Qualys: " + input_url
            save_output_to_file(message)

    else:
        print(f"API Error for {input_url}")
        print(f"Response Code: {response.status_code}")
        print(response.text)


def save_output_to_file(message):
    with open('output.txt', 'a') as f:
        f.write(message + "\n")


def main():
    are_valid_creds = are_creds_valid()

    if not are_valid_creds:
        print("[-] Invalid Qualys Credentials!")
        exit(1)

    with open("urls.txt", "r") as f:
        for url in f:
            url_to_search = url.strip()
            find_all_matching_urls(url_to_search)


if __name__ == "__main__":
    main()