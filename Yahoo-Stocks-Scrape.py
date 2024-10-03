import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Gets the Entire Table
def getTable(url):

    soup = getSoup(url)
    pagination = soup.find('div', class_='select-dropdown yf-1tdhqb1')

    # When there is no Pagination!
    if pagination == None:
        dfFrame = getRows(soup)
        dfFrame.to_csv('Example-output.csv', index=False)
        
        return dfFrame

    # For 25+ rows of data!
    else:
        # Generates Soup from drivers html! 
        driver = getDriver(url)     
        soup = BeautifulSoup(driver.page_source, 'lxml')

        dfList = []

        # looping through modified URL for other sets of 25 rows of data
        while True:
            
            # Get current set of Rows & adds DataFrame to list!
            try:
                dfList.append(getRows(soup))

                # Getting the total rows & Starting Row in table
                total_pg = soup.find('div', class_='total yf-1tdhqb1').get_text()   #type: ignore
                pg_info = total_pg.split('of')

                total = int(pg_info[1])
                endRow = int(pg_info[0].split('-')[1])
            
            # The table extracted up until now will be saved, (In Case, loss of internet/PC/other problems) ! 
            except Exception as errorMSG:
                print("An Error Has Been Generated! \nPrinting the message: \n", errorMSG)
                
                # Within Exception the endRow < total will go to else statement!
                total = 45
                endRow = 50


            # Modifies URL to get next set of data/25-Rows
            if endRow < total:
                new_url = f'{url}?start={endRow}&count=25'
                print(new_url)

                driver.get(new_url)
                soup = BeautifulSoup(driver.page_source)
            
            # Combine DataFrames in list to generate CSV file, & Break the loop!
            else:
                dfCombined = pd.concat(dfList, ignore_index=True)
                dfCombined.to_csv('Example-output.csv', index=False)

                return dfCombined
        

# Returns the Soup!
def getSoup(url):
    request = requests.get(url)
    html = request.text
    soup = BeautifulSoup(html, 'lxml')

    return soup

# Returns a Soup from driver
def getDriver(url):

    # Setting Options to run Browser Without UI & disabling GPU for increased Performance!
    options = webdriver.EdgeOptions()
    options.add_argument("--headless")  
    # options.add_argument("--disable-gpu") 

    service = webdriver.EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)

    driver.get(url)
    
    return driver

# Returns a DataFrame
def getRows(soup):

    # Finds the table & Creates a list for rows
    table = soup.find('tbody')
    rows = table.find_all('tr') 

    # symbol, name, price, change, percentChange, Vol, avgVol, marketCap, PEratio, 52 Week Change %
    columns = [[] for i in range(10)]


    for r in rows:
        # Gets all the Cells per row
        cellData = r.find_all('td')
        
        # Retrieves text & appends them to the respective Columns
        for i in range(2, len(columns)):
            columns[i].append(cellData[i-1].get_text())

        # Symbol & Name are on same CellData[0]
        columns[0].append(cellData[0].find('span', class_='symbol yf-1jpysdn').get_text())
        columns[1].append(cellData[0].find('span', class_='yf-1jpysdn longName').get_text())


    columns[2] = [price.split(' ')[1] for price in columns[2]]      # This line removes Unneccessary data that appears for this column

    # Creates a 2D Dictionary with all these Columns
    tbColumns = ['Symbol', 'Name', 'Price', 'Change', '%Change', 'Volume', 
                 'AvgVolume', 'MarketCap', 'P/E Ratio (TTM)', '52 Wk Change %']
    tb_dict = {}

    for i, column in enumerate(tbColumns):
        tb_dict[column] = columns[i]

    dfFrame = pd.DataFrame(tb_dict)
    
    return dfFrame


if __name__ == '__main__':
    dataFrameTable = getTable('https://finance.yahoo.com/markets/stocks/52-week-gainers/')
    print(dataFrameTable)