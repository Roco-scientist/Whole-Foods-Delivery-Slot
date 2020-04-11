import argparse
import os
import time
import os

import bs4
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from twilio.rest import Client


def arguments():
    """
    Arguments for the script
    """
    parser = argparse\
        .ArgumentParser(description="Pings Amazon Prime Whole Foods for open delivery slots")
    parser.add_argument("-b", dest="browser", type=str, default="chrome",
                        choices=("firefox", "chrome"), help="browser type [default: chrome]")
    parser.add_argument("-a", dest="autocheckout", action="store_true",
                        help="Use autocheckout with chrome")
    parser.add_argument("-t", dest="send_text", action="store_true",
                        help="Send a text using information from info.csv")
    parser.add_argument("-f", dest="amazon_fresh", action="store_true",
                        help="use amazon fresh instead of prime now")
    return parser.parse_args()


def send_text(message: str) -> None:
    """
    Uses twilio to send a text message

    Setup an account with twilio.  An additional file is created called info.csv in the same
    directory.  Have 4 columns, column name doesn't matter, but the first row content is your
    account sid, authorization token, your number to text to and setup with the account, and
    the from number created by twilio.

    :message: the message sent as a text
    :return: No return
    """
    if not os.path.isfile("info.csv"):
        raise RuntimeError("Unable to send text\n\
                info.csv does not exist\n\
                create comma sepparated info.csv file with 4 columns\n\
                Column_1 containing twilio account sid\n\
                Column_2 containing authorization token\n\
                Column_3 containing your personal number to text to\n\
                Column_4 containing the from number created within twilio")
    with open("info.csv", "r") as info_file:
        info_file.readline()  # remove the column headers and go to row 1
        account_sid, auth_token, to_num, from_num = info_file.readline().split(",")  # split values by comma

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        to=to_num,
        from_=from_num
    )


def windows_beep():
    import winsound
    duration = 1000
    freq = 440
    winsound.Beep(freq, duration)


def autoCheckout(driver):
    driver = driver

    time.sleep(1)
    try:
        slot_select_button = driver.find_element_by_xpath(
            '/html/body/div[5]/div[1]/div/div[2]/div/div/div/div/div[1]/div[4]/div[2]/div/div[3]/div/div/ul/li/span/span/div/div[2]/span/span/button')
        slot_select_button.click()
        print("Clicked open slot")
    except NoSuchElementException:
        slot_select_button = driver.find_element_by_xpath(
            '/html/body/div[5]/div[1]/div/div[2]/div/div/div/div/div[1]/div[4]/div[2]/div/div[4]/div/div/ul/li/span/span/div/div[2]/span/span/button')
        slot_select_button.click()

    slot_continue_button = driver.find_element_by_xpath(
        '/html/body/div[5]/div[1]/div/div[2]/div/div/div/div/div[2]/div[3]/div/span/span/span/input')
    slot_continue_button.click()
    print("Selected slot and continued to next page")

    try:
        time.sleep(6)
        outofstock_select_continue = driver.find_element_by_xpath(
            '/html/body/div[5]/div/form/div[25]/div/div/span/span/input')
        outofstock_select_continue.click()
        print("Passed out of stock")
    except NoSuchElementException:
        pass

    try:
        time.sleep(6)
        payment_select_continue = driver.find_element_by_xpath(
            '/html/body/div[5]/div[1]/div[2]/div[2]/div[4]/div/form/div[3]/div[1]/div[2]/div/div/div/div[1]/span/span/input')
        payment_select_continue.click()
        print("Payment method selected")

        time.sleep(6)
        try:
            review_select_continue = driver.find_element_by_xpath(
                '/html/body/div[5]/div[1]/div[2]/form/div/div/div/div[2]/div/div[1]/div/div[1]/div/span/span/input')
            review_select_continue.click()
            print("Order reviewed")
        except NoSuchElementException:
            review_select_continue = driver.find_element_by_xpath(
                '/html/body/div[5]/div[1]/div[2]/form/div/div/div/div[2]/div[2]/div/div[1]/span/span/input')
            review_select_continue.click()
            print("Order reviewed")

        print("Order Placed!")
        os.system('say "Order Placed!"')
    except NoSuchElementException:
        print("Found a slot but it got taken, run script again.")
        os.system('say "Found a slot but it got taken, run script again."')
        time.sleep(1400)


