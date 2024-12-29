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
            soup.find_all('script')
        ))[0].text
        
        # Clean up the script content to prepare it for JSON parsing
        prerender_script = prerender_script.replace(
            "AF_initDataCallback(", "").replace(");", "")
        
        # Extract hash value and replace the corresponding fields in the script for JSON formatting
        hash = re.search(r"hash: '(\d+)'", prerender_script).group(1)
        prerender_script = prerender_script.replace(
            f"key: 'ds:0', hash: '{hash}', data:",
            f"\"key\": \"ds:0\", \"hash\": \"{hash}\", \"data\":"
        ).replace("sideChannel:", "\"sideChannel\":")

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
                "title": prerender_script[0][1][8][12][0][0][0],  # Extract item title
                "thumbnail": prerender_script[0][1][8][12][0][2][0][0],  # Extract thumbnail URL
                "pageURL": prerender_script[0][1][8][12][0][2][0][4]  # Extract page URL
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
            # Safely extract thumbnail URL if available
            thumbnail_url = match[0][0] if (
                isinstance(match[0], list) and len(match[0]) > 0 and
                isinstance(match[0][0], str)
            ) else None

            # Safely extract price if available
            price = match[0][7][1] if (
                isinstance(match[0], list) and len(match[0]) > 7 and
                isinstance(match[0][7], list) and len(match[0][7]) > 1 and
                isinstance(match[0][7][1], str)
            ) else None

            # Clean price by removing any special characters (e.g., currency signs)
            price = re.sub(r"[^\d.]", "", price) if price is not None else None

            # Safely extract currency if available
            currency = match[0][7][5] if (
                isinstance(match[0], list) and len(match[0]) > 7 and
                isinstance(match[0][7], list) and len(match[0][7]) > 5 and
                isinstance(match[0][7][5], str)
            ) else None

            # Append the extracted information to the "similar" matches list
            data["similar"].append(
                {
                    "title": match[3],  # Extract item title
                    "similarity score": match[1],  # Extract similarity (?) score
                    "thumbnail": thumbnail_url,  # Thumbnail URL
                    "pageURL": match[5],  # Extract page URL
                    "sourceWebsite": match[14],  # Extract source website name
                    "price": price,  # Price (cleaned)
                    "currency": currency  # Currency symbol
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
        multipart = {
            'encoded_image': (file_path, open(file_path, 'rb')),
            'image_content': ''
        }
        
        # Send a POST request to upload the file
        response = self.session.post(
            self.url + "/upload",
            files=multipart,
            allow_redirects=False  # Must be false to capture the 302 response
        )

        # Check if the request was successful
        if response.status_code != 302: # Expecting a 302 for redirect
            print(f"Error uploading file: Status code {response.status_code}")
            print(response.text)
            return None

        # Get the redirect URL from the 'Location' header
        search_url = response.headers.get('Location')

        # If redirect URL is not found, print an error and return
        if search_url is None:
            print("Redirect URL not found in response headers.")
            return None
        
        # Proceed with the redirect
        response = self.session.get(search_url)

        # Extract the prerendered JavaScript content for further parsing.
        prerender_script = self.__get_prerender_script(response.text)

        # Parse the prerender script and return the processed search result.
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