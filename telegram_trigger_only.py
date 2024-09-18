# Automatic video call system for elderly V0.1
# by Yo Nutchanon @ Cytron Thailand
#
# Online platform use in this project
#  1. Google Meet
#  2. Telegram
#
# Tools use in this project
#  1. Python
#  2. Selenium
#  3. Chromium remote debugging
#
# Required file for this project
#  1. chromedriver
#  2. chromium-launcher.sh
#  3. chromium-terminate.sh
#  4. telegram_config.py (For store Telegram bot token and username)

# Feature including 
#  1. Locate element position using static method (Refer to text on element)
#  2. Local report join-left user and user number (Mutitasking handle by threading)
#  3. Start session from Telegram only (No local input)
#  4. Telegram bot able to handle command in Telegram group

# Future improve
#  1. Some element using random class ID to locate (ex. people_number_class)
#  2. Rearrange local report and add time log to each action

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException


import time
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import subprocess
import sys
import threading
import re

import telegram_config

people_number_class = 'uGOf1d'
chrome_launcher_path = '~/automatic-videocall-for-elderly/chromium-launcher.sh'
chrome_terminate_path = '~/automatic-videocall-for-elderly/chromium-terminate.sh'
def restart():
    print('Restarting script...')
    os.execv(sys.executable, ['python'] + sys.argv)

def remove_status(text: str) -> str:
    if text is None:
        return text
    
    # Use regex to replace "has left the meeting" or "joined" with an empty string
    cleaned_text = re.sub(r"(has left the meeting|joined)", "", text).strip()
    return cleaned_text

