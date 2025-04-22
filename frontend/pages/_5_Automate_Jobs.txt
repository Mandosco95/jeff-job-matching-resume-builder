import streamlit as st
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

def validate_openai_key(api_key):
    """Validate OpenAI API key by making a test request"""
    try:
        openai.api_key = api_key
        # Make a minimal test request
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return True, "API key is valid!"
    except Exception as e:
        return False, f"API key validation failed: {str(e)}"

# --- Helper function to initialize webdriver ---
def get_driver():
    options = webdriver.ChromeOptions()
    # Add any desired options here (e.g., headless mode if needed, though not for manual CAPTCHA)
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        st.error(f"Failed to initialize WebDriver: {e}")
        st.error("Please ensure Google Chrome is installed and accessible.")
        return None

# --- Streamlit Page Logic ---

# Get query parameters
params = st._get_query_params()

# Check if the 'show_automate' parameter is set to 'true'
show_automate_param = params.get("show_automate")
if show_automate_param and show_automate_param[0] == "true":
    st.set_page_config(page_title="Automate Form", page_icon="🤖")
    st.title("🤖 Web Form Automation")
    
    # API Key Configuration Section
    st.header("🔑 API Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        value=OPENAI_API_KEY if OPENAI_API_KEY else "",
        type="password",
        help="Enter your OpenAI API key. It will be used for automation tasks."
    )
    
    if st.button("Validate API Key"):
        if api_key:
            with st.spinner("Validating API key..."):
                is_valid, message = validate_openai_key(api_key)
                if is_valid:
                    st.success(message)
                else:
                    st.error(message)
        else:
            st.error("Please enter an API key")
    
    st.divider()
    
    # Form Automation Section
    st.header("📝 Form Automation")
    st.write("Enter a URL and form data, then launch the browser to fill the form. Solve any CAPTCHA manually.")

    # --- Inputs ---
    target_url = st.text_input("Target Website URL", "https://example.com/contact") # Replace with your target
    name_to_fill = st.text_input("Name", "Test User")
    email_to_fill = st.text_input("Email", "test@example.com")

    # --- Placeholders for Selectors (IMPORTANT: Replace these with actual selectors from your target website) ---
    # Use browser developer tools (Inspect Element) to find appropriate IDs, names, or XPaths
    FORM_FIELD_NAME_SELECTOR = (By.ID, "name-input-id") # Example: (By.ID, "name") or (By.NAME, "username") or (By.XPATH, "//input[@placeholder='Your Name']")
    FORM_FIELD_EMAIL_SELECTOR = (By.ID, "email-input-id") # Example: (By.ID, "email")
    SUBMIT_BUTTON_SELECTOR = (By.XPATH, "//button[@type='submit']") # Example: (By.ID, "submit-button")

    # Initialize session state for driver
    if 'driver' not in st.session_state:
        st.session_state.driver = None
    if 'form_filled' not in st.session_state:
        st.session_state.form_filled = False

    # --- Button 1: Launch Browser & Fill Form ---
    if st.button("Launch Browser & Fill Form"):
        if st.session_state.driver is None: # Start only if not already running
            st.session_state.driver = get_driver()

        if st.session_state.driver:
            try:
                st.info(f"Navigating to {target_url}...")
                st.session_state.driver.get(target_url)
                st.session_state.driver.maximize_window() # Optional: Maximize

                wait = WebDriverWait(st.session_state.driver, 15) # Wait up to 15 seconds

                # Wait for and fill Name field
                st.write("Filling Name field...")
                name_field = wait.until(EC.presence_of_element_located(FORM_FIELD_NAME_SELECTOR))
                name_field.clear()
                name_field.send_keys(name_to_fill)
                st.write("Name field filled.")

                # Wait for and fill Email field
                st.write("Filling Email field...")
                email_field = wait.until(EC.presence_of_element_located(FORM_FIELD_EMAIL_SELECTOR))
                email_field.clear()
                email_field.send_keys(email_to_fill)
                st.write("Email field filled.")

                st.session_state.form_filled = True
                st.success("Form fields filled successfully!")
                st.warning("ACTION REQUIRED: Please switch to the browser window opened by Selenium.\n"
                           "Solve any CAPTCHA or complete other manual steps required.\n"
                           "Once ready, click the 'Submit Form (After CAPTCHA)' button below.")

            except TimeoutException:
                st.error("Error: Timed out waiting for form elements. Check the selectors or website load time.")
                if st.session_state.driver:
                    st.session_state.driver.quit()
                    st.session_state.driver = None
                    st.session_state.form_filled = False
            except NoSuchElementException:
                 st.error("Error: Could not find one of the form elements using the provided selectors. Please check them.")
                 if st.session_state.driver:
                    st.session_state.driver.quit()
                    st.session_state.driver = None
                    st.session_state.form_filled = False
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                if st.session_state.driver:
                    st.session_state.driver.quit()
                    st.session_state.driver = None
                    st.session_state.form_filled = False
        else:
            st.error("WebDriver could not be initialized. Cannot proceed.")


    # --- Button 2: Submit Form (After Manual Steps) ---
    if st.session_state.form_filled: # Only show if form was filled
         if st.button("Submit Form (After CAPTCHA)"):
             if st.session_state.driver:
                 try:
                     st.info("Attempting to find and click the submit button...")
                     wait = WebDriverWait(st.session_state.driver, 10)
                     submit_button = wait.until(EC.element_to_be_clickable(SUBMIT_BUTTON_SELECTOR))
                     submit_button.click()
                     st.success("Submit button clicked! Check the browser for confirmation or next steps.")
                     # Optionally add a small delay or check URL/content for success indicator
                     time.sleep(5) # Give time for page to potentially react

                 except TimeoutException:
                     st.error("Error: Timed out waiting for the submit button to be clickable. Was the CAPTCHA solved?")
                 except NoSuchElementException:
                     st.error("Error: Could not find the submit button using the provided selector.")
                 except Exception as e:
                     st.error(f"An error occurred during submission: {str(e)}")
                 finally:
                     # Clean up
                     st.info("Closing the browser.")
                     if st.session_state.driver:
                         st.session_state.driver.quit()
                     st.session_state.driver = None
                     st.session_state.form_filled = False
                     st.rerun() # Rerun to reset the page state cleanly

             else:
                 st.error("Error: Browser session lost or not started.")
                 st.session_state.form_filled = False # Reset state


else: # If query param is not set correctly
    st.error("Access denied. This page requires the '?show_automate=true' query parameter to be viewed.")
    st.stop() 