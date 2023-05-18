# Google Lens Python

Google Lens Python is a Python package that allows you to reverse image search on Google Lens using Python, with the ability to search by file path or by URL.

## Installation

You can install Google Lens Python using pip:

```sh
pip install git+https://github.com/krishna2206/google-lens-python.git
```

## Usage

To use Google Lens Python, import the `GoogleLens` class from the package and create an instance of it:

```python
from googlelens import GoogleLens

lens = GoogleLens()
```

### Searching by file

To search by a file path, use the `search_by_file` method and pass in the file path as a string:

```python
search_result = lens.search_by_file("path/to/image.jpg")
print(search_result)
```

This will return a dictionary containing the search results.

### Searching by URL

To search by a URL, use the `search_by_url` method and pass in the URL as a string:

```python
search_result = lens.search_by_url("https://example.com/image.jpg")
print(search_result)
```

This will return a dictionary containing the search results.

## Ideas

- Implement text detection (if possible)
- Implement translate feature (if possible)

## Contributing

Contributions to the Google Lens Python project are welcome! To contribute, please submit a pull request to the project's [GitHub repository](https://github.com/krishna2206/google-lens-python). 

## License

MIT License

#### Notice

This license applies only to the files in this repository authored by Anhy Krishna Fitiavana (the "Author"). Other files may be subject to additional or different licenses.

#### License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use,copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,subject to the following conditions: 

1. The above notice and this permission notice shall be included in all copies or substantial portions of the Software.

2. The Software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. 

3. In no event shall the Author be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the Software or the use or other dealings in the Software.