# Z-Lib-Multi-Utility-Scraper

## About Search Engine

ZLibrary.Asia is the biggest ebook library which has two main servers:
- b-ok.asia
- booksc.xyz

b-ok.asia can be used for downloading books based whereas booksc.xyz contains articles and research papers.

## About Scraper

This is a multiple utility scraper which can fetch the metadata of books in a csv file. Also, user can download the desired books in one click.
Note that, this scraper is just for b-ok.asia but it is very easy to switch to booksc.xyz by changing search url in the code.

## Outputs

### Metadata

The data fetched contains the following columns :
- Title
- Author
- Categories
- File (Format)
- Language
- Pages (Number of Pages)
- Publisher
- Year

### File

Book is downloaded based on user confirmation. For downloading, scraper uses selenium and opens browser to click the download link. We can avoid opening of browser using --headless option but as the books have a download limit thus this method is not preferrable.

**Note:** One book is uploaded for sample and not all the books - for obvious reasons.

## Requirements

- Python >=3.6 
- Selenium
- Chromedriver
- pyfiglet
- urllib
- requests
- bs4
