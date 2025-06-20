import time
import json
import os
import signal
import sys
import random
import traceback
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import database
from database import Database

WEBSITES = [
    # websites of your choice
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

TRACES_PER_SITE = 1000
FINGERPRINTING_URL = "http://localhost:5000" 
OUTPUT_PATH = "dataset.json"

# Initialize the database to save trace data reliably
database.db = Database(WEBSITES)

""" Signal handler to ensure data is saved before quitting. """
def signal_handler(sig, frame):
    print("\nReceived termination signal. Exiting gracefully...")
    try:
        database.db.export_to_json(OUTPUT_PATH)
    except:
        pass
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


"""
Some helper functions to make your life easier.
"""

def is_server_running(host='127.0.0.1', port=5000):
    """Check if the Flask server is running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def setup_webdriver():
    """Set up the Selenium WebDriver with Chrome options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--disable-extensions")

    driver_path = "E:\CSE406\Side_Channel_Attack_Offline\chromedriver-win64\chromedriver.exe"  
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def retrieve_traces_from_backend(driver):
    """Retrieve traces from the backend API."""
    traces = driver.execute_script("""
        return fetch('/api/get_results')
            .then(response => response.ok ? response.json() : {traces: []})
            .then(data => data.traces || [])
            .catch(() => []);
    """)
    
    count = len(traces) if traces else 0
    print(f"  - Retrieved {count} traces from backend API" if count else "  - No traces found in backend storage")
    return traces or []

def clear_trace_results(driver, wait):
    """Clear all results from the backend by pressing the button."""
    clear_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear Results')]")
    clear_button.click()

    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, "//div[@role='alert']"), "Results cleared successfully!"))
    
def is_collection_complete():
    """Check if target number of traces have been collected."""
    current_counts = database.db.get_traces_collected()
    remaining_counts = {website: max(0, TRACES_PER_SITE - count) 
                      for website, count in current_counts.items()}
    return sum(remaining_counts.values()) == 0

"""
Your implementation starts here.
"""

def collect_single_trace(driver, wait, website_url):
    """ Implement the trace collection logic here. 
    1. Open the fingerprinting website
    2. Click the button to collect trace
    3. Open the target website in a new tab
    4. Interact with the target website (scroll, click, etc.)
    5. Return to the fingerprinting tab and close the target website tab
    6. Wait for the trace to be collected
    7. Return success or failure status
    """
    driver.get(FINGERPRINTING_URL)
    
    # Step 2: Click "Collect Trace" button
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Collect Trace')]"))).click()

    # Step 3: Open target website in new tab
    driver.execute_script("window.open(arguments[0]);", website_url)
    driver.switch_to.window(driver.window_handles[1])
    
    # Step 4: Simulate interaction
    time.sleep(random.uniform(3, 5))
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(random.uniform(2, 4))

    # Step 5: Close target website tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    # Step 6: Wait for backend to finish heatmap generation
    time.sleep(5)

    return True


def collect_fingerprints(driver, target_counts=None):
    """ Implement the main logic to collect fingerprints.
    1. Calculate the number of traces remaining for each website
    2. Open the fingerprinting website
    3. Collect traces for each website until the target number is reached
    4. Save the traces to the database
    5. Return the total number of new traces collected
    """
    wait = WebDriverWait(driver, 15)

    for website in WEBSITES:
        current_count = database.db.get_traces_collected().get(website, 0)
        remaining = TRACES_PER_SITE - current_count

        print(f"Collecting for: {website} ({remaining} remaining)")
        
        for _ in range(remaining):
            try:
                if collect_single_trace(driver, wait, website):
                    # Download collected traces from backend
                    traces = retrieve_traces_from_backend(driver)
                    
                    for trace in traces:
                        database.db.save_trace(website, WEBSITES.index(website), trace)

                    clear_trace_results(driver, wait)
            except Exception as e:
                print("Error during collection:", e)
                traceback.print_exc()


def main():
    """ Implement the main function to start the collection process.
    1. Check if the Flask server is running
    2. Initialize the database
    3. Set up the WebDriver
    4. Start the collection process, continuing until the target number of traces is reached
    5. Handle any exceptions and ensure the WebDriver is closed at the end
    6. Export the collected data to a JSON file
    7. Retry if the collection is not complete
    """
    if not is_server_running():
        print("Flask server is not running. Start your app.py first.")
        return

    database.db.init_database()
    driver = setup_webdriver()

    try:
        while True:
            collect_fingerprints(driver)
            # Check if collection complete
            remaining = sum(max(0, TRACES_PER_SITE - count) for count in database.db.get_traces_collected().values())
            if remaining == 0:
                print("Data collection complete!")
                break
            else:
                print(f"Still remaining traces: {remaining}")
                time.sleep(2)
    finally:
        database.db.export_to_json(OUTPUT_PATH)
        driver.quit()


if __name__ == "__main__":
    main()
