import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time
import threading
import os
from pathlib import Path

class BrowserAutomation:
    def __init__(self):
        self.apkpure_driver = None
        self.uptodown_driver = None
        self.apkpure_tabs = []
        self.uptodown_tabs = []
        self.downloads_path = str(Path.home() / "Downloads")
        self.total_file=0
        
    def cleanup_downloads(self):
        """Delete APK files containing the word 'black' in their name from the downloads folder"""
        try:
            for filename in os.listdir(self.downloads_path):
                if filename.lower().endswith('.apk') and 'black' in filename.lower():
                    file_path = os.path.join(self.downloads_path, filename)
                    try:
                        os.remove(file_path)
                        self.total_file=self.total_file+1
                        print(f"total_file deleted: {self.total_file}")
                    except Exception as e:
                        print(f"Failed to delete file {filename}: {str(e)}")
        except Exception as e:
            print(f"Error while cleaning downloads folder: {str(e)}")

    def create_driver(self):
        """Create browser instance"""
        try:
            edge_options = EdgeOptions()
            edge_service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=edge_service, options=edge_options)
           
        except:
            try:
                firefox_options = FirefoxOptions()
                firefox_service = FirefoxService(GeckoDriverManager().install())
                return webdriver.Firefox(service=firefox_service, options=firefox_options)
            except:
                try:
                    chrome_options = ChromeOptions()
                    chrome_service = ChromeService(ChromeDriverManager().install())
                    return webdriver.Chrome(service=chrome_service, options=chrome_options)
                except:
                    raise Exception("No supported browser found")

    def visit_apkpure(self, tab_index):
        """Visit APKPure site repeatedly"""
        while True:
            try:
                self.apkpure_driver.switch_to.window(self.apkpure_tabs[tab_index])
                self.apkpure_driver.get("https://d.apkpure.com/b/APK/com.blacklotus.app?version=latest")
                time.sleep(0.5)
            except:
                continue

    def visit_uptodown(self, tab_index):
             try:
                self.uptodown_driver.switch_to.window(self.uptodown_tabs[tab_index])
                self.uptodown_driver.get("https://black-lotus.en.uptodown.com/android/download")
                time.sleep(5)
                
                download_button = WebDriverWait(self.uptodown_driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#detail-download-button"))
                )
                
                # التمرير إلى العنصر
                self.uptodown_driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                time.sleep(1)  # انتظر لإكمال التمرير
                
                # ثم حاول النقر
                #download_button.click()
                self.uptodown_driver.execute_script("arguments[0].click();", download_button)

                print(f"Download button clicked in tab {tab_index}")
                
             except Exception as e:
                print(f"Error in tab {tab_index}: {str(e)}")

    def run(self):
        """Run main program"""
        self.cleanup_downloads()
        
        # Create two separate windows
        print("Creating APKPure window...")
        self.apkpure_driver = self.create_driver()
        print("Creating Uptodown window...")
        self.uptodown_driver = self.create_driver()
        
        # Open 10 tabs in APKPure window
        self.apkpure_tabs.append(self.apkpure_driver.current_window_handle)
        for _ in range(9):
            self.apkpure_driver.execute_script("window.open('');")
            self.apkpure_tabs.append(self.apkpure_driver.window_handles[-1])
        
        # Open 10 tabs in Uptodown window
        self.uptodown_tabs.append(self.uptodown_driver.current_window_handle)
        for _ in range(9):
            self.uptodown_driver.execute_script("window.open('');")
            self.uptodown_tabs.append(self.uptodown_driver.window_handles[-1])

        threads = []
        
        # Run APKPure tabs
        for i in range(10):
            thread = threading.Thread(target=self.visit_uptodown, args=(i,))
            threads.append(thread)
            thread.start()

        # Run Uptodown tabs
        for i in range(10):
            thread = threading.Thread(target=self.visit_uptodown, args=(i,))
            threads.append(thread)
            thread.start()

        # Run periodic cleanup
        cleanup_thread = threading.Thread(target=self.periodic_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def periodic_cleanup(self):
        """Periodic cleanup of downloads folder every 5 seconds"""
        while True:
            self.cleanup_downloads()
            time.sleep(5)

    def cleanup(self):
        """Close browsers"""
        if self.apkpure_driver:
            try:
                self.apkpure_driver.quit()
            except:
                pass
        if self.uptodown_driver:
            try:
                self.uptodown_driver.quit()
            except:
                pass

if __name__ == "__main__":
    try:
        automation = BrowserAutomation()
        automation.run()
    except KeyboardInterrupt:
        print("\nStopping program...")
    finally:
        automation.cleanup()
