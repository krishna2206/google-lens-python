import re
import json
from typing import Any, Optional
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
        prerender_script: Optional[str] = None
        for script in soup.find_all('script'):
            if script.text is None or 'AF_initDataCallback(' not in script.text:
                continue
            key_match = re.search(r"key: 'ds:(\d+)'", script.text)
            if key_match and key_match.group(1) == "0":
                prerender_script = script.text
                break

        if prerender_script is None:
            raise ValueError("Unable to find Google Lens prerender data in response.")
        
        # Clean up the script content to prepare it for JSON parsing
        prerender_script = prerender_script.replace(
            "AF_initDataCallback(", "").replace(");", "")
        
        # Extract hash value and replace the corresponding fields in the script for JSON formatting
        hash_match = re.search(r"hash: '(\d+)'", prerender_script)
        if hash_match is None:
            raise ValueError("Unable to parse Google Lens prerender hash.")
        script_hash = hash_match.group(1)
        prerender_script = prerender_script.replace(
            f"key: 'ds:0', hash: '{script_hash}', data:",
            f"\"key\": \"ds:0\", \"hash\": \"{script_hash}\", \"data\":"
        ).replace("sideChannel:", "\"sideChannel\":")

        # Parse the cleaned prerender script into a JSON object
        prerender_script = json.loads(prerender_script)

        # Return the relevant data section for further processing
        return prerender_script['data'][1]

    @staticmethod
    def __safe_get(value: Any, path: list[int]) -> Any:
        current = value
        for index in path:
            if not isinstance(current, list) or not isinstance(index, int):
                return None
            if index < 0 or index >= len(current):
                return None
            current = current[index]
        return current

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
        match_title = self.__safe_get(prerender_script, [0, 1, 8, 12, 0, 0, 0])
        match_thumbnail = self.__safe_get(prerender_script, [0, 1, 8, 12, 0, 2, 0, 0])
        match_page_url = self.__safe_get(prerender_script, [0, 1, 8, 12, 0, 2, 0, 4])
        if isinstance(match_title, str) and isinstance(match_thumbnail, str) and isinstance(match_page_url, str):
            data["match"] = {
                "title": match_title,  # Extract item title
                "thumbnail": match_thumbnail,  # Extract thumbnail URL
                "pageURL": match_page_url  # Extract page URL
            }

        # Determine which section to use for extracting visual matches
        if data["match"] is not None:
            visual_matches = self.__safe_get(prerender_script, [1, 1, 8, 8, 0, 12])
        else:
            visual_matches = self.__safe_get(prerender_script, [0, 1, 8, 8, 0, 12])

        if not isinstance(visual_matches, list):
            return data

        # Iterate through the visual matches and extract relevant details
        for match in visual_matches:
            # Safely extract thumbnail URL if available
            thumbnail_url = self.__safe_get(match, [0, 0])
            if not isinstance(thumbnail_url, str):
                thumbnail_url = None

            # Safely extract price if available
            price = self.__safe_get(match, [0, 7, 1])
            if not isinstance(price, str):
                price = None

            # Clean price by removing any special characters (e.g., currency signs)
            price = re.sub(r"[^\d.]", "", price) if price is not None else None

            # Safely extract currency if available
            currency = self.__safe_get(match, [0, 7, 5])
            if not isinstance(currency, str):
                currency = None

            title = self.__safe_get(match, [3])
            similarity_score = self.__safe_get(match, [1])
            page_url = self.__safe_get(match, [5])
            source_website = self.__safe_get(match, [14])

            # Append the extracted information to the "similar" matches list
            data["similar"].append(
                {
                    "title": title,  # Extract item title
                    "similarity score": similarity_score,  # Extract similarity (?) score
                    "thumbnail": thumbnail_url,  # Thumbnail URL
                    "pageURL": page_url,  # Extract page URL
                    "sourceWebsite": source_website,  # Extract source website name
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
        with open(file_path, 'rb') as image_file:
            multipart = {
                'encoded_image': (file_path, image_file),
                'image_content': ''
            }

            # Build the parameter dictionary
            params = {
                "hl": "en",  # Adjust host language here
                "gl": "us",  # Adjust the geolocation parameter here
            }
            
            # Send a POST request to upload the file
            response = self.session.post(
                self.url + "/upload",
                files=multipart,
                params=params,
                allow_redirects=False,  # Must be false to capture the 302 response
                timeout=30
            )

        # Check if the request was successful
        if response.status_code != 302: # Expecting a 302 for redirect
            print(f"Error uploading file: Status code {response.status_code}")
            print(response.text)
            return None  # Or handle the error appropriately

        # Get the redirect URL from the 'Location' header
        search_url = response.headers.get('Location')

        # If redirect URL is not found, print an error and return
        if search_url is None:
            print("Redirect URL not found in response headers.")
            return None  # Or handle the error appropriately
        
        # Proceed with the redirect
        response = self.session.get(search_url, timeout=30)

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
        # Build the parameter dictionary
        params = {
            "url": url,
            "hl": "en",  # Adjust host language here
            "gl": "us",  # Adjust geolocation here
        }
        # Send a GET request to the provided URL
        response = self.session.get(
            self.url + "/uploadbyurl",
            params=params,
            allow_redirects=True,
            timeout=30
        )

        # Extract the prerendered JavaScript content for further parsing
        prerender_script = self.__get_prerender_script(response.text)

        # Parse the prerender script and return the processed search result
        return self.__parse_prerender_script(prerender_script)