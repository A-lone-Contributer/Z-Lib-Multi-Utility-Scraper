# Importing necessary libraries
import os
import random
import re
import csv
import time
import shutil
import pyfiglet
from collections import OrderedDict
from urllib.request import urlopen, Request, urlretrieve
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup, NavigableString, Tag

ascii_banner = pyfiglet.figlet_format("Z-LIB BOOK SCRAPER")
print(ascii_banner)

# Join user agents file to the system path
user_agents_file = os.path.join(os.path.dirname(__file__), 'user_agents.txt')

# Utlity function to get the user agent
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


def userMenu():
    """
    User Input and Initial Reterieval
    """

    # Number of retries after URLError
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
        html = urlopen(Request(url, headers={'User-Agent': get_user_agent()}))
        bs = BeautifulSoup(html, 'html.parser')
    except HTTPError as e:
        print(e)
    except URLError as e:
        if i + 1 == retries:
            print('The server could not be found!')
        else:
            time.sleep(42)
    else:
        print("Details Fetched!")
        print("=" * 40)

    # getting the total count of results
    totalResults = bs.find(class_='totalCounter')
    for number in totalResults.descendants:
        fileTotal = number.replace("(", "").replace(")", "")
        if fileTotal == "500+":
            print(
                f'There are total of more than {fileTotal.replace("+","")} search results for {query}')
        elif int(fileTotal) > 0:
            print(f"There are total {fileTotal} search results for {query}")
            print("-" * 40)
        else:
            print("No results!")

    # calling function for book link
    bookLinkRetrieval(bs)


# Utility function for Book Title Reterieval and Direct-link Parsing
def bookLinkRetrieval(bs):
    """
    bs : Soup object having parsed HTML for the user query
    """

    i = 0

    # fetching the title and book link
    for tr in bs.find_all("td"):
        for td in bs.find_all("h3"):
            for ts in td.find_all("a"):
                title = ts.get_text()

            for ts in td.find_all('a', attrs={'href': re.compile("^/book/")}):
                ref = ts.get('href')
                BookLink = "https://b-ok.asia" + ref

            print("Title of the book: " + title+"\n")
            print("Book link: " + BookLink)
            print("=" * 40)

            # request the book page link for fetching direct download link
            try:
                print("Fetching direct link to the book...")
                request = urlopen(
                    Request(
                        BookLink, headers={
                            'User-Agent': get_user_agent()})).read()
                soup = BeautifulSoup(request, 'html.parser')
            except HTTPError as e:
                print(e)
            except URLError as e:
                if i + 1 == retries:
                    print('The server could not be found!')
                else:
                    time.sleep(42)
            else:
                print("Link fetched!")

            # get the direct link to the book
            for link in soup.findAll('a', attrs={'href': re.compile("^/dl/")}):
                urlTrail = link.get('href')
                dirlink = "https://b-ok.asia" + urlTrail

            print(f"Direct Link: {dirlink}")

            # calling bookMetaData for fetching book details
            bookMetaData(dirlink, title)


# Function to fetch book metadata and create excel file
def bookMetaData(dirlink, title):
    """
    dirlink: Direct link to the book
    title: Title of the book
    """

    # fetching the metadata for each of the books
    try:
        print("=" * 40)
        print("Fetching book metadata...")
        request = urlopen(
            Request(
                dirlink, headers={
                    'User-Agent': get_user_agent()})).read()
        soup = BeautifulSoup(request, 'html.parser')
    except HTTPError as e:
        print(e)
    except URLError as e:
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

    # fetch the book details by requesting directlink of booko
    for child in soup.find('div', {'class': 'bookDetailsBox'}).children:

        # check if the parsed content (child) is NavigableString
        if isinstance(child, NavigableString):
            continue

        # check if the parsed content (child) is Tag
        if isinstance(child, Tag):

            # get the keys and values
            metadata = soup.find(
                'div', {
                    'class': child['class'][1]}).get_text().split()

            # create a dictionary
            metadict[metadata[0].replace(":", "")] = metadata[1]

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
    # check if the lenght of columns list and fetched data keys are same
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

    # adding title column to the front of the dictionary
    metadict = OrderedDict([('Title', title)] + list(metadict.items()))

    csv_file = "metadata.csv"  # name of the csv file

    print("Creating Excel File... Adding row...")

    # open the file in append mode and write the dictionary content
    try:
        with open(csv_file, 'a+') as csvfile:
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
    download(dirlink, title, metadict['File'].replace(",", ""))


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

    userMenu()