def prime_now(driver, soup):
    no_open_slots = True
    slot_patterns = ['Next available', '1-hour delivery windows', '2-hour delivery windows']
    try:
        next_slot_text = soup.find(
            'h4', class_='ufss-slotgroup-heading-text a-text-normal').text
        if any(next_slot_text in slot_pattern for slot_pattern in slot_patterns):
            if ARGS.send_text:
                send_text("Whole foods 1 slot open")
            print('SLOTS OPEN 1!')
            os.system('say "Slots for delivery opened!"')
            no_open_slots = False
            time.sleep(1400)
            if os.name == "nt":
                windows_beep()
            if ARGS.autocheckout:
                autoCheckout(driver)
    except AttributeError:
        pass

    try:
        slot_opened_text = "Not available"
        all_dates = soup.findAll("div", {"class": "ufss-date-select-toggle-text-availability"})
        for each_date in all_dates:
            if slot_opened_text not in each_date.text:
                if ARGS.send_text:
                    send_text("Whole foods 2 slot open")
                print('SLOTS OPEN 2!')
                os.system('say "Slots for delivery opened!"')
                no_open_slots = False
                if os.name == "nt":
                    windows_beep()
                if ARGS.autocheckout:
                    autoCheckout(driver)
                time.sleep(1400)
    except AttributeError:
        pass

    try:
        no_slot_pattern = 'No delivery windows available. New windows are released throughout the day.'
        if no_slot_pattern == soup.find('h4', class_='a-alert-heading').text:
            print("NO SLOTS!")
    except AttributeError:
        if ARGS.send_text:
            send_text("Whole foods 3 slot open")
        print('SLOTS OPEN 3!')
        os.system('say "Slots for delivery opened!"')
        no_open_slots = False
        if os.name == "nt":
            windows_beep()
        if ARGS.autocheckout:
            autoCheckout(driver)
    return no_open_slots


def amazon_fresh(driver, soup):
    no_open_slots = True
    no_open_slots = "No doorstep delivery windows are available for"
    try:
        no_slots_from_web = driver.find_element_by_xpath(
            '/html/body/div[5]/div/div/div[2]/div/div/form/div[3]/div[4]/div/div[2]/div[2]/div[6]/div/div[2]/div/div[2]/div/div[20]/div[1]/div[1]/div/div/div/span').text
        if no_open_slots in no_slots_from_web:
            pass
        else:
            print('SLOTS OPEN!')
            os.system('say "Slots for delivery opened!"')
            no_open_slots = False
            time.sleep(1400)
    except NoSuchElementException:
        print('SLOTS OPEN!')
        os.system('say "Slots for delivery opened!"')
        no_open_slots = False
        time.sleep(1400)

    try:
        open_slots = soup.find('div', class_='orderSlotExists').text()
        if open_slots != "false":
            print('SLOTS OPEN!')
            os.system('say "Slots for delivery opened!"')
            no_open_slots = False
            time.sleep(1400)
    except AttributeError:
        pass
    return no_open_slots


def getWFSlot(productUrl: str) -> None:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    if ARGS.browser == "chrome":
        driver = webdriver.Chrome()
    elif ARGS.browser == "firefox":
        driver = webdriver.Firefox()
    else:
        raise RuntimeError("Browser type not recognized")
    driver.get(productUrl)
    html = driver.page_source
    soup = bs4.BeautifulSoup(html)
    time.sleep(60)
    no_open_slots = True

    while no_open_slots:
        driver.refresh()
        print("refreshed")
        html = driver.page_source
        soup = bs4.BeautifulSoup(html)
        time.sleep(4)
        if ARGS.amazon_fresh:
            no_open_slots = amazon_fresh
        else:
            no_open_slots = prime_now(driver, soup)


def main() -> None:
    getWFSlot('https://www.amazon.com/gp/buy/shipoptionselect/handlers/display.html?hasWorkingJavascript=1')


if __name__ == "__main__":
    ARGS = arguments()
    if ARGS.browser == "firefox" and ARGS.autocheckout:
        raise RuntimeError("Auto checkout only available with chrome")
    main()
