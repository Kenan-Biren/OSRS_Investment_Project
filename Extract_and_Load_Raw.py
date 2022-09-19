from selenium import webdriver
import selenium.webdriver.common.by
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime
import csv
import os
import boto3
import botocore.client
import logging



options = Options()
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
#chrome_options.add_argument("--user-agent=Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                          options=chrome_options)

                          

def get_all_items():
    cur_pg = 1
    no_pg = 74
    item_list = []
    buylimit_list = []
    dailyvol_list = []

    driver.get('https://prices.runescape.wiki/osrs/all-items/')


    while cur_pg <= no_pg:      ## Extract full item list with associated buy 
        try:                    ## limits and most recent daily volume 
            cur_pg = cur_pg + 1
            time.sleep(3)
            names = driver.find_elements(by="css selector", value='td:nth-child(2) a')
            for n in names:
                text = n.text
                if '(tablet)' in text:
                    text = text.replace(' (tablet)', '', 1)
                item_list.append(text)

            buylimit = driver.find_elements(by="css selector", value='td:nth-child(3)')
            for b in buylimit:
                b1 = b.text.replace(',', '')
                if b1 != '':
                    if b1 == 'Unknown':
                        buylimit_list.append(int(1))
                    else:
                        buylimit_list.append(int(b1))

            dailyvol = driver.find_elements(by="css selector", value='td:nth-child(10)')
            for d in dailyvol:
                d1 = d.text.replace(',', '')
                if d1 != 'Unknown':
                    dailyvol_list.append(int(d1))
                else:
                    dailyvol_list.append(int(0))

            next_url = driver.find_element(by="css selector", value='.btn-secondary:nth-child(3)')
            next_url.click()            ## Click next page
        except:
            break



    # Code to only inlcude items where daily volume is not greater than 10x buy limit 

    # for i in range(len(item_list)):
    #     if daily_vol_list[i] > 10 * buylimit_list[i]:
    #         final_item_list.append(item_list[i])
    #         final_dailyvol_list.append(dailyvol_list[i])
    #         final_buylimit_list.append(buylimit_list[i])





    return [item_list, dailyvol_list, buylimit_list]



def get_link(name):  ##Use item name to get link to price data on osrs website. Returns link as string
    time.sleep(5)
    driver.get('https://secure.runescape.com/m=itemdb_oldschool/')
    text_area = driver.find_element(by="id", value='item-search')
    text_area.send_keys(name)
    text_area.send_keys(selenium.webdriver.Keys.ENTER)
    results = driver.find_elements(by="css selector", value='.table-item-link')
    link = ''
    for r in results:
        if r.get_attribute('title') == name:
            link = r.get_attribute('href')
    if link == '':
        return None
    return link






def record_hist_data(link, name, buylimit, position):  ## Uses link from get_link function to extract historical price
    price_list = []                                    ## and volume data
    volume_list = []
    ind = 0
    time.sleep(3)    
    driver.get(link)

    raw_file = driver.find_element(by="xpath", value='//*[@id="grandexchange"]/div/div/main/div[2]/script')
    contents = raw_file.get_attribute('innerHTML')          
    all_lines = contents.splitlines()  

    current_date = datetime.date.today()                    ## Get date two weeks ago
    curr_str = current_date.strftime('%Y/%m/%d')            
    past_date = current_date - datetime.timedelta(days=14) 
    past_str = past_date.strftime('%Y/%m/%d')
    yest_date = current_date - datetime.timedelta(days=1)
    yest_str = yest_date.strftime('%Y/%m/%d')
    #curr_str = yest_str  ## COMMENT OUT THIS LINE IN PRODUCTION, ALLOWS FOR
                          ## TESTING WHEN OSRS WEBSITE DATA ISN'T UPDATED




    for line in all_lines:
        if past_str in line:                           ## Use past date to find starting index for parsing
            ind = all_lines.index(line)
            break
 

    while curr_str not in all_lines[ind-1]:

            line_text = all_lines[ind]                 ## Extract price data
            split = line_text.split(", ")
            price = ''.join(filter(str.isdigit, split[1]))
            price_list.append(int(price))
            ind = ind + 1

            line_text = all_lines[ind]                 ## Extract volume data
            split = line_text.split(", ")
            volume = ''.join(filter(str.isdigit, split[1]))
            volume_list.append(int(volume))

        ind = ind + 1

    new_row = [name, buylimit]

    for v in range(len(volume_list)):
        new_row.append(volume_list[v])
    for p in range(len(price_list)):
        new_row.append(price_list[p])

    with open('/home/ec2-user/PROJECTFOLDER/raw_hist.csv', 'a+', newline='') as f:
        writer = csv.writer(f)
        f.seek(position)
        writer.writerow(new_row)                    ## Write row to csv file, record position of cursor
        pos = f.tell()                              ## (use cursor position as start for next row)
        f.close()
    return pos





