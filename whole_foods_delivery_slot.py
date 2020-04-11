import argparse
import os
import time

import bs4
from selenium import webdriver
from twilio.rest import Client


def arguments():
    """
    Arguments for the script
    """
    parser = argparse.ArgumentParser(
        description="Pings Amazon Prim Whole Foods for open delivery slots")
    parser.add_argument("-b", dest="browser", type=str, default="chrome",
                        choices=("firefox", "chrome"), help="browser type [default: chrome]")
    return parser.parse_args()


def send_text(message: str) -> None:
    """
    Uses twilio to send a tex message

    Setup an account with twilio.  An additional file is created called info.csv in the same
    directory.  Have 4 columns, column name doesn't matter, but the first row content is your
    account sid, authorization token, your number to text to and setup with the account, and
    the from number created by twilio.

    :message: the message sent as a text
    :return: No return
    """
    with open("info.csv", "r") as info_file:
        info_file.readline()  # remove the column headers and go to row 1
        account_sid, auth_token, to_num, from_num = info_file.readline().split(",")  # split values by comma

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        to=to_num,
        from_=from_num
    )


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

        slot_patterns = ['Next available', '1-hour delivery windows', '2-hour delivery windows']
        try:
            next_slot_text = soup.find(
                'h4', class_='ufss-slotgroup-heading-text a-text-normal').text
            if any(next_slot_text in slot_pattern for slot_pattern in slot_patterns):
                send_text("Whole foods 1 slot open")
                print('SLOTS OPEN 1!')
                os.system('say "Slots for delivery opened!"')
                no_open_slots = False
                time.sleep(1400)
        except AttributeError:
            pass

        try:
            slot_opened_text = "Not available"
            all_dates = soup.findAll("div", {"class": "ufss-date-select-toggle-text-availability"})
            for each_date in all_dates:
                if slot_opened_text not in each_date.text:
                    send_text("Whole foods 2 slot open")
                    print('SLOTS OPEN 2!')
                    os.system('say "Slots for delivery opened!"')
                    no_open_slots = False
                    time.sleep(1400)
        except AttributeError:
            pass

        try:
            no_slot_pattern = 'No delivery windows available. New windows are released throughout the day.'
            if no_slot_pattern == soup.find('h4', class_='a-alert-heading').text:
                print("NO SLOTS!")
        except AttributeError:
            send_text("Whole foods 3 slot open")
            print('SLOTS OPEN 3!')
            os.system('say "Slots for delivery opened!"')
            no_open_slots = False


def main() -> None:
    getWFSlot('https://www.amazon.com/gp/buy/shipoptionselect/handlers/display.html?hasWorkingJavascript=1')


if __name__ == "__main__":
    ARGS = arguments()
    main()
