from tkinter import *
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tkcalendar import Calendar, DateEntry
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.common.keys import Keys
import pandas as pd
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

departure_date_entry = None
return_date_entry = None
from_entry = None
to_entry = None
email_entry = None
root = Tk()

# main search function
def get_flight_details(from_city, to_city):
    # Chrome set up
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://expedia.com")

    # click on flight
    flight_xpath = '//*[@id="multi-product-search-form-1"]/div/div/div[1]/ul/li[2]/a'
    driver.find_element(By.XPATH, flight_xpath).click()
    time.sleep(1)

    # leaving from
    driver.find_element(By.XPATH, '//button[@aria-label="Leaving from"]').click()
    time.sleep(1)
    input = driver.find_element(By.XPATH, '//*[@id="origin_select"]')
    input.send_keys(from_city)
    time.sleep(2) 
    input.send_keys(Keys.RETURN)

    # going to
    driver.find_element(By.XPATH, '//button[@aria-label="Going to"]').click()
    time.sleep(1)
    input = driver.find_element(By.XPATH, '//*[@id="destination_select"]')
    input.send_keys(to_city)
    time.sleep(1) 
    input.send_keys(Keys.RETURN)

    # need debugging for select dates in the future step, XPATH is not working for now
    # #choosing the departure date
    # departing_box_xpath = '//*[@id="FlightSearchForm_ROUND_TRIP"]/div/div[2]/div/div/div'
    # depart_box_element = driver.find_element(By.XPATH, departing_box_xpath)
    # depart_box_element.click() #Click on departure box
    # time.sleep(2)

    # #Find the current date. (WILL arrow to it)
    # trip_date_xpath = '//button[@aria-label="{}")]'.format(trip_date)
    # return_trip_date_xpath = '//button[contains(@class,"uitk-date-picker-day") and (@aria-label,"{}")]'.format(return_trip_date)
    # departing_date_element = ""
    # return_date_element = ""

    # #loops until finds the departure date
    # while departing_date_element == "":
    #     try:
    #         departing_date_element = driver.find_element(By.XPATH, trip_date_xpath)
    #         departing_date_element.click() #Click on the departure date
    #     except TimeoutException:
    #         departing_date_element=""
    #         next_month_xpath = '//button[@data-stid="date-picker-paging"][2]'
    #         driver.find_element(By.XPATH, next_month_xpath).click()
    #         time.sleep(1)

    # #loops until finds the return date
    # while return_date_element == "":
    #     try:
    #         return_date_element = driver.find_element(By.XPATH, return_trip_date_xpath)
    #         return_date_element.click() #Click on return date
            
    #     except TimeoutException: 
    #         departing_date_element = ""
    #         next_month_xpath = '//button[@data-stid="date-picker-paging"][2]'
    #         next_month_element = driver.find_element(By.XPATH, next_month_xpath)
    #         next_month_element.click()#Click on next month
    #         time.sleep(1)

    # # click Done
    # depart_date_done_xpath = '//button[@data-stid="apply-date-picker"]'
    # depart_date_done_element = driver.find_element(By.XPATH, depart_date_done_xpath)
    # depart_date_done_element.click()

    # click search 
    driver.find_element(By.XPATH,'//*[@id="search_button"]').click()
    time.sleep(15)

    # Looking for the search result if there are flights available, and select the top 5 cheap flight
    available_flights = driver.find_elements(By.XPATH, "//span[contains(text(),'Select and show fare information ')]")
    if len(available_flights) >  0:
        flights = [(item.text.split(",")[0].split('for')[-1].title(),
                    item.text.split(",")[1].title().replace("At",":"),
                    item.text.split(",")[2].title().replace("At",":"),
                    item.text.split(",")[3].title().replace("At",":")) for item in available_flights[0:5]]

        print(flights)
        driver.quit()
    else:
        print("No flight was founded")

    return flights


def select_departure_date():
    def set_departure_date():
        selected_date = cal.selection_get()
        departure_date_entry.delete(0, END)
        departure_date_entry.insert(0, selected_date.strftime('%Y-%m-%d'))
        top.destroy()

    top = Toplevel(root)
    cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack()
    confirm_button = Button(top, text="Select Departure Date", command=set_departure_date)
    confirm_button.pack()


def select_return_date():
    def set_return_date():
        selected_date = cal.selection_get()
        return_date_entry.delete(0, END)
        return_date_entry.insert(0, selected_date.strftime('%Y-%m-%d'))
        top.destroy()

    top = Toplevel(root)
    cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack()
    confirm_button = Button(top, text="Select Return Date", command=set_return_date)
    confirm_button.pack()


def send_email(flights_data):
    df = pd.DataFrame(flights_data, columns=["Airline", "Departure", "Arrival", "Price"])

# send the email if df was not empty
    if not df.empty: 
        # Create the email
        msg = MIMEMultipart("alternative")
        msg['Subject'] = "Cheap flight info: Departing: {}, Arrival: {}".format(from_entry.get(), to_entry.get())
        msg['From'] = 'email'
        msg['To'] = 'email'

        # Convert the DataFrame to HTML
        html = df.to_html()

        # Attach the HTML to the email
        msg.attach(MIMEText(html, 'html'))

        # Create secure connection with server and send email
        context = ssl.create_default_context()

        try:
            server = smtplib.SMTP('smtp.gmail.com',587)
            server.ehlo() # Can be omitted
            server.starttls(context=context) # Secure the connection
            server.ehlo() # Can be omitted
            # https://stackoverflow.com/questions/16512592/login-credentials-not-working-with-gmail-smtp
            server.login('email', 'pw')
            server.sendmail('email','email',msg.as_string())
        except Exception as e:
            # Print any error messages to stdout
            print(e)
        finally:
            server.quit() 
    

def search_flights():
    from_city = from_entry.get()
    to_city = to_entry.get()
    try:
        flights_data = get_flight_details(from_city, to_city)
        send_email(flights_data)
        messagebox.showinfo('Success', 'Flight details has been sent to your email!')
    except Exception as e:
        messagebox.showerror('Error', str(e))



root.title('Flight Search')
root.geometry('400x250')

# Labels
from_label = Label(root, text='Leaving From:')
from_label.grid(row=0, column=0, padx=10, pady=10)
to_label = Label(root, text='Going To:')
to_label.grid(row=1, column=0, padx=10, pady=10)
departure_label = Label(root, text='Departure Date:')
departure_label.grid(row=2, column=0, padx=10, pady=10)
return_label = Label(root, text='Return Date:')
return_label.grid(row=3, column=0, padx=10, pady=10)
email_label = Label(root, text='Email:')
email_label.grid(row=4, column=0, padx=10, pady=10)

# Entry fields
from_entry = Entry(root)
from_entry.grid(row=0, column=1, padx=10, pady=10)
to_entry = Entry(root)
to_entry.grid(row=1, column=1, padx=10, pady=10)

email_entry = Entry(root)
email_entry.grid(row=4, column=1, padx=10, pady=10)

departure_date_entry = Entry(root)
departure_date_entry.grid(row=2, column=1, padx=10, pady=10)
departure_date_button = Button(root, text="Select", command=select_departure_date)
departure_date_button.grid(row=2, column=2, padx=5, pady=10)

return_date_entry = Entry(root)
return_date_entry.grid(row=3, column=1, padx=10, pady=10)
return_date_button = Button(root, text="Select", command=select_return_date)
return_date_button.grid(row=3, column=2, padx=5, pady=10)

# Button
search_button = Button(root, text='Search Flights', command=search_flights)
search_button.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()