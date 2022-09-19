# OSRS_Investment_Project
Scrapes and analyzes data from Old School Runescape items to make investment predictions


Summary:

Old School Runescape (osrs) is a medieval themed online game that launched in
2013. It hosts millions of users, and has a complex marketplace where items 
are bought and sold for in-game currency. The marketplace is named the 
Grand Exchange, and it automates trades for almost 4000 individual game items.
Luckily for us, there are websites that track data from these marketplace 
transactions. 

The goal of this project is to extract historical marketplace
information on each item in the game, then perform investment analysis on
that data. I will do this for free by utilizing open source softwares (Airflow,
Python) in conjunction with softwares under the Amazon Web Services (AWS) Free Tier
(EC2, S3, Redshift, EventBridge).

Some code to help you get a similar project up and running is included
in the Getting_Started file. It includes the link for getting started 
with Airflow and basic instructions for setting up an EC2 instance for
web scraping. 


Architecture:





Architecture Summary: 

Airflow is run on a local machine. Airflow schedules an extract/load 
script to run on an EC2 instance, which then uploads to a raw data staging zone in 
S3. SQL queries have been pre-scheduled via AWS EventBridge and data is 
automatically loaded and transformed in AWS Redshift. The final output of 
the analytical queries is sent out via email. 

 

Task Flow: 

Task 1: Start EC2 instance if it is not started already

Task 2: Connect to EC2 via SSH and run command to run extract/load script

Task 3: Wait, give time for queries scheduled via Eventbridge to complete

Task 4: Connect to EC2 via SSH and run command to run output script (send emails)

*Task 5: Stop EC2 instance

*Optional but not implemented due to Elastic IP Free Tier constraint

 

Considerations: 

The main considerations when building this project were scalability
and cost. Scheduling, Extraction/Loading, and Transformation 
responsibilities are separated between the local machine, EC2 instances,
and pre-scheduled queries on Redshift. Combining this with an ELT design
creates a pipeline that is scalable in its current state for more complex
analysis, and also allows for future integration of new data sources.
Using object storage for staging and a columnar database for large 
batch analysis maximizes efficiency when using these resources, 
which in turn minimizes cost.





Extraction / Loading:

These are the two websites that data is extracted from:

https://prices.runescape.wiki/osrs/all-items  (1)

https://secure.runescape.com/m=itemdb_oldschool  (2)


Unfortunately, there is no free website that features a complete item list 
as well as historical data for each item. So in this case, the complete
item list is extracted from the wiki database (1), and each item is individually
searched in the Runescape item database (2) to access its historical data. 

Example of wiki database that contains complete item list

-pic

Example of one item's historical data on the Runescape item database

-pic

The historical data is in graph form, so the extraction script download the 
graph's source code and parses it for data.


The extraction script writes raw data incrementally to a local csv file. When
extraction is complete, the csv file is uploaded to an S3 bucket. 

-raw data pic





Transformation:


The csv file upload to S3 triggers an EventBridge rule that loads the csv file 
from S3 to Redshift, then performs a series of analytical queries. 


EventBridge Rule Trigger
-eventbridge pic

EventBridge Rule Target 
-eventbridge pic


Below is a walthrough of my investment analysis. In general, this is just an 
attempt to use historical data to weigh today's investment opportunites.



-data_tb pic
This cleaned data table is the first layer of analysis on the raw data.
The data table contains data on many attributes of each item, such as:
    price has risen for past two days T/F
    price has risen for past three days T/F 
    daily volume has increased for past two days T/F
    daily volume has increased for past three days T/F
    % price increase in past day
    % price increase from 3 days ago
    % price increase from 1 week ago



-data summary pic
The data summary table is the second layer of analysis. Data from the cleaned
data table is aggregated to see if there are any insights that can be drawn.


-final output pic
Aggregated data from the data summary table is applied to the original item
list and prices, creating a final item list with recent prices increases
adjusted based on historical data. 






Future Considerations

1. The Selenium package is used to scrape web data, but it is not very efficient.
Future versions will use Scrapy, allowing parallel execution for web scrapes.

2. AWS EventBridge is very simple and easy to get up and running,
but has very limited Transformation capabilities beyond scheduling queries. 
I hope to incorporate a more comprehensive Transformation software 
such as Data Build Tool (DBT). DBT offers the benefits of better structure,
testing, and documentation in the Transformation phase. This would allow more 
complex analysis, which I believe is necessary.

3. Redshift clusters need to be running for queries to be performed. This 
project records daily data, so the cluster must be running 24/7 or on a 
scheduled daily interval. This is not a problem with the Redshift Free Tier, 
but that only last two months. I believe an easy way to 
address this would be to run the cluster on a small daily scheduled interval, 
and use an associated CloudTrail to trigger the EventBridge rule instead of S3.
