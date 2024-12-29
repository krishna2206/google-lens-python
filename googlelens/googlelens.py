import re
import json
from requests import Session
from bs4 import BeautifulSoup

class GoogleLens:
    def __init__(self):
        """
        Initialize the GoogleLens object.

        Sets up base URL and session with appropriate headers for making requests to Google Lens.
        """
        self.url = "https://lens.google.com"
        self.session = Session()
        
        # Update session headers to mimic a standard browser user-agent
        self.session.headers.update(
            {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0'}
        )


    def __get_prerender_script(self, page: str):
        """
        Extracts the relevant prerendered JavaScript data from the HTML page.

        Parameters:
        page (str): The HTML page content as a string.

        Returns:
        dict: The extracted and parsed JSON data structure from the prerendered script.
        """
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(page, 'html.parser')

        # Find the script containing 'AF_initDataCallback' with specific key and hash values
        prerender_script = list(filter(
            lambda s: (
                'AF_initDataCallback(' in s.text and
                re.search(r"key: 'ds:(\d+)'", s.text).group(1) == "0"),
            soup.find_all('script')))[0].text
        
        # Clean up the script content to prepare it for JSON parsing
        prerender_script = prerender_script.replace(
            "AF_initDataCallback(", "").replace(");", "")
        
        # Extract hash value and replace the corresponding fields in the script for JSON formatting
        hash = re.search(r"hash: '(\d+)'", prerender_script).group(1)
        prerender_script = prerender_script.replace(
            f"key: 'ds:0', hash: '{hash}', data:",
            f"\"key\": \"ds:0\", \"hash\": \"{hash}\", \"data\":").replace("sideChannel:", "\"sideChannel\":")

        # Parse the cleaned prerender script into a JSON object
        prerender_script = json.loads(prerender_script)

        # Return the relevant data section for further processing
        return prerender_script['data'][1]

    def __parse_prerender_script(self, prerender_script):
        """
        Parses the prerendered script to extract match and similar items.

        Parameters:
        prerender_script (dict): The parsed JSON data from the prerender script.

        Returns:
        dict: A dictionary containing the main match and visually similar matches.
        """
        # Initialize the result dictionary
        data = {
            "match": None,
            "similar": []
        }
        
        # Extract the best match information if available
        try:
            data["match"] = {
                "title": prerender_script[0][1][8][12][0][0][0],
                "thumbnail": prerender_script[0][1][8][12][0][2][0][0],
                "pageURL": prerender_script[0][1][8][12][0][2][0][4]
            }
        except IndexError:
            # If data is unavailable, continue without a match
            pass
        
        # Determine which section to use for extracting visual matches
        if data["match"] is not None:
            visual_matches = prerender_script[1][1][8][8][0][12]
        else:
            try:
                visual_matches = prerender_script[0][1][8][8][0][12]
            except IndexError:
                return data

        # Iterate through the visual matches and extract relevant details
        for match in visual_matches:
            # Append the extracted information to the "similar" matches list
            data["similar"].append(
                {
                    "title": match[3],
                    "thumbnail": match[0][0],
                    "pageURL": match[5],
                    "sourceWebsite": match[14]
                }
            )

        # Return the results dictionary
        return data

    def search_by_file(self, file_path: str):
        """
        Perform an image-based search by uploading a file.

        Parameters:
        file_path (str): The path to the image file that will be used for the search.

        Returns:
        The parsed search results after extracting and processing the response.
        """
        multipart = {'encoded_image': (file_path, open(file_path, 'rb')), 'image_content': ''}
        
        # Send a POST request to upload the file
        response = self.session.post(self.url + "/upload", files=multipart, allow_redirects=False)
        
        # Get the object containing the search URL from the response
        search_url = BeautifulSoup(
            response.text,
            'html.parser').find('meta', {'http-equiv': 'refresh'}).get('content')
        
        # Extract the search URL
        search_url = re.sub("^.*URL='", '', search_url).replace("0; URL=", "")

        # Send a GET request to the search URL
        response = self.session.get(search_url)
        
        # Extract the prerendered JavaScript content for further parsing
        prerender_script = self.__get_prerender_script(response.text)

        # Parse the prerender script and return the processed search result
        return self.__parse_prerender_script(prerender_script)
        
    def search_by_url(self, url: str):
        """
        Perform an image-based search by providing an image URL.

        Parameters:
        url (str): The URL of the image that will be used for the search.

        Returns:
        The parsed search results after extracting and processing the response.
        """
        # Send a GET request to the provided URL
        response = self.session.get(self.url + "/uploadbyurl", params={"url": url}, allow_redirects=True)

        # Extract the prerendered JavaScript content for further parsing
        prerender_script = self.__get_prerender_script(response.text)

        # Parse the prerender script and return the processed search result
        return self.__parse_prerender_script(prerender_script)