import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Web Scraper", page_icon="💬")
st.title("**Product Review Scraper**")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
import time
import pandas as pd

# Initialize Streamlit session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

if not st.session_state.setup_complete:
    if "url" not in st.session_state:
        st.session_state["url"] = ""
    if "output_file_name" not in st.session_state:
        st.session_state["output_file_name"] = ""

    st.session_state["url"] = st.text_input(
        label="Product URL",
        value=st.session_state["url"],
        placeholder="Paste product URL",
        max_chars=200
    )
    st.session_state["output_file_name"] = st.text_input(
        label="Output File Name (.csv)",
        value=st.session_state["output_file_name"],
        placeholder="Write output file name (e.g., reviews.csv)",
        max_chars=100
    )

    if st.button("Start Scraping", on_click=complete_setup):
        st.write("Setup complete. Starting scraping reviews...")

if st.session_state.setup_complete and not st.session_state.chat_complete:
    chromedriver_autoinstaller.install()  # Auto install matching chromedriver

    # Selenium Chrome options for Streamlit Cloud (headless mode)
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(st.session_state["url"])

    time.sleep(5)  # Give the page some time to load

    reviews_data = []

    for page in range(1, 3):  # Reduced to 2 pages for demo (increase as needed)
        st.write(f"Scraping Page: {page}")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        reviews = soup.find_all("div", {"id": "cm_cr-review_list"})

        for review in reviews:
            titles = review.find_all("a", {"data-hook": "review-title"})
            ratings = review.find_all("i", {"data-hook": "review-star-rating"})
            bodies = review.find_all("span", {"data-hook": "review-body"})
            dates = review.find_all("span", {"data-hook": "review-date"})
            authors = review.find_all("span", {"class": "a-profile-name"})

            for i in range(len(titles)):
                title_text = titles[i].find_all('span')[-1].get_text(strip=True) if titles else ""
                rating_text = ratings[i].find_all('span')[-1].get_text(strip=True) if ratings else ""
                body_text = bodies[i].find_all('span')[-1].get_text(strip=True) if bodies else ""
                date_text = dates[i].get_text(strip=True) if dates else ""
                author_text = authors[i].get_text(strip=True) if authors else ""

                reviews_data.append({
                    "title": title_text,
                    "rating": rating_text,
                    "review": body_text,
                    "date": date_text,
                    "author": author_text
                })

        # Try clicking the 'Next' button
        try:
            next_button = driver.find_element(By.XPATH, '//li[@class="a-last"]/a')
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)  # wait for next page to load
        except NoSuchElementException:
            st.write("No more pages.")
            break

    driver.quit()

    # Save results to CSV
    df = pd.DataFrame(reviews_data)
    output_path = st.session_state["output_file_name"]
    df.to_csv(output_path, index=False)
    st.success(f"Scraping Complete. Data saved to {output_path}")
    st.session_state.chat_complete = True

if st.session_state.chat_complete:
    st.write("Scraping Completed Successfully!")
    if st.button("Restart Scraping", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
