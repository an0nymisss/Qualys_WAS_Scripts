# Input file: urls.txt
# Usage: python3 Qualys_WAS_Bulk_URL_Deletion.py 
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
DELETION_URL = BASE_URL + "/delete/was/webapp/"
ID_FETCH_URL = BASE_URL + "/search/was/webapp"
USERNAME = ""   # Your username                       
PASSWORD = ""   # Your password


def are_creds_valid():

    response = requests.get(
        LOGIN_URL,
        auth=(USERNAME,PASSWORD),  #Basic authentication
        verify=False
    )

    if response.status_code == 401:
        return False

    return True


def find_all_matching_urls(input_url):

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
        ID_FETCH_URL,
        data=xml_data,
        auth=(USERNAME,PASSWORD),
        verify=False
    )

    if response.status_code == 200:
    #fetch all urls that match with input file url
        urls = []
        tree = ET.fromstring(response.text)
        data = tree.find("data")

        if int(tree.find("count").text) >= 1:
            for i in data:
                qualys_url = i.find("url").text 
                urls.append(qualys_url)
        
            delete_urls(urls, input_url)
        
        else:
            print("URL not found in Qualys: " + input_url)
            #append output to file
            message = "URL not found in Qualys: " + input_url
            save_output_to_file(message)


def delete_urls(urls, input_url):

    del_flag = False   
    for url in urls:

        url_tldextract = tldextract.extract(url)
        if url_tldextract.subdomain:
            url_tld = url_tldextract.subdomain + "." + url_tldextract.domain + "." + url_tldextract.suffix
        else:
            url_tld = url_tldextract.domain + "." + url_tldextract.suffix

        input_url_tldextract = tldextract.extract(input_url)
        if input_url_tldextract.subdomain:
            input_tld = input_url_tldextract.subdomain + "." + input_url_tldextract.domain + "." + input_url_tldextract.suffix
        else:
            input_tld = input_url_tldextract.domain + "." + input_url_tldextract.suffix

        if url.startswith(f'http://{input_tld}') or url.startswith(f'https://{input_tld}'):
            if input_tld == url_tld:
                
                headers = {
                    "Content-Type": "application/xml"
                }

                xml_data = f"""<ServiceRequest>
            <filters>
            <Criteria field="url" operator="EQUALS">{url}</Criteria>
            </filters>
            </ServiceRequest>"""

                response = requests.post(
                    DELETION_URL,
                    data=xml_data,
                    auth=(USERNAME,PASSWORD),
                    verify=False
                )

                if response.status_code == 200:
                    #parse xml response
                    tree = ET.fromstring(response.text)
                    data = tree.find("responseCode").text
                    
                    if data == "SUCCESS":
                        print("URL deleted: " + url)
                        del_flag = True
                        #append output to file
                        message = "URL deleted: " + url
                        save_output_to_file(message)
    
    if del_flag == False:
        print("URL not deleted: " + input_url)
        #append output to file
        message = "URL not deleted: " + input_url
        save_output_to_file(message)


def print_error(response):
    print("Error Status Code: {}".format(response.status_code))
    print("Error Message: {}".format(response.text))


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
            url_to_delete = url.strip()
            find_all_matching_urls(url_to_delete)


if __name__ == "__main__":
    main()