import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv

from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Gets the Entire Table
def getTable(url):
    
    soup = getSoup(url)

    # Check for pagination existence
    pagination = soup.find('div', class_='select-dropdown yf-1tdhqb1')

    if pagination != None:
        
        dfList = []
        driver = getDriver(url)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        while True:
            
            dfList.append(getRows(soup))
            

            total_pg = soup.find('div', class_='total yf-1tdhqb1').get_text()   #type: ignore
            pg_info = total_pg.split('of')

            total = int(pg_info[1])
            endRow = int(pg_info[0].split('-')[1])

            if endRow >= total:

                dfCombined = pd.concat(dfList, ignore_index=True)
                dfCombined.to_csv('Example-output.csv', index=False)

                break

            new_url = f'{url}?start={endRow}&count=25'
            print(new_url)

            driver.get(new_url)

            soup = BeautifulSoup(driver.page_source)
        
        print(dfList)

    else:
        pdFrame = getRows(soup)
        pdFrame.to_csv('Example-output.csv', index=False)

# Returns a BS4 result element
def getSoup(url):
    request = requests.get(url)
    html = request.text
    soup = BeautifulSoup(html, 'lxml')

    return soup

# Returns a Soup from driver
def getDriver(url):
    options = webdriver.EdgeOptions()

    options.add_argument("--headless")  # Run in headless mode (no browser UI)
    options.add_argument("--disable-gpu")  # Disable GPU rendering for increased performance

    service = webdriver.EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)

    driver.get(url)
    
    return driver

# Returns a PandaFrame
def getRows(soup):

    # finds the table tag
    table = soup.find('tbody')
    rows = table.find_all('tr') 

    # symbol, name, price, change, percentChange, Vol, avgVol, marketCap, PEratio
    columns = [[] for i in range(10)]


    for cell in rows:
        data = cell.find_all('td')
        
        for i in range(2, len(columns)):
            columns[i].append(data[i-1].get_text())

        # adding symbol & name
        columns[0].append(data[0].find('span', class_='symbol yf-1jpysdn').get_text())
        columns[1].append(data[0].find('span', class_='yf-1jpysdn longName').get_text())

    columns[2] = [price.split(' ')[1] for price in columns[2]] 

    tbColumns = ['Symbol', 'Name', 'Price', 'Change', '%Change', 'Volume', 
                 'AvgVolume', 'MarketCap', 'P/E Ratio (TTM)', '52 Wk Change %']
    
    tb_dict = {}

    for i, column in enumerate(tbColumns):
        tb_dict[column] = columns[i]

    pdFrame = pd.DataFrame(tb_dict)
    
    return pdFrame




if __name__ == '__main__':
    getTable('https://finance.yahoo.com/markets/stocks/gainers/')