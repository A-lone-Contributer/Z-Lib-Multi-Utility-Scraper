# Importing necessary libraries
import os
import random
import re
import csv
import time
import pyfiglet
import requests
from collections import OrderedDict
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, NavigableString, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ascii_banner = pyfiglet.figlet_format("Z-LIB BOOK SCRAPER")
print(ascii_banner)

# Join user agents file to the system path
user_agents_file = os.path.join(os.path.dirname(__file__), 'user_agents.txt')


# Utility function to get the user agent
def get_user_agent():
    """
    Load the User Agent File
    """
    user_agent = load_user_agents(uafile=user_agents_file)
    return user_agent


# Utility function to get random UserAgent from the file
def load_user_agents(uafile):
    """
    uafile : string
    path to text file of user agents, one per line
    """
    uas = []

    # read the user agent file and create a list
    with open(uafile, 'rb') as uaf:
        for ua in uaf.readlines():
            if ua:
                uas.append(ua.strip()[1:-1 - 1])

    # return a random user agent
    return random.choice(uas)


def usermenu():
    """
    User Input and Initial Retrieval
    """

    # Number of retries after URLError
    global bs
    retries = 3
    i = 0

    # query from user
    query = input("Enter your query (Book name, genre, etc) : ")

    # create a search URL
    url = "https://b-ok.asia/s/" + query

    # Fetching the url
    try:
        print("=" * 40)
        print("Fetching the details...")

        html = urlopen(Request(url, headers={
            "Connection": "close",
            "User-Agent": get_user_agent()}))
        bs = BeautifulSoup(html, 'html.parser')
    except HTTPError as e:
        print(e)
    except URLError:
        if i + 1 == retries:
            print('The server could not be found!')
        else:
            time.sleep(42)
    else:
        print("Details Fetched!")
        print("=" * 40)

    # getting the total count of results
    total_results = bs.find(class_='totalCounter')
    for number in total_results.descendants:
        file_total = number.replace("(", "").replace(")", "")
        if file_total == "500+":
            print(
                f'There are total of more than {file_total.replace("+", "")} search results for {query}')
        elif int(file_total) > 0:
            print(f"There are total {file_total} search results for {query}")
            print("-" * 40)
        else:
            print("No results!")

    # calling function for book link
    book_link_retrieval(bs)


# Utility function for Book Title Retrieval and Direct-link Parsing
def book_link_retrieval(soup_object):
    """
    bs : Soup object having parsed HTML for the user query
    """

    global sp, dir_link
    i, retries = 0, 3

    # fetching the title and book link
    for _ in soup_object.find_all("td"):
        for td in soup_object.find_all("h3"):
            for ts in td.find_all("a"):
                title = ts.get_text()

            for ts in td.find_all('a', attrs={'href': re.compile("^/book/")}):
                ref = ts.get('href')
                book_link = "https://b-ok.asia" + ref

            print("Title of the book: " + title + "\n")
            print("Book link: " + book_link)
            print("=" * 40)

            # Fetching name of the author
            data = requests.request('get', book_link)  # any website
            s = BeautifulSoup(data.text, 'html.parser')
            author = s.find('a', {'class': 'color1'}).get_text()

            # calling bookMetaData for fetching book details
            book_meta_data(book_link, title, author)


# Function to fetch book metadata and create excel file
def book_meta_data(book_link, book_title, author_name):
    """
    book_link: Direct link to the book
    book_title: Title of the book
    author_name: Name of the author
    """

    global soup
    i, retries = 0, 3

    # fetching the metadata for each of the books
    try:
        print("Fetching book metadata...")
        request = urlopen(
            Request(
                book_link, headers={
                    "Connection": "close",
                    "User-Agent": get_user_agent()})).read()
        soup = BeautifulSoup(request, 'html.parser')
    except HTTPError as e:
        print(e)
    except URLError:
        if i + 1 == retries:
            print('The server could not be found!')
        else:
            time.sleep(42)
    else:
        print("Metadata Fetched!")

    print("=" * 40)

    metadict = {}  # dictionary to hold the fetched details
    columns = [
        "Categories",
        "File",
        "ISBN",
        "Language",
        "Pages",
        "Publisher",
        "Year"]

    try:
        # fetch the book details by requesting direct link of books
        for child in soup.find('div', {'class': 'bookDetailsBox'}).children:

            # check if the parsed content (child) is NavigableString
            if isinstance(child, NavigableString):
                continue

            # check if the parsed content (child) is Tag
            if isinstance(child, Tag):
                # get the keys and values
                metadata = soup.find('div', {'class': child['class'][1]}).get_text().split()

                # create a dictionary
                metadict[metadata[0].replace(":", "")] = metadata[1]

    except AttributeError:
        print("No Children found!")

    # removing ISBN as it is not useful here
    if 'ISBN' in metadict.keys():
        del metadict['ISBN']
    if 'ISBN' in columns:
        columns.remove('ISBN')

    # sorting the dictionary by keys
    metadict = dict(sorted(metadict.items()))

    """
    logic to add NaN values
    """
    # check if the length of columns list and fetched data keys are same
    if len(columns) != len(metadict.keys()):

        # if not then find the columns which are not there
        not_present = set(columns) - set(metadict.keys())

        # added them to dictionary with None values
        for col in not_present:
            metadict[col] = 'NaN'

    # sort the data again for sanity
    metadict = OrderedDict(sorted(metadict.items()))

    # cleaning 'File' column
    metadict['File'] = metadict['File'].replace(",", "")

    # cleaning 'Categories' column
    if 'Categories' in metadict.keys():
        metadict['Categories'] = metadict['Categories'].replace("\\\\", ",")

    # adding author column to the front of the dictionary
    metadict = OrderedDict([('Author', author_name)] + list(metadict.items()))

    # adding title column to the front of the dictionary
    metadict = OrderedDict([('Title', book_title)] + list(metadict.items()))

    csv_file = "metadata.csv"  # name of the csv file

    print("Creating Excel File... Adding row...")

    # open the file in append mode and write the dictionary content
    try:
        with open(csv_file, 'a+', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=metadict.keys(), delimiter=',')
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(metadict)

    except IOError:
        print("I/O error")

    print("Row Added!")
    print("=" * 40)

    # call the download function
    download(book_link)


# Helper function to launch browser
def launch_browser(link):
    """
    link : Direct link to the book
    """
    
    chrome_options = Options()
    chrome_options.add_argument("start-maximized")
    driver = webdriver.Chrome(executable_path="chromedriver.exe", options=chrome_options)
    driver.get(link)

    return driver


# Function to download File and save to disk
def download(link):
    """
    link : Direct link to the book
    """

    confirmation = input("Do you want to download this book? (Y/N) ").lower()

    print("There is a download limit of 5, so if the file doesn't download then check your limit.")

    # if user inputs 'y' then download the file
    if confirmation == 'y':
        print("Downloading file....")
        driver = launch_browser(link)

        # clicking the download button
        driver.find_element_by_class_name("addDownloadedBook").click()

        # timer for chrome to download the file
        time.sleep(100)

        # close the driver
        driver.close()

        print("Downloaded!")


if __name__ == "__main__":
    usermenu()
