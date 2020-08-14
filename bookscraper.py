# Importing necessary libraries
import os
import random
import re
import csv
import time
import pyfiglet
from collections import OrderedDict
from urllib.request import urlopen, Request, urlretrieve
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, NavigableString, Tag

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

            # request the book page link for fetching direct download link
            try:
                print("Fetching direct link to the book...")
                request = urlopen(
                    Request(
                        book_link, headers={
                            "Connection": "close",
                            "User-Agent": get_user_agent()})).read()
                sp = BeautifulSoup(request, 'html.parser')
            except HTTPError as e:
                print(e)
            except URLError:
                if i + 1 == retries:
                    print('The server could not be found!')
                else:
                    time.sleep(42)
            else:
                print("Link fetched!")

            # get the direct link to the book
            for link in sp.findAll('a', attrs={'href': re.compile("^/dl/")}):
                url_trail = link.get('href')
                dir_link = "https://b-ok.asia" + url_trail

            print(f"Direct Link: {dir_link}")

            # calling bookMetaData for fetching book details
            book_meta_data(dir_link, title)


# Function to fetch book metadata and create excel file
def book_meta_data(direct_link, title):
    """
    direct_link: Direct link to the book
    title: Title of the book
    """

    global soup
    i, retries = 0, 3

    # fetching the metadata for each of the books
    try:
        print("=" * 40)
        print("Fetching book metadata...")
        request = urlopen(
            Request(
                direct_link, headers={
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
    if metadict['Categories']:
        metadict['Categories'] = metadict['Categories'].replace("\\", ",")

    # adding title column to the front of the dictionary
    metadict = OrderedDict([('Title', title)] + list(metadict.items()))

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
    download(direct_link, title, metadict['File'].replace(",", ""))


# Function to download File and Save to Disk
def download(link, title, extension):
    """
    link : Direct link to the book
    title : Title of the book
    extension : extension of the file (epub/pdf etc)
    """

    confirmation = input("Do you want to download this book? (Y/N) ").lower()

    # if user inputs 'y' then download the file
    if confirmation == 'y':
        output_file = title + "." + extension.lower()
        urlretrieve(link, output_file)
        print("Book Download Complete!")


if __name__ == "__main__":
    usermenu()
