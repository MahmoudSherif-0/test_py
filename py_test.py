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
import undetected_chromedriver as uc
import time
import threading
import os
import random
import json
import pickle
import base64
from pathlib import Path
from fake_useragent import UserAgent
import requests
from dotenv import load_dotenv

# محاولة استيراد مكتبة العُقَد إن وجدت
try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("selenium-stealth not available. For better results, install with: pip install selenium-stealth")

class BrowserAutomation:
    def __init__(self):
        self.apkpure_driver = None
        self.uptodown_driver = None
        self.youtube_driver = None
        self.apkpure_tabs = []
        self.uptodown_tabs = []
        self.youtube_tabs = []
        self.downloads_path = str(Path.home() / "Downloads")
        self.user_agent = UserAgent().random
        self.proxies = []
        self.load_proxies()
        self.cookies_file = "apkpure_cookies.pkl"
        self.uptodown_cookies_file = "uptodown_cookies.pkl"
        self.youtube_cookies_file = "youtube_cookies.pkl"
        # قائمة المواقع العشوائية للزيارة بعد مشاهدة الفيديو
        self.random_sites = [
            "https://ai-news1.blogspot.com/",
            "https://ai-news1.blogspot.com/2024/12/claude-ai.html#more",
            "https://ai-news1.blogspot.com/2024/12/chatgpt.html",
            "https://blacklotusai.blogspot.com/",
            "https://blacklotusai.blogspot.com/2025/01/black-lotus-ai-is-advanced-application.html",
            "https://blacklotusai.blogspot.com/2024/07/black-lotus-creator-is-app-that-helps.html"
        ]
        # قائمة فيديوهات يوتيوب
        self.youtube_videos = [
               "https://ai-news1.blogspot.com/",
            "https://ai-news1.blogspot.com/2024/12/claude-ai.html#more",
            "https://ai-news1.blogspot.com/2024/12/chatgpt.html",
            "https://blacklotusai.blogspot.com/",
            "https://blacklotusai.blogspot.com/2025/01/black-lotus-ai-is-advanced-application.html",
            "https://blacklotusai.blogspot.com/2024/07/black-lotus-creator-is-app-that-helps.html"
        ]
        # مدة الفيديو بالثواني (4 دقائق و14 ثانية)
        self.video_duration = 4 * 60+14   # 4 minutes  14 seconds
        
        # تحميل الكوكيز من ملف .env إذا كان موجودًا
        self.load_cookies_from_env_file()
        
    def load_proxies(self):
        """Load proxies from free proxy list or file"""
        try:
            # يمكنك استخدام قائمة ثابتة من البروكسيات
            # self.proxies = ["182.52.229.165:8080", "123.45.67.89:8080"]
            
            # أو يمكنك الحصول على قائمة من البروكسيات عبر API
            response = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all")
            if response.status_code == 200:
                self.proxies = [proxy for proxy in response.text.split("\n") if proxy.strip()]
                print(f"Loaded {len(self.proxies)} proxies")
            
            # إذا فشل الحصول على البروكسيات أو كانت القائمة فارغة، استخدم قائمة افتراضية
            if not self.proxies:
                self.proxies = ["185.199.229.156:7492", "185.199.228.220:7300", "185.199.231.45:8382"]
        except Exception as e:
            print(f"Error loading proxies: {e}")
            self.proxies = ["185.199.229.156:7492", "185.199.228.220:7300", "185.199.231.45:8382"]
    
    def get_random_proxy(self):
        """Get random proxy from list"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
        
    def cleanup_downloads(self):
        """Delete APK files containing the word 'black' in their name from the downloads folder"""
        try:
            deleted_count = 0
            for filename in os.listdir(self.downloads_path):
                if filename.lower().endswith('.apk') and ('black' in filename.lower() or filename.lower().startswith('com.blacklotus.app')) and not filename.lower().endswith('.crdownload'):
                    file_path = os.path.join(self.downloads_path, filename)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print(f"Failed to delete file {filename}: {str(e)}")
            if deleted_count > 0:
                print(f"Deleted {deleted_count} APK files")
        except Exception as e:
            print(f"Error while cleaning downloads folder: {str(e)}")

    def create_driver(self):
        """Create browser instance"""
        try:
            # Try undetected-chromedriver first
            options = uc.ChromeOptions()
            options.add_argument(f'--user-agent={self.user_agent}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-browser-side-navigation')
            options.add_argument('--disable-gpu')
            
            # Add proxy if available
            # proxy = self.get_random_proxy()
            # if proxy:
            #     options.add_argument(f'--proxy-server={proxy}')
            #     print(f"Using proxy: {proxy}")
                
            prefs = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": self.downloads_path,
                "download.prompt_for_download": False,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                # السماح بالتنزيلات المتعددة
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "browser.download.manager.showWhenStarting": False,
                # تعطيل تنبيهات التنزيل وحظر الملفات المشبوهة
                "browser.download.manager.showAlertOnComplete": False,
                "browser.download.quarantineDownloads": False
            }
            options.add_experimental_option("prefs", prefs)
            
            # Add timezone to make fingerprint more consistent
            options.add_argument('--timezone="America/New_York"')
            
            driver = uc.Chrome(options=options)
            
            # Apply stealth if available
            if STEALTH_AVAILABLE:
                stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
            
            return driver
            
        except Exception as e:
            print(f"Error with undetected-chromedriver: {e}")
        try:
            edge_options = EdgeOptions()
            edge_options.add_argument(f'--user-agent={self.user_agent}')
            edge_options.add_argument('--disable-blink-features=AutomationControlled')
            edge_service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=edge_service, options=edge_options)
           
        except:
            try:
                firefox_options = FirefoxOptions()
                firefox_options.add_argument(f'--user-agent={self.user_agent}')
                firefox_service = FirefoxService(GeckoDriverManager().install())
                return webdriver.Firefox(service=firefox_service, options=firefox_options)
            except:
                try:
                    chrome_options = ChromeOptions()
                    chrome_options.add_argument(f'--user-agent={self.user_agent}')
                    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    chrome_options.add_experimental_option('useAutomationExtension', False)
                    chrome_service = ChromeService(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
                    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": self.user_agent})
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    return driver
                except:
                    raise Exception("No supported browser found")

    def save_cookies(self, driver):
        """Save cookies to file"""
        try:
            cookies = driver.get_cookies()
            if cookies:
                with open(self.cookies_file, 'wb') as file:
                    pickle.dump(cookies, file)
                print(f"Saved {len(cookies)} cookies")
        except Exception as e:
            print(f"Error saving cookies: {e}")
    
    def load_cookies(self, driver, domain):
        """Load cookies from file"""
        try:
            cookie_file = None
            if domain == "apkpure.com":
                cookie_file = self.cookies_file
            elif domain == "uptodown.com":
                cookie_file = self.uptodown_cookies_file
            elif domain == "youtube.com":
                cookie_file = self.youtube_cookies_file
            
            if cookie_file and os.path.exists(cookie_file):
                with open(cookie_file, 'rb') as file:
                    cookies = pickle.load(file)
                    
                # First navigate to the domain to properly set the cookies
                driver.get(f"https://{domain}")
                time.sleep(2)
                
                # Add the cookies to the browser
                for cookie in cookies:
                    # Skip cookies from other domains
                    if domain not in cookie.get('domain', ''):
                        continue
                    
                    try:
                        # حذف مفاتيح غير متوافقة إذا وجدت
                        if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                            cookie['expiry'] = int(cookie['expiry'])
                        driver.add_cookie(cookie)
                    except Exception as cookie_error:
                        print(f"Error adding cookie: {cookie_error}")
                
                print(f"Loaded cookies for {domain}")
                return True
            else:
                print(f"No cookies file found for {domain}")
                return False
        except Exception as e:
            print(f"Error loading cookies for {domain}: {e}")
            return False

    def load_cookies_from_env_file(self):
        """تحميل ملفات تعريف الارتباط من ملف .env"""
        try:
            # تحميل المتغيرات من ملف .env
            load_dotenv()
            cookies_env = os.getenv('YOUTUBE_COOKIES_BASE64')
            
            if cookies_env:
                try:
                    # محاولة فك تشفير Base64 إذا كان الإدخال مشفرًا
                    try:
                        cookies_data = base64.b64decode(cookies_env)
                        cookies = pickle.loads(cookies_data)
                    except:
                        # إذا فشل الفك، يفترض أن الإدخال هو JSON مباشر
                        cookies = json.loads(cookies_env)
                    
                    # حفظ ملفات تعريف الارتباط في ملف pickle
                    with open(self.youtube_cookies_file, 'wb') as file:
                        pickle.dump(cookies, file)
                    print(f"تم تحميل {len(cookies)} من ملفات تعريف ارتباط YouTube من ملف .env")
                    return True
                except Exception as e:
                    print(f"خطأ في تحميل ملفات تعريف ارتباط YouTube من ملف .env: {e}")
            else:
                print("لم يتم العثور على متغير YOUTUBE_COOKIES_BASE64 في ملف .env")
        except Exception as e:
            print(f"خطأ في قراءة ملف .env: {e}")
        return False

    def load_cookies_from_env(self):
        """تحميل ملفات تعريف الارتباط من متغيرات البيئة"""
        cookies_env = os.environ.get('YOUTUBE_COOKIES_BASE64')
        if cookies_env:
            try:
                # محاولة فك تشفير Base64 إذا كان الإدخال مشفرًا
                try:
                    cookies_data = base64.b64decode(cookies_env)
                    cookies = pickle.loads(cookies_data)
                except:
                    # إذا فشل الفك، يفترض أن الإدخال هو JSON مباشر
                    cookies = json.loads(cookies_env)
                
                # حفظ ملفات تعريف الارتباط في ملف pickle
                with open(self.youtube_cookies_file, 'wb') as file:
                    pickle.dump(cookies, file)
                print(f"تم تحميل {len(cookies)} من ملفات تعريف ارتباط YouTube من متغيرات البيئة")
                return True
            except Exception as e:
                print(f"خطأ في تحميل ملفات تعريف ارتباط YouTube من متغيرات البيئة: {e}")
        return False
    
    def test_youtube_cookies(self):
        """اختبار ما إذا كانت ملفات تعريف الارتباط لـ YouTube تعمل"""
        try:
            print("اختبار ملفات تعريف الارتباط ليوتيوب...")
            
            # إعداد متصفح Chrome
            options = uc.ChromeOptions()
            driver = uc.Chrome(options=options)
            
            # الانتقال إلى YouTube
            driver.get('https://www.youtube.com')
            time.sleep(2)
            
            # تحميل ملفات تعريف الارتباط
            if os.path.exists(self.youtube_cookies_file):
                with open(self.youtube_cookies_file, 'rb') as file:
                    cookies = pickle.load(file)
                    
                # إضافة ملفات تعريف الارتباط إلى المتصفح
                for cookie in cookies:
                    # تخطي ملفات تعريف الارتباط من نطاقات أخرى
                    if '.youtube.com' not in cookie.get('domain', ''):
                        continue
                    
                    try:
                        # معالجة مفتاح expiry إذا كان float
                        if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                            cookie['expiry'] = int(cookie['expiry'])
                        driver.add_cookie(cookie)
                    except Exception as cookie_error:
                        print(f"خطأ في إضافة ملف تعريف ارتباط: {cookie_error}")
                
                # تحديث الصفحة لتطبيق ملفات تعريف الارتباط
                driver.refresh()
                time.sleep(3)
                
                # التحقق من حالة تسجيل الدخول
                if 'Sign in' not in driver.page_source and 'تسجيل الدخول' not in driver.page_source:
                    print("ملفات تعريف الارتباط تعمل! تم تسجيل الدخول بنجاح.")
                    result = True
                else:
                    print("ملفات تعريف الارتباط لا تعمل. قد تحتاج إلى إعادة تسجيل الدخول.")
                    result = False
            else:
                print(f"ملف ملفات تعريف الارتباط {self.youtube_cookies_file} غير موجود.")
                result = False
                
            # إغلاق المتصفح
            driver.quit()
            return result
            
        except Exception as e:
            print(f"خطأ أثناء اختبار ملفات تعريف الارتباط: {e}")
            return False

    def visit_apkpure(self, tab_index):
        """Visit APKPure site repeatedly"""
        download_count = 0
        while True:
            try:
                self.apkpure_driver.switch_to.window(self.apkpure_tabs[tab_index])
                
                # Add initial delay to appear more human-like
                time.sleep(random.uniform(2, 5))
                
                # Load cookies if available (first tab only)
                if tab_index == 0:
                    self.load_cookies(self.apkpure_driver, "apkpure.com")
                
                # Randomly decide to visit main site first or direct link
                if random.random() < 0.3 or tab_index == 0:
                    # Visit main site first
                    print(f"Tab {tab_index}: Visiting main APKPure site first")
                    self.apkpure_driver.get("https://apkpure.com")
                    time.sleep(random.uniform(3, 7))
                    
                    # Navigate through the site a bit to look more human
                    if random.random() < 0.5:
                        try:
                            # Click on random elements
                            elements = self.apkpure_driver.find_elements(By.TAG_NAME, "a")
                            if elements:
                                random_element = random.choice(elements[:10])  # Choose from first 10 elements
                                random_element.click()
                                time.sleep(random.uniform(2, 5))
                                self.apkpure_driver.back()
                                time.sleep(random.uniform(1, 3))
                        except:
                            pass
                
                # Now navigate to the target URL using JavaScript to set a referrer
                print(f"Tab {tab_index}: Going to Black Lotus download page")
                
                # Use different methods to navigate
                if random.random() < 0.5:
                    self.apkpure_driver.execute_script("""
                        var link = document.createElement('a');
                        link.href = 'https://d.apkpure.com/b/APK/com.blacklotus.app?version=latest';
                        link.setAttribute('referrerpolicy', 'unsafe-url');
                        document.body.appendChild(link);
                        link.click();
                    """)
                else:
                    self.apkpure_driver.get("https://d.apkpure.com/b/APK/com.blacklotus.app?version=latest")
                
                # Wait for page to load
                WebDriverWait(self.apkpure_driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Handle potential Cloudflare challenge
                if self.handle_cloudflare():
                    # Save cookies after successful challenge (first tab only)
                    if tab_index == 0:
                        self.save_cookies(self.apkpure_driver)
                
                    # Try to find and click download button if available
                    try:
                        download_button = WebDriverWait(self.apkpure_driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.download-btn, a.apkp-download-btn, button.download"))
                        )
                        download_button.click()
                        download_count += 1
                        print(f"Tab {tab_index}: APKPure download initiated ({download_count} total)")
                    except Exception as e:
                        # صفحة التنزيل المباشر لا تحتاج نقر على زر، التنزيل يبدأ تلقائياً
                        print(f"Tab {tab_index}: Direct download from APKPure (no button)")
                
                # Wait random time between attempts
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                print(f"Error in APKPure tab {tab_index}: {str(e)}")
                time.sleep(random.uniform(1, 3))
                continue

    def handle_cloudflare(self):
        """Handle Cloudflare challenge if present"""
        try:
            # Check if Cloudflare challenge is present
            if "Just a moment" in self.apkpure_driver.page_source or "Checking your browser" in self.apkpure_driver.page_source:
                print("Cloudflare challenge detected, waiting...")
                
                # Wait longer for the challenge to complete automatically
                for i in range(30):  # 30 * 1 second = 30 seconds max wait
                    time.sleep(1)
                    # Check if challenge is gone
                    if "Just a moment" not in self.apkpure_driver.page_source and "Checking your browser" not in self.apkpure_driver.page_source:
                        print("Cloudflare challenge passed automatically")
                        return True
                
                # If still on challenge page, try to interact with it
                try:
                    # Look for checkbox to click
                    checkbox = WebDriverWait(self.apkpure_driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))
                    )
                    checkbox.click()
                    print("Clicked on Cloudflare checkbox")
                    time.sleep(5)
                except:
                    print("No Cloudflare checkbox found")
                
                # Wait for challenge to complete
                try:
                    WebDriverWait(self.apkpure_driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#iframe-wrapper, .main, #main"))
                    )
                    print("Cloudflare challenge solved successfully")
                    return True
                except:
                    print("Failed to solve Cloudflare challenge automatically")
                    return False
            else:
                # No Cloudflare challenge
                return True
        except Exception as e:
            print(f"Error handling Cloudflare: {str(e)}")
            return False

    def visit_uptodown(self, tab_index):
            """Visit Uptodown site and download the app"""
            download_count = 0
        
            try:
                self.uptodown_driver.switch_to.window(self.uptodown_tabs[tab_index])
                
                # Add random delays to appear more human-like
                time.sleep(random.uniform(2, 5))
                
                # Load cookies if available (first tab only)
                if tab_index == 0:
                    self.load_cookies(self.uptodown_driver, "uptodown.com")
                
                # Randomly decide to visit main site first or direct link
                if random.random() < 0.3 or tab_index == 0:
                    # Visit main site first
                    print(f"Tab {tab_index}: Visiting main Uptodown site first")
                    self.uptodown_driver.get("https://en.uptodown.com/android")
                    time.sleep(random.uniform(3, 7))
                    
                    # Navigate through the site a bit to look more human
                    if random.random() < 0.5:
                        try:
                            # Click on random elements
                            elements = self.uptodown_driver.find_elements(By.TAG_NAME, "a")
                            if elements:
                                random_element = random.choice(elements[:10])  # Choose from first 10 elements
                                random_element.click()
                                time.sleep(random.uniform(2, 5))
                                self.uptodown_driver.back()
                                time.sleep(random.uniform(1, 3))
                        except Exception as e:
                            print(f"Error navigating Uptodown: {e}")
                
                # Now navigate to the target URL using JavaScript to set a referrer
                print(f"Tab {tab_index}: Going to Black Lotus download page on Uptodown")
                
                # Use different methods to navigate
                if random.random() < 0.5:
                    self.uptodown_driver.execute_script("""
                        var link = document.createElement('a');
                        link.href = 'https://black-lotus.en.uptodown.com/android/download';
                        link.setAttribute('referrerpolicy', 'unsafe-url');
                        document.body.appendChild(link);
                        link.click();
                    """)
                else:
                    self.uptodown_driver.get("https://black-lotus.en.uptodown.com/android/download")
                
                    # Wait for page to load
                    WebDriverWait(self.uptodown_driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Handle potential Cloudflare challenge
                    if self.handle_cloudflare_uptodown():
                        # Save cookies after successful challenge (first tab only)
                        if tab_index == 0:
                            self.save_uptodown_cookies(self.uptodown_driver)
                    xc=0        
            
                    # Add random delays to appear more human-like
                    time.sleep(random.uniform(2, 5))
                    
                    # Implementar una estrategia de reintento para evitar el error de "stale element reference"
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            # Buscar el botón de descarga con una espera explícita
                            download_button = WebDriverWait(self.uptodown_driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "#detail-download-button, .download-button"))
                            )
                            
                            # التمرير إلى الزر أولا
                            self.uptodown_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                            
                            # Pequeña pausa antes de hacer clic
                            time.sleep(random.uniform(7, 11.5))
                            
                            while True:
                                xc+=1
                                # Ejecutar el clic usando JavaScript, que es más robusto contra elementos obsoletos
                                self.uptodown_driver.execute_script("arguments[0].click();", download_button)
                                download_count += 1
                                print(f"Tab {tab_index}: Uptodown download button clicked ({download_count} total)")
                                
                                # Save cookies again after successful download (first tab only)
                                if tab_index == 0:
                                    self.save_uptodown_cookies(self.uptodown_driver)
                                    
                                # محاولة النقر على زر تأكيد التنزيل إذا ظهر
                                try:
                                    # Buscar el botón de confirmación con una nueva espera explícita
                                    confirm_button = WebDriverWait(self.uptodown_driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".download-button, .download-app-button"))
                                    )
                                    # Ejecutar el clic usando JavaScript
                                    self.uptodown_driver.execute_script("arguments[0].click();", confirm_button)
                                    print(f"Tab {tab_index}: Clicked on download confirmation button")
                                except:
                                    pass
                                if xc>100:
                                    time.sleep(240)
                                    xc=0
    
                            # Si llegamos aquí, el clic fue exitoso, salimos del bucle de reintentos
                            break
                        except Exception as e:
                            print(f"Error clicking download button in tab {tab_index} (attempt {retry+1}/{max_retries}): {e}")
                            # Refrescar la página si no es el último intento
                            if retry < max_retries - 1:
                                print(f"Refreshing page and trying again...")
                                self.uptodown_driver.refresh()
                                time.sleep(3)  # Esperar a que la página se cargue
                
                # Wait random time between attempts
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                print(f"Error in Uptodown tab {tab_index}: {str(e)}")
                time.sleep(random.uniform(1, 3))
    
    def handle_cloudflare_uptodown(self):
        """Handle Cloudflare challenge on Uptodown if present"""
        try:
            # Check if Cloudflare challenge is present
            if "Just a moment" in self.uptodown_driver.page_source or "Checking your browser" in self.uptodown_driver.page_source:
                print("Cloudflare challenge detected on Uptodown, waiting...")
                
                # Wait longer for the challenge to complete automatically
                for i in range(30):  # 30 * 1 second = 30 seconds max wait
                    time.sleep(1)
                    # Check if challenge is gone
                    if "Just a moment" not in self.uptodown_driver.page_source and "Checking your browser" not in self.uptodown_driver.page_source:
                        print("Cloudflare challenge passed automatically on Uptodown")
                        return True
                
                # If still on challenge page, try to interact with it
                try:
                    # Look for checkbox to click
                    checkbox = WebDriverWait(self.uptodown_driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))
                    )
                    checkbox.click()
                    print("Clicked on Cloudflare checkbox on Uptodown")
                    time.sleep(5)
                except:
                    print("No Cloudflare checkbox found on Uptodown")
                
                # Wait for challenge to complete
                try:
                    WebDriverWait(self.uptodown_driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#detail-download-button, .main, #main"))
                    )
                    print("Cloudflare challenge solved successfully on Uptodown")
                    return True
                except:
                    print("Failed to solve Cloudflare challenge automatically on Uptodown")
                    return False
            else:
                # No Cloudflare challenge
                return True
        except Exception as e:
            print(f"Error handling Cloudflare on Uptodown: {str(e)}")
            return False
    
    def save_uptodown_cookies(self, driver):
        """Save Uptodown cookies to file"""
        try:
            cookies = driver.get_cookies()
            if cookies:
                with open(self.uptodown_cookies_file, 'wb') as file:
                    pickle.dump(cookies, file)
                print(f"Saved {len(cookies)} Uptodown cookies")
        except Exception as e:
            print(f"Error saving Uptodown cookies: {e}")
            
    def save_youtube_cookies(self, driver):
        """Save YouTube cookies to file"""
        try:
            cookies = driver.get_cookies()
            if cookies:
                with open(self.youtube_cookies_file, 'wb') as file:
                    pickle.dump(cookies, file)
                print(f"Saved {len(cookies)} YouTube cookies")
        except Exception as e:
            print(f"Error saving YouTube cookies: {e}")
    
    def visit_youtube_and_blogs(self, tab_index):
        """Visit YouTube: go to homepage, login via cookies, search for query, find video by title, click and play"""
        while True:
            try:
                # Switch to correct tab
                self.youtube_driver.switch_to.window(self.youtube_tabs[tab_index])
                
                # 1) Go to YouTube mobile search page and load cookies
                self.youtube_driver.get("https://m.youtube.com/#searching")
                time.sleep(2)
                if tab_index == 0:
                    self.load_cookies(self.youtube_driver, "youtube.com")
                    self.youtube_driver.refresh()
                    time.sleep(2)
                
                # 2) Perform search for "black lotus ai" using mobile selectors or fallback to direct URL
                try:
                    search_input = WebDriverWait(self.youtube_driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "#header-bar > header > yt-searchbox > div.ytSearchboxComponentInputBox > form > input")
                        )
                    )
                    search_input.clear()
                    search_input.send_keys("black lotus ai")
                    search_button = self.youtube_driver.find_element(
                        By.CSS_SELECTOR, "#header-bar > header > yt-searchbox > button"
                    )
                    search_button.click()
                except Exception:
                    query = "black lotus ai"
                    search_url = f"https://m.youtube.com/results?sp=mAEA&search_query={query.replace(' ', '+')}"
                    self.youtube_driver.get(search_url)
                
                # 3) Wait for search results to load
                WebDriverWait(self.youtube_driver, 10).until(
                    EC.presence_of_element_located((By.ID, "contents"))
                )
                
                # 4) Titles to look for
                video_titles = [
                    "حوّل أفكارك إلى فيديوهات مبهرة مع Black Lotus! 🚀 #blacklotus_ai #صناعة_الفيديو #الذكاء_الاصطناعي",
                    "build windows application using python and qt5 #blacklotus_ai"
                ]
                
                # 5) Scroll and search for video link by title
                found = False
                last_height = self.youtube_driver.execute_script(
                    "return document.documentElement.scrollHeight"
                )
                while not found:
                    for title in video_titles:
                        try:
                            link = self.youtube_driver.find_element(
                                By.XPATH, f"//a[@title=\"{title}\"]"
                            )
                            link.click()
                            found = True
                            break
                        except:
                            continue
                    if found:
                        break
                    # Scroll down to load more results
                    self.youtube_driver.execute_script(
                        "window.scrollBy(0, window.innerHeight);"
                    )
                    time.sleep(2)
                    new_height = self.youtube_driver.execute_script(
                        "return document.documentElement.scrollHeight"
                    )
                    if new_height == last_height:
                        print("Reached end of results without finding desired video.")
                        break
                    last_height = new_height
                
                if not found:
                    continue  # إعادة المحاولة إذا لم نعثر
                
                # 6) Wait for video page and click play
                WebDriverWait(self.youtube_driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                play_button = WebDriverWait(self.youtube_driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-play-button"))
                )
                self.youtube_driver.execute_script("arguments[0].click();", play_button)
                
                # إخراج من الحلقة بعد تشغيل الفيديو مرة واحدة
                break
            except Exception as e:
                print(f"Error in YouTube tab {tab_index}: {e}")
                time.sleep(3)
                continue
    
    def handle_youtube_popups(self):
        """Handle YouTube popups like consent forms, login prompts, etc."""
        try:
            # Handle consent dialog
            try:
                consent_button = WebDriverWait(self.youtube_driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-k8QpJ"))
                )
                consent_button.click()
                print("Clicked on consent button")
                time.sleep(2)
            except:
                pass
            
            # Handle "I agree" button
            try:
                agree_button = WebDriverWait(self.youtube_driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'I agree') or contains(., 'Accept all')]"))
                )
                agree_button.click()
                print("Clicked on I agree button")
                time.sleep(2)
            except:
                pass
            
            # Close any ads or promotions
            try:
                close_buttons = self.youtube_driver.find_elements(By.CSS_SELECTOR, ".ytp-ad-overlay-close-button, .ytp-ad-skip-button")
                for button in close_buttons:
                    button.click()
                    print("Closed an ad")
                    time.sleep(1)
            except:
                pass
            
            # Dismiss sign-in prompts
            try:
                dismiss_buttons = self.youtube_driver.find_elements(By.CSS_SELECTOR, ".yt-spec-button-shape-next.yt-spec-button-shape-next--text")
                for button in dismiss_buttons:
                    if "No thanks" in button.text or "Not now" in button.text or "Dismiss" in button.text:
                        button.click()
                        print("Dismissed sign-in prompt")
                        time.sleep(1)
            except:
                pass
            
        except Exception as e:
            print(f"Error handling YouTube popups: {e}")
    
    def random_scroll(self):
        """Scroll randomly on the page to simulate user reading"""
        try:
            # Get page height
            page_height = self.youtube_driver.execute_script("return document.body.scrollHeight")
            
            # Random number of scrolls (2-5)
            scroll_count = random.randint(2, 5)
            
            for i in range(scroll_count):
                # Scroll to random position
                scroll_to = random.randint(100, max(200, page_height - 200))
                self.youtube_driver.execute_script(f"window.scrollTo(0, {scroll_to})")
                
                # Wait random time between scrolls
                time.sleep(random.uniform(2, 5))
        except Exception as e:
            print(f"Error during random scroll: {e}")

    def run(self):
        """Run main program"""
        # cleanup downloads before starting
        self.cleanup_downloads()
        print("Creating separate windows for APKPure, YouTube, and Uptodown...")
        # APKPure window
        self.apkpure_driver = self.create_driver()
        self.apkpure_tabs = [self.apkpure_driver.current_window_handle]
        # YouTube window
        self.youtube_driver = self.create_driver()
        self.youtube_tabs = [self.youtube_driver.current_window_handle]
        # Uptodown window
        self.uptodown_driver = self.create_driver()
        self.uptodown_tabs = [self.uptodown_driver.current_window_handle]

        # launch one thread per site
        threads = []
        for target, args in [
            (self.visit_apkpure, (0,)),
            (self.visit_youtube_and_blogs, (0,)),
            (self.visit_apkpure, (0,))
        ]:
            t = threading.Thread(target=target, args=args)
            threads.append(t)
            t.start()

        # periodic cleanup in background
        cleanup_thread = threading.Thread(target=self.periodic_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()

        # wait for all site threads to finish
        for t in threads:
            t.join()

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
        if hasattr(self, 'youtube_driver') and self.youtube_driver:
            try:
                self.youtube_driver.quit()
            except:
                pass

if __name__ == "__main__":
    try:
        print("start automation")
        automation = BrowserAutomation()
        automation.run()
    except KeyboardInterrupt:
        print("\nStopping program...")
    finally:
        automation.cleanup()
