# Input file: data.csv
'''Sample values of data.csv:
URL,SCID
http://test.com,1234
https://example.com,6789
'''  
# Usage: python3 Qualys_WAS_Bulk_URL_SCID_Updation.py
# Output file created: output.txt

from getpass import getpass
import xml.etree.ElementTree as ET
import requests
import csv
import tldextract
import urllib3
urllib3.disable_warnings()

''' Globals '''
BASE_URL = "https://qualysapi.qualys.com/qps/rest/3.0"  # Qualys API Base URL (Change if required)
LOGIN_URL = BASE_URL + "/count/was/webapp"
ID_FETCH_URL = BASE_URL + "/search/was/webapp"
UPDATION_URL = BASE_URL + "/update/was/webapp/{}"
INPUT_FILE = "data.csv"
USERNAME = ""   # Your username                       
PASSWORD = ""   # Your password


def are_creds_valid() -> bool:
    """
    Returns True if credentials are valid
    """

    response = requests.get(
        LOGIN_URL,
        auth=(USERNAME,PASSWORD),  #Basic authentication
        verify=False
    )

    if response.status_code == 401:
        return False

    return True


def find_all_matching_urls(input_url: str, new_scid: str) -> None:
    """
    Extracts all URLs containing the same TLD as input URL
    Validates the extracted URLs with Input URLs
    Fetches URL ID and proceeds to update SCID based on validation

    Args:
        input_url: URL in CSV file for which SCID is to be updated
        new_scid: Value of the new SCID

    Returns:
        None 
    """

    update_flag = False

    input_url_tldextract = tldextract.extract(input_url)
    if input_url_tldextract.subdomain:
        input_url_tld = input_url_tldextract.subdomain + "." + input_url_tldextract.domain + "." + input_url_tldextract.suffix
    else:
        input_url_tld = input_url_tldextract.domain + "." + input_url_tldextract.suffix

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

                        url_id = fetch_url_id(qualys_url)   
                        update_flag = url_scid_updated(qualys_url, url_id, new_scid)   
                        if update_flag:
                            print("URL SCID updated: " + qualys_url)
                            #append output to file
                            message = "URL SCID updated: " + qualys_url
                            save_output_to_file(message)     

            if update_flag == False:
                print("URL SCID not updated: " + input_url)
                message = "URL SCID not updated: " + input_url
                save_output_to_file(message)             
    
        else:
            print("URL not found in Qualys: " + input_url)
            #append output to file
            message = "URL not found in Qualys: " + input_url
            save_output_to_file(message)


def fetch_url_id(url: str) -> str:
    """
    Fetches and returns the WebApp ID of the given URL
    """

    headers = {
        "Content-Type": "application/xml"
    }

    xml_data = f"""<ServiceRequest>
<filters>
 <Criteria field="url" operator="EQUALS">{url}</Criteria>
</filters>
</ServiceRequest>"""

    response = requests.post(
        ID_FETCH_URL,
        data=xml_data,
        auth=(USERNAME,PASSWORD),
        verify=False
    )

    if response.status_code == 200:

        tree = ET.fromstring(response.text)
        data = tree.find("data")
        for i in data:
            url_id = i.find("id").text
        return url_id

    return ""
        

def url_scid_updated(url: str, url_id: str, new_scid: str) -> bool:
    """
    Returns True if SCID is updated successfully for the given URL
    """

    if url_id == "" or new_scid == "":
        return False

    headers = {
        "Content-Type": "application/xml"
    }

    xml_data = f"""<ServiceRequest>
 <data>
 <WebApp>
 <attributes>
 <update>
 <Attribute>
 <name>SCID</name>
 <value><![CDATA[{new_scid}]]></value>
 </Attribute>
 </update>
 </attributes>
 </WebApp>
 </data>
</ServiceRequest>"""

    response = requests.post(
        UPDATION_URL.format(url_id),
        data=xml_data,
        auth=(USERNAME,PASSWORD),
        verify=False
    )

    if response.status_code == 200:
        #parse xml response
        tree = ET.fromstring(response.text)
        data = tree.find("responseCode").text
        
        if data == "SUCCESS":
            return True

    return False


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

    file = open('data.csv')
    csvreader = csv.reader(file)
    fields = next(csvreader)
    for count, row in enumerate(csvreader):
        url = row[0]
        new_scid = row[1]
        if new_scid and url:
            find_all_matching_urls(url, new_scid)
        else:
            print(f"Please enter valid URL and/or SCID in CSV file in row number {count+2}")
            message = f"Please enter valid URL and/or SCID in CSV file in row number {count+2}"
            save_output_to_file(message + "\n")

            
if __name__ == "__main__":
    main()