import re
import pandas as pd
# Selenium NEEDS to be installed with pip and not conda, otherwise geckodriver won't be recognized
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as OptFirefox
from selenium.webdriver.chrome.options import Options as OptChrome
from selenium.common.exceptions import WebDriverException
import time
import sys

def expand_shadow_element(driver, element):
    return driver.execute_script('return arguments[0].shadowRoot.children[0]', element)

def scrape_table():
    try:
        print("Checking Firefox...")
        optfirefox = OptFirefox()
        optfirefox.add_argument("--headless")
        driver = webdriver.Firefox(options=optfirefox)
        print("Found Firefox installation!")
    except WebDriverException:
        try:
            # Needs to have chromedriver_binary installed
            print("Firefox not found\nChecking Chrome...")
            optchrome = OptChrome()
            optchrome.add_argument("--headless")
            driver = webdriver.Chrome(options=optchrome)
            print("Found Chrome installation!")
        except WebDriverException:
            print("Chrome not found")
            print("ERROR: You must either have Firefox or Chrome installed to automatically update the calculator!")
            sys.exit(1)
    
    driver.implicitly_wait(10)
    driver.get("https://2e.aonprd.com/Equipment.aspx?sort=level-asc%2Cprice-asc%2Cname-asc&display=table&columns=rarity%2Citem_category%2Citem_subcategory%2Clevel%2Cprice%2Cbulk")

    shadow_parent = driver.find_element(By.CSS_SELECTOR, "#ctl00_RadDrawer1_Content_MainContent_DetailedOutput > nethys-search")
    shadow_root = expand_shadow_element(driver, shadow_parent)

    button_parent = shadow_root.find_element(By.CSS_SELECTOR, """div[class="row gap-medium"]""")
    load_button = button_parent.find_elements(By.CSS_SELECTOR, "button")[1]
    load_button.click()
    time.sleep(10)

    table = shadow_root.find_element(By.CSS_SELECTOR, "tbody")

    htmlcode = table.get_attribute("outerHTML")
    with open("aon_data/html_dump.htm", "w") as html:
        html.write(htmlcode)
    driver.quit()

def decipher_writing():
    with open("aon_data/html_dump.htm", "r") as data:
        content = data.read()
        content = re.sub(r"</?tbody>","", content)
        content = re.sub(r"</td>", "\n", content)
        content = re.sub(r"<[^<>]*>", "", content)
        content = re.sub(r",", "", content)
        content = re.sub(r" or —", " or 0", content)
        content = re.sub(r"è", "e", content)


    with open("temp.txt", "w") as tempfile:
        tempfile.write(content)
    with open("temp.txt", "r") as tempfile:
        filtered = tempfile.readlines()

    stripped: list[str] = []
    for line in filtered:
        stripped.append(line.strip())

    with open("aon_data/PF2eItemList.csv", "w") as itemlist:
        itemlist.write("Name,Rarity,Category,Subcategory,Level,Price,Bulk\n")
        
        curr_line = ""
        for i, property in enumerate(stripped):
            curr_line += property
            if i % 7 != 6:
                curr_line += ","
            else:
                curr_line += "\n"
                itemlist.write(curr_line)
                curr_line = ""

if __name__ == "__main__":
    scrape_table()
    decipher_writing()
    df = pd.read_csv("aon_data/PF2eItemList.csv")
    print(df.shape)
    print(df.head(10))