def record_todays_data(link, name, position):  ## Uses link from get_link function to extract only today's
    ind = 0                                    ## price and volume data
    time.sleep(3)     
    driver.get(link)

    raw_file = driver.find_element(by="xpath", value='//*[@id="grandexchange"]/div/div/main/div[2]/script')
    contents = raw_file.get_attribute('innerHTML')
    all_lines = contents.splitlines()  

    current_date = datetime.date.today()
    curr_str = current_date.strftime('%Y/%m/%d')
    yest_date = current_date - datetime.timedelta(days=1)
    yest_str = yest_date.strftime('%Y/%m/%d')
    #curr_str = yest_str  ## COMMENT OUT THIS LINE IN PRODUCTION, ALLOWS FOR
                          ## TESTING WHEN OSRS WEBSITE DATA ISN'T UPDATED 
  

 
    for line in all_lines:
        if curr_str in line:
            ind = all_lines.index(line)
            break


    line_text = all_lines[ind]
    split = line_text.split(", ")
    price = ''.join(filter(str.isdigit, split[1]))

    ind = ind + 1
    line_text = all_lines[ind]
    split = line_text.split(", ")
    volume = ''.join(filter(str.isdigit, split[1]))

    new_row = [name, price, volume]


    with open('/home/ec2-user/PROJECTFOLDER/raw_today.csv', 'a+', newline='') as f:
        writer = csv.writer(f)
        f.seek(position)
        writer.writerow(new_row)                    ## Write row to csv file, record position of cursor
        pos = f.tell()                              ## (use cursor position as start for next row)
        f.close()
    return pos









def upload_file(file_name, bucket, object_name=None):     ## Taken from Boto3 documentation
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except botocore.client.ClientError as e:
        logging.error(e)
        return False
    return True


## Get full item list
final_lists = get_all_items()

## Check contents of historical data staging bucket
s3 = boto3.client('s3')                             
objects = s3.list_objects_v2(Bucket='osrs-grand-exchange-hist-staging')
keycount = objects["KeyCount"] 

## If historical data has not already been recorded,
## extract historical data and upload to S3
if objects["KeyCount"] == 0:            
    with open('/home/ec2-user/PROJECTFOLDER/raw_hist.csv', 'a+', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'buy_limit', 'dv_14', 'dv_13', 'dv_12',
                         'dv_11', 'dv_10', 'dv_9', 'dv_8', 'dv_7', 'dv_6', 'dv_5',
                         'dv_4', 'dv_3', 'dv_2', 'dv_1', 'daily_vol_today',
                         'p_14', 'p_13', 'p_12', 'p_11', 'p_10', 'p_9', 'p_8', 'p_7',
                         'p_6', 'p_5', 'p_4', 'p_3', 'p_2', 'p_1', 'price_today'])
        position = f.tell()
        f.close()

    for i in range(len(final_lists[0])):
        link = get_link(final_lists[0][i])
        if link is None:
            continue

        # Final dailyvol (dv) list is not used here because record_hist_data
        # will record dv data

        pos = record_hist_data(link, final_lists[0][i], final_lists[2][i], position)
        position = pos

    s3 = boto3.client('s3')
    with open("/home/ec2-user/PROJECTFOLDER/raw_hist.csv", "rb") as f:
        s3.upload_fileobj(f, "osrs-grand-exchange-hist-staging", "raw_hist_csv")


## If historical data has already been extracted, extract today's data and upload to S3
else:
    with open('/home/ec2-user/PROJECTFOLDER/raw_today.csv', 'a+', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'price', 'volume'])
            position = f.tell()
            f.close()

    for i in range(len(final_lists[0])):
        link = get_link(final_lists[0][i])
        if link is None:
            continue


        pos = record_todays_data(link, final_lists[0][i], position)
        position = pos

    s3 = boto3.client('s3')
    with open("/home/ec2-user/PROJECTFOLDER/raw_today.csv", "rb") as f:
        s3.upload_fileobj(f, "osrs-grand-exchange-todays-staging", "raw_todays_csv")
