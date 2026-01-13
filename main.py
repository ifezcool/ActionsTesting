from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv('PROCESS_STREET_EMAIL')
PASSWORD = os.getenv('PROCESS_STREET_PASSWORD')
tariff_review = os.getenv('TARIFF_REVIEW')

class ProcessStreetExporter:
    def __init__(self, headless=False):
        options = Options()
        
        # Force headless in CI environment
        if headless or os.getenv('CI'):
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1820,1080')
        # Add these for stability in CI
        options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Rest of your code...

        # Set download directory
        self.download_dir = os.path.abspath("downloads")
        os.makedirs(self.download_dir, exist_ok=True)

        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)

        print("✓ Browser initialized")
        print("✓ Downloads will be saved to:", self.download_dir)

    def login(self):
        print("\n" + "=" * 60)
        print("STEP 1: Logging in to Process Street")
        print("=" * 60)

        try:
            self.driver.get(tariff_review)

            # Email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(EMAIL)

            # Password
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)

            # Login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Wait for redirect
            self.wait.until(lambda d: 'login' not in d.current_url.lower())

            print("✓ Login successful!")
            return True

        except Exception as e:
            print("✗ Login failed:", e)
            self.driver.save_screenshot("login_error.png")
            return False

    def show_completed_runs(self):
        print("\n" + "=" * 60)
        print("STEP 2: Toggling 'Show completed runs'")
        print("=" * 60)

        try:
            # Wait for dashboard to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            # Scroll down so the toggle is visible
            print("  → Scrolling page...")
            for _ in range(5):
                self.driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(0.7)

            # Locate the label text
            label = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[contains(text(),'Show completed runs')]"
                ))
            )

            # From the label, find the toggle switch next to it
            toggle = label.find_element(
                By.XPATH,
                "./ancestor::div[1]//input | ./following::input[1] | ./preceding::input[1]"
            )

            # Scroll directly to toggle
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", toggle
            )
            time.sleep(1)

            # Click the toggle (use JS fallback)
            try:
                toggle.click()
            except:
                self.driver.execute_script("arguments[0].click();", toggle)

            print("✓ 'Show completed runs' toggled ON")
            time.sleep(2)

        except Exception as e:
            print("✗ Failed to toggle 'Show completed runs':", e)
            self.driver.save_screenshot("show_completed_error.png")
            raise

    def find_and_click_ellipsis(self, row_text=None):
        """
        Find and click the ellipsis menu button.
        """
        print("\n" + "="*60)
        print("STEP 3: Finding and Clicking Ellipsis Menu")
        print("="*60)
        
        try:
            time.sleep(1)
            
            # Scroll down slightly to ensure buttons are in viewport
            self.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)
            
            # Strategy: Find all buttons where ID starts with 'menu-button' because id changes for every pull/site refresh
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.chakra-button.chakra-menu__menu-button.css-qvlyp9[id^='menu-button']")
            ellipsis_button = None
            if row_text:
                # If a row_text is provided, find the button in that specific row
                for btn in buttons:
                    parent_row = btn.find_element(By.XPATH, "./ancestor::tr")
                    if row_text in parent_row.text and btn.is_displayed() and btn.is_enabled():
                        ellipsis_button = btn
                        print(f"Found ellipsis button for row with text: {row_text}")
                        break
            else:
                # Otherwise, pick the first visible & enabled button
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        ellipsis_button = btn
                        print("Found visible ellipsis button")
                        break
            
            if ellipsis_button is None:
                raise Exception("Could not find a visible ellipsis button")
            
            full_id = ellipsis_button.get_attribute('id')
            print(f"  ✓ Found ellipsis button with ID: {full_id}")
            
            filter_button = self.wait.until(
                            EC.presence_of_element_located( 
                                (By.ID, full_id)
                            )
                        )

            # Scroll button into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", filter_button
            )
            time.sleep(0.5)
            
            # Click using JavaScript (bypasses React/Chakra issues)
            self.driver.execute_script("arguments[0].click();", filter_button)
            
            # Wait until dropdown opens (aria-expanded = "true")
            self.wait.until(lambda d: filter_button.get_attribute("aria-expanded") == "true")
            print(" ✓ Ellipsis dropdown opened successfully")
            #Click Export option
            export_btn = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[@role='menuitem' or @role='option']//*[normalize-space()='Export']"
                ))
            )

            try:
                export_btn.click()
            except:
                self.driver.execute_script("arguments[0].click();", export_btn)

            print("✓ Clicked Export button")

            #Click Export option again to confirm download
            export_selectors = [
                (By.XPATH, "//button[contains(text(), 'Export')]"),
                (By.XPATH, "//button[contains(text(), 'export')]"),
                (By.XPATH, "//*[contains(text(), 'Export')]"),
            ]
            
            export_button = None
            for by, selector in export_selectors:
                try:
                    export_button = self.driver.find_element(by, selector)
                    export_button.click()
                    print(f"  → Found Export button to download CSV")
                    break
                except:
                    continue
            
            if not export_button:
                print("✗ Could not find Export button")
                self.driver.save_screenshot('export_button_not_found.png')
                try:
                    generic_export = self.driver.find_element(By.XPATH, "//div[contains(@class, 'modal')]//button[contains(text(), 'Export')]")
                    generic_export.click()
                    print("  → Clicked generic Export button")
                except:
                    pass
            
            # Wait for download to start
            print("  → Waiting for download to complete...")
            time.sleep(20)
            
            # Check if file was downloaded
            files = os.listdir(self.download_dir)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            if csv_files:
                print(f"✓ CSV exported successfully!")
                print(f"✓ Downloaded file(s): {csv_files}")
            else:
                print("⚠ No CSV file found in downloads folder")
                print(f"  Files in folder: {files}")
            
            return True
            
        except Exception as e:
            print(f"✗ Export failed: {e}")
            self.driver.save_screenshot('export_error.png')
            return False               
            

    def wait_for_user(self, seconds=60):
        """Keep browser open for inspection"""
        print(f"\n  → Keeping browser open for {seconds} seconds...")
        print("     (You can manually check the page)")
        time.sleep(seconds)
    
    def close(self):
        """Close the browser"""
        self.driver.quit()
        print("\n✓ Browser closed")    


# ------------------- RUN SCRIPT -------------------

exporter = ProcessStreetExporter(headless=True)

if not exporter.login():
    exporter.close()
    exit(1)

exporter.show_completed_runs()
exporter.find_and_click_ellipsis()
exporter.wait_for_user(60)
exporter.close()