async def call_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Session starting!")
    shell_process = subprocess.Popen(["sh", chrome_launcher_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await update.message.reply_text("Browser opened!")

	# Set a timeout for waiting (in seconds)
    create_room_timeout = 8
    wait_ppl_timeout = 120
    check_ppl_inroom_timeout = 10
    update_ppl_inroom_period = 1

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")

    cService = webdriver.ChromeService(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service = cService, options=chrome_options)
    time.sleep(2)
    newMeeting=driver.find_element(By.XPATH, "//span[text()='New meeting']")

    newMeeting.click()
    time.sleep(2)
    startInstant=driver.find_element(By.XPATH, "//span[text()='Start an instant meeting']")
    startInstant.click()

    time.sleep(1)
    wait1 = WebDriverWait(driver, create_room_timeout)
    try:
        print("waiting for room")
        start_time = time.time()  # Start time
        element = wait1.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'meet.google.com/') and starts-with(text(), 'meet.google.com/')]")))
        end_time = time.time()  # End time
        print(f"Found element in {end_time - start_time} seconds")
    except:
        end_time = time.time()  # End time
        print(f"Room error. Waiting for {end_time - start_time}, Restart scipt")
        await update.message.reply_text("Room error, Restart scipt")
        driver.quit()
        os.system(f'sh {chrome_terminate_path}')
        restart()

    meet_links = driver.find_elements(By.XPATH, "//*[contains(text(), 'meet.google.com/') and starts-with(text(), 'meet.google.com/')]")

    # Loop through the elements and print the extracted text
    for link in meet_links:
        print(link.text)
    await update.message.reply_text("Room has been created!")
    await update.message.reply_text("Please join within 30 seconds :" + link.text)

	# Create a WebDriverWait object
    wait2 = WebDriverWait(driver, wait_ppl_timeout)
    try:
        element = wait2.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Admit']")))
        element.click()
    except:
        print("Noone join session. End this session")
        await update.message.reply_text("Noone join session. Ending")
        driver.quit()
        os.system(f'sh {chrome_terminate_path}')
        restart()
    
    time.sleep(5)
    
    

    def admit():
        ppnumber = driver.find_element(By.CLASS_NAME, people_number_class)
        wait3 = WebDriverWait(driver, check_ppl_inroom_timeout)
        while(int(ppnumber.text) >=2):
            ppnumber = driver.find_element(By.CLASS_NAME, people_number_class)
            try:
                element = wait3.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Admit']")))
                element.click()
            except:
                None
        
        print("admit end")
                
    def user_report():
        last_join_user = None
        last_left_user = None
        last_ppnumber = None
        current_join_user = None
        current_left_user = None
        last_status = None
        ppnumber = driver.find_element(By.CLASS_NAME, people_number_class)
        wait4 = WebDriverWait(driver, update_ppl_inroom_period)
        
        while int(ppnumber.text) >= 2:
            ppnumber = driver.find_element(By.CLASS_NAME, people_number_class)
            current_ppnumber = ppnumber.text
            if current_ppnumber != last_ppnumber:
                print("Session online. Users on call now: " + ppnumber.text)
                last_ppnumber = current_ppnumber  # Update the last printed value

            try:
                # Check for users who have joined
                report_join_user = driver.find_elements(By.XPATH, "//*[contains(text(), 'joined')]")
                for join_user in report_join_user:
                    #current_join_user = None
                    try:
                        current_join_user = join_user.text
                    except StaleElementReferenceException:
                        # Re-find the element in case it becomes stale
                        continue
                    if current_join_user != last_join_user and len(current_join_user) != 0 and current_join_user != last_status:
                        #print(f"1 {current_join_user}")
                        print(current_join_user)
                        last_join_user = current_join_user
                        last_status = current_join_user
                        #print(f"1 LJU: {last_join_user} , LLU: {last_left_user} ")

                if remove_status(last_join_user) == remove_status(last_left_user) and last_join_user != None and last_left_user != None:
                    last_join_user = None
                    last_left_user = None
                    #print(f"1 Equal found LJU: {last_join_user}, LLU: {last_left_user}")

            except NoSuchElementException:
                # If the element is not found, continue waiting
                continue

            except TimeoutException:
                None

            try:
                # Check for users who have left
                report_left_user = driver.find_elements(By.XPATH, "//*[contains(text(), 'has left the meeting')]")
                for left_user in report_left_user:
                    #current_left_user = None
                    try:
                        current_left_user = left_user.text
                    except StaleElementReferenceException:
                        # Re-find the element in case it becomes stale
                        continue
                    if current_left_user != last_left_user and len(current_left_user) != 0 and current_left_user != last_status:
                        #print(f"2 {current_left_user}")
                        print(current_left_user)
                        # Update the last printed value
                        last_left_user = current_left_user
                        last_status = current_left_user
                        #print(f"2 LJU: {last_join_user} , LLU: {last_left_user} ")

                if remove_status(last_join_user) == remove_status(last_left_user) and last_join_user != None and last_left_user != None:
                    last_join_user = None
                    last_left_user = None
                    #print(f"2 Equal found LJU: {last_join_user}, LLU: {last_left_user}")

            except NoSuchElementException:
                # If the element is not found, continue waiting
                continue

            except TimeoutException:
                None
        print(last_left_user)
        print("user report end")
                
    thread1 = threading.Thread(target=admit)
    thread2 = threading.Thread(target=user_report)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    print("Session end. Closing session")
    await update.message.reply_text("Thanks for using me!. Bye")
    driver.quit()
    os.system(f'sh {chrome_terminate_path}')
    restart()

    
async def check_pp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I can help!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Custom command here")

# Responses


def handler_response(text: str) -> str:
    processed: str = text.lower()
    return "."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if telegram_config.BOT_USERNAME in text:
            new_text: str = text.replace(telegram_config.BOT_USERNAME, '').strip()
            response: str = handler_response(new_text)
        else:
            return
    else:
        response: str = handler_response(text)

    print('Bot:', response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(telegram_config.TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('call', call_command))
    app.add_handler(CommandHandler('check_people', check_pp_command))
    app.add_handler(CommandHandler('help', help_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
