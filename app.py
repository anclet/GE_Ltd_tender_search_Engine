

# # Combined Tender Scraping System - Merging Two Approaches
# import gradio as gr
# import pandas as pd
# import os
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# import re
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import time
# from datetime import datetime, timedelta
# import numpy as np
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import nltk
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
# import warnings
# warnings.filterwarnings('ignore')

# # Optional Selenium imports
# try:
#     from selenium import webdriver
#     from selenium.webdriver.common.by import By
#     from selenium.webdriver.support.ui import WebDriverWait
#     from selenium.webdriver.support import expected_conditions as EC
#     from selenium.common.exceptions import TimeoutException, NoSuchElementException
#     SELENIUM_AVAILABLE = True
# except ImportError:
#     SELENIUM_AVAILABLE = False

# # Download NLTK data if not already present
# try:
#     nltk.data.find('tokenizers/punkt')
# except LookupError:
#     nltk.download('punkt')
# try:
#     nltk.data.find('corpora/stopwords')
# except LookupError:
#     nltk.download('stopwords')

# # ============================================================================
# # SCRAPING METHOD 1: Original BeautifulSoup Method (Unchanged)
# # ============================================================================

# def scrape_all_links_to_dataframe(base_url):
#     try:
#         visited_links = set()
#         all_tenders = []

#         print(f"Scraping base URL: {base_url}")
#         html_content = fetch_page_content(base_url)
#         if html_content:
#             soup = BeautifulSoup(html_content, "html.parser")
#             tenders = extract_tender_data(soup, base_url)
#             all_tenders.extend(tenders)
#             visited_links.add(base_url)

#             links = extract_internal_links(base_url, soup)
#             for link in links:
#                 if link not in visited_links:
#                     page_content = fetch_page_content(link)

#         if all_tenders:
#             df = pd.DataFrame(all_tenders)
#             df = df.drop_duplicates(subset=['title', 'link'], keep='first')
#             df = df.reset_index(drop=True)
#             return df
#         else:
#             return pd.DataFrame(columns=['title', 'link', 'deadline'])

#     except Exception as e:
#         print(f"Error during scraping: {e}")
#         return pd.DataFrame(columns=['title', 'link', 'deadline'])

# def extract_tender_data(soup, current_url):
#     tenders = []

#     unwanted_selectors = [
#         'nav', 'header', 'footer', 'sidebar', '.menu', '.navigation',
#         '.footer', '.header', '.sidebar', '#menu', '#navigation',
#         '#footer', '#header', '#sidebar', '.social', '.contact-info'
#     ]

#     for selector in unwanted_selectors:
#         for element in soup.select(selector):
#             element.decompose()

#     tender_selectors = [
#         {'tag': 'div', 'class': re.compile(r'tender|job|listing|post|item', re.I)},
#         {'tag': 'article', 'class': re.compile(r'tender|job|post', re.I)},
#         {'tag': 'tr', 'class': re.compile(r'tender|row', re.I)},
#         {'tag': 'li', 'class': re.compile(r'tender|job|item', re.I)},
#     ]

#     tender_containers = []
#     for selector in tender_selectors:
#         containers = soup.find_all(selector['tag'], class_=selector['class'])
#         tender_containers.extend(containers)

#     if not tender_containers:
#         main_content = soup.find('main') or soup.find('div', class_=re.compile(r'content|main', re.I))
#         if main_content:
#             tender_containers = main_content.find_all('a', href=True)
#         else:
#             tender_containers = soup.find_all('a', href=True)

#     for container in tender_containers:
#         if is_unwanted_content(container):
#             continue

#         tender_info = {}
#         title = extract_title(container)
#         if not title or len(title.strip()) < 5:
#             continue

#         if not is_tender_title(title):
#             continue

#         tender_info['title'] = title.strip()
#         link = extract_link(container, current_url)

#         if not is_tender_link(link):
#             continue

#         tender_info['link'] = link
#         deadline = extract_deadline(container)
#         tender_info['deadline'] = deadline

#         if (tender_info['title'] and
#             tender_info['deadline'] != "Not specified" and
#             tender_info['link'] != "No link available" and
#             is_valid_tender_entry(tender_info)):
#             tenders.append(tender_info)

#     return tenders

# def is_unwanted_content(container):
#     unwanted_keywords = [
#         'navigation', 'menu', 'footer', 'header', 'sidebar', 'contact',
#         'about', 'social', 'copyright', 'terms', 'privacy', 'testimonial',
#         'breadcrumb', 'pagination', 'filter', 'search-form'
#     ]

#     container_class = ' '.join(container.get('class', [])).lower()
#     container_id = container.get('id', '').lower()

#     for keyword in unwanted_keywords:
#         if keyword in container_class or keyword in container_id:
#             return True

#     parent = container.parent
#     while parent and parent.name != 'body':
#         parent_class = ' '.join(parent.get('class', [])).lower()
#         parent_id = parent.get('id', '').lower()

#         for keyword in unwanted_keywords:
#             if keyword in parent_class or keyword in parent_id:
#                 return True
#         parent = parent.parent

#     return False

# def is_tender_title(title):
#     title_lower = title.lower()

#     skip_keywords = [
#         'post advert', 'hr service', 'employers', 'testimonials', 'about us',
#         'contact us', 'featured', 'jobs', 'tenders', 'consultancy', 'internships',
#         'public', 'others', 'job in rwanda', 'kg 611', 'info@', 'published jobs',
#         'registered', 'home', 'login', 'register', 'search', 'apply', 'browse',
#         'categories', 'locations', 'salary', 'experience', 'education', 'skills',
#         'follow us', 'social media', 'facebook', 'twitter', 'linkedin', 'instagram',
#         '+250', 'phone', 'email', 'address', 'contact info', 'site map', 'help',
#         'faq', 'support', 'privacy policy', 'terms of service', 'copyright'
#     ]

#     for keyword in skip_keywords:
#         if keyword in title_lower:
#             return False

#     if re.search(r'^(featured|jobs|tenders|consultancy|internships|public|others)\d+$', title_lower):
#         return False

#     if re.search(r'^\+?\d+[\d\s\-\(\)]+$', title.strip()):
#         return False
#     if '@' in title and len(title) < 30:
#         return False
#     if re.search(r'kg\s*\d+', title_lower):
#         return False

#     if len(title.strip()) < 15 or title.strip().isdigit():
#         return False

#     tender_keywords = [
#         'tender notice', 'tender for', 'supply of', 'construction of', 'provision of',
#         'consultancy services', 'request for proposal', 'rfp', 'procurement',
#         'bidding', 'contract for', 'services for', 'works for', 'job', 'hiring', 
#         'expresssion of interest', 'EoI', 'terms of reference', 'ToR', 'market']

#     for keyword in tender_keywords:
#         if keyword in title_lower:
#             return True

#     if (len(title.strip()) > 25 and
#         not any(skip in title_lower for skip in skip_keywords) and
#         not re.search(r'^\w+\d+$', title.strip())):
#         return True

#     return False

# def is_valid_tender_entry(tender_info):
#     title = tender_info['title'].lower()
#     link = tender_info['link'].lower()

#     if re.search(r'^(featured|jobs|tenders|consultancy|internships|public|others)\d+$', title):
#         return False

#     if any(contact in title for contact in ['@', 'kg 611', '+250', 'published jobs', 'registered']):
#         return False

#     if not any(pattern in link for pattern in ['/job/', '/tender/', '/vacancy/', '/opportunity/']):
#         return False

#     category_endings = ['/jobs/all', '/jobs/featured', '/jobs/tender', '/jobs/consultancy',
#                        '/jobs/internships', '/jobs/public-adverts', '/jobs/others']
#     if any(link.endswith(ending) for ending in category_endings):
#         return False

#     return True

# def is_tender_link(link):
#     if link == "No link available":
#         return False

#     link_lower = link.lower()

#     skip_patterns = [
#         '/post-advert', '/all-employers', '/testimonials', '/about', '/contact',
#         '/jobs/all', '/jobs/featured', '/jobs/internships', '/jobs/consultancy',
#         '/jobs/public-adverts', '/jobs/others', '/page/', '/help', '/support',
#         'hrms.rw', 'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
#         '/privacy', '/terms', '/sitemap', '/faq'
#     ]

#     for pattern in skip_patterns:
#         if pattern in link_lower:
#             return False

#     accept_patterns = [
#         '/job/', '/tender/', '/vacancy/', '/opportunity/'
#     ]

#     found_pattern = False
#     for pattern in accept_patterns:
#         if pattern in link_lower:
#             found_pattern = True
#             break

#     if not found_pattern:
#         return False

#     if link_lower.endswith('/tender') or link_lower.endswith('/tenders'):
#         return False
#     if link_lower.endswith('/jobs') or link_lower.endswith('/job'):
#         return False

#     return True

# def extract_title(container):
#     title_selectors = [
#         {'tag': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 'class': None},
#         {'tag': ['a'], 'class': re.compile(r'title|heading|name', re.I)},
#         {'tag': ['span', 'div'], 'class': re.compile(r'title|heading|name', re.I)},
#         {'tag': ['a'], 'class': None},
#     ]

#     for selector in title_selectors:
#         if selector['class']:
#             elements = container.find_all(selector['tag'], class_=selector['class'])
#         else:
#             elements = container.find_all(selector['tag'])

#         for element in elements:
#             text = element.get_text(strip=True)
#             if text and len(text) > 5:
#                 return text[:150]

#     if container.name == 'a':
#         return container.get_text(strip=True)[:150]

#     text = container.get_text(strip=True)
#     if len(text) > 10:
#         first_sentence = text.split('.')[0]
#         return first_sentence[:150] if len(first_sentence) < 200 else text[:150]

#     return None

# def extract_link(container, base_url):
#     link_element = container.find('a', href=True)

#     if link_element:
#         href = link_element['href']
#         return urljoin(base_url, href)
#     elif container.name == 'a' and container.get('href'):
#         href = container['href']
#         return urljoin(base_url, href)
#     else:
#         return "No link available"

# def extract_deadline(container):
#     container_text = container.get_text()

#     deadline_patterns = [
#         r'deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
#         r'due[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
#         r'closing[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
#         r'submit by[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
#         r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
#         r'(\d{4}-\d{1,2}-\d{1,2})',
#         r'(\d{1,2}[/-]\d{1,2}[/-]\d{2})',
#         r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})',
#         r'(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})'
#     ]

#     for pattern in deadline_patterns:
#         match = re.search(pattern, container_text, re.IGNORECASE)
#         if match:
#             return match.group(1)

#     return "Not specified"

# def fetch_page_content(url):
#     try:
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         }
#         response = requests.get(url, timeout=10, headers=headers)
#         response.raise_for_status()
#         return response.text
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching {url}: {e}")
#         return None

# def extract_internal_links(base_url, soup):
#     links = set()
#     for anchor in soup.find_all("a", href=True):
#         href = anchor["href"]
#         full_url = urljoin(base_url, href)
#         if is_internal_link(base_url, full_url):
#             links.add(full_url)
#     return links

# def is_internal_link(base_url, link_url):
#     base_netloc = urlparse(base_url).netloc
#     link_netloc = urlparse(link_url).netloc
#     return base_netloc == link_netloc

# def scrape_single_url(base_url):
#     print(f"Starting scraping for: {base_url}")
#     df = scrape_all_links_to_dataframe(base_url)
#     print(f"Completed scraping for: {base_url}, Found {len(df)} tenders.")
#     return base_url, df

# def scrape_multiple_urls_parallel(urls, max_workers=3):
#     all_dfs = []
#     failed_urls = []

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         future_to_url = {executor.submit(scrape_single_url, url): url for url in urls}

#         for future in as_completed(future_to_url):
#             url = future_to_url[future]
#             try:
#                 base_url, df = future.result()
#                 if not df.empty:
#                     all_dfs.append(df)
#                 else:
#                     print(f"No valid tenders extracted from: {base_url}")
#             except Exception as e:
#                 print(f"Error scraping {url}: {e}")
#                 failed_urls.append(url)

#     if all_dfs:
#         combined_df = pd.concat(all_dfs, ignore_index=True)
#         combined_df = combined_df.drop_duplicates(subset=['title', 'link'], keep='first')
#         combined_df = combined_df.reset_index(drop=True)
#     else:
#         combined_df = pd.DataFrame(columns=['title', 'link', 'deadline'])

#     print(f"\nScraping completed. Total unique tenders found: {len(combined_df)}")
#     if failed_urls:
#         print(f"Failed URLs: {failed_urls}")

#     return combined_df

# # ============================================================================
# # SCRAPING METHOD 2: Umucyo Selenium Method (Unchanged)
# # ============================================================================

# class UmucyoTendersScraper:
#     """
#     Original Umucyo scraper - unchanged
#     """

#     def __init__(self, driver_path=None, headless=True):
#         if not SELENIUM_AVAILABLE:
#             raise ImportError("Selenium not installed")
            
#         options = webdriver.ChromeOptions()
#         if headless:
#             options.add_argument('--headless')
#         options.add_argument('--disable-gpu')
#         options.add_argument('--no-sandbox')
#         options.add_argument('--disable-dev-shm-usage')
#         options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

#         if driver_path:
#             self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
#         else:
#             self.driver = webdriver.Chrome(options=options)

#         self.driver.set_page_load_timeout(30)
#         self.driver.implicitly_wait(10)

#         self.base_url = "https://www.umucyo.gov.rw"
#         self.tenders_url = "https://www.umucyo.gov.rw/eb/bav/selectListAdvertisingListForGU.do?menuId=EB01020100&leftTopFlag=l"

#         self.data = []

#     def _wait_for_page_load(self, timeout=15):
#         """Wait for page to fully load"""
#         try:
#             WebDriverWait(self.driver, timeout).until(
#                 lambda driver: driver.execute_script("return document.readyState") == "complete"
#             )
#         except TimeoutException:
#             print("Page load timeout - continuing anyway")

#     def _extract_tender_rows_from_table(self):
#         """Extract tender data from the main table"""
#         tender_rows = []

#         try:
#             soup = BeautifulSoup(self.driver.page_source, 'html.parser')
#             tables = soup.find_all('table')

#             for table_idx, table in enumerate(tables):
#                 rows = table.find_all('tr')

#                 if len(rows) < 2:
#                     continue

#                 header_row = None
#                 data_rows = []

#                 for row_idx, row in enumerate(rows):
#                     cells = row.find_all(['td', 'th'])
#                     if len(cells) >= 3:
#                         if row_idx == 0 or row.find_all('th'):
#                             header_row = [cell.get_text(strip=True) for cell in cells]
#                         else:
#                             data_rows.append(cells)

#                 for row in data_rows:
#                     try:
#                         tender_data = self._extract_tender_data_from_row(row, header_row)
#                         if tender_data:
#                             tender_rows.append(tender_data)
#                     except Exception as e:
#                         print(f"Error processing row: {e}")
#                         continue

#                 if tender_rows:
#                     break

#         except Exception as e:
#             print(f"Error extracting table data: {e}")

#         return tender_rows

#     def _extract_tender_data_from_row(self, row_cells, header_row=None):
#         """Extract tender information from a table row"""
#         try:
#             cell_texts = [cell.get_text(strip=True) for cell in row_cells]

#             if len(cell_texts) < 3 or all(not text for text in cell_texts):
#                 return None

#             # Extract tender link
#             tender_link = None
#             for cell in row_cells:
#                 cell_links = cell.find_all('a', href=True)
#                 for link in cell_links:
#                     href = link.get('href')
#                     if href:
#                         if href.startswith('/'):
#                             tender_link = self.base_url + href
#                         elif not href.startswith('http'):
#                             tender_link = self.base_url + '/' + href
#                         else:
#                             tender_link = href
#                         break
#                 if tender_link:
#                     break

#             # Extract dates
#             dates = self._extract_all_dates(cell_texts)
            
#             advertising_date = dates[0] if len(dates) > 0 else None
#             deadline_date = dates[1] if len(dates) > 1 else None
#             planned_open_date = dates[2] if len(dates) > 2 else None

#             # Extract tender name
#             tender_name = self._extract_tender_name(row_cells, cell_texts)

#             tender_data = {
#                 'tender_name': tender_name,
#                 'advertising_date': advertising_date,
#                 'deadline_of_submitting': deadline_date,
#                 'planned_open_date': planned_open_date,
#                 'tender_link': tender_link
#             }

#             return tender_data

#         except Exception as e:
#             print(f"Error extracting tender data from row: {e}")
#             return None

#     def _extract_tender_name(self, row_cells, cell_texts):
#         """Extract tender name from row"""
#         for cell in row_cells:
#             links = cell.find_all('a', href=True)
#             for link in links:
#                 link_text = link.get_text(strip=True)
#                 if len(link_text) > 10 and not self._is_date_string(link_text):
#                     return link_text
        
#         candidate = ""
#         for text in cell_texts:
#             if len(text) > len(candidate) and len(text) > 10 and not self._is_date_string(text):
#                 if text.upper() not in ['OPEN', 'CLOSED', 'CANCELLED', 'AWARDED', 'PENDING']:
#                     candidate = text
        
#         return candidate if candidate else "N/A"

#     def _extract_all_dates(self, cell_texts):
#         """Extract all dates from cell texts"""
#         date_patterns = [
#             r'\d{2}/\d{2}/\d{4}',
#             r'\d{4}-\d{2}-\d{2}',
#             r'\d{2}-\d{2}-\d{4}',
#             r'\d{1,2}\s+\w+\s+\d{4}'
#         ]

#         dates_found = []
#         for text in cell_texts:
#             for pattern in date_patterns:
#                 matches = re.findall(pattern, text)
#                 for match in matches:
#                     if match not in dates_found:
#                         dates_found.append(match)

#         return dates_found

#     def _is_date_string(self, text):
#         """Check if text looks like a date"""
#         date_patterns = [
#             r'\d{2}/\d{2}/\d{4}',
#             r'\d{4}-\d{2}-\d{2}',
#             r'\d{2}-\d{2}-\d{4}'
#         ]
#         return any(re.search(pattern, text) for pattern in date_patterns)

#     def _check_for_next_page(self):
#         """Check if there's a next page and navigate to it"""
#         try:
#             next_buttons = self.driver.find_elements(By.XPATH,
#                 "//a[contains(text(), 'Next') or contains(text(), '다음') or contains(text(), '>')]")

#             for button in next_buttons:
#                 if button.is_enabled() and button.is_displayed():
#                     button.click()
#                     self._wait_for_page_load()
#                     return True

#             page_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'page') or contains(@href, 'Page')]")
#             current_page_text = self.driver.find_element(By.TAG_NAME, 'body').text

#             for link in page_links:
#                 link_text = link.text.strip()
#                 if link_text.isdigit() and link_text not in current_page_text:
#                     link.click()
#                     self._wait_for_page_load()
#                     return True

#         except (NoSuchElementException, TimeoutException):
#             pass

#         return False

#     def scrape(self, max_pages=10):
#         """Main scraping method"""
#         print("Starting Umucyo tenders scraping...")

#         try:
#             print(f"Navigating to {self.tenders_url}")
#             self.driver.get(self.tenders_url)
#             self._wait_for_page_load()

#             page_count = 0

#             while page_count < max_pages:
#                 print(f"Scraping page {page_count + 1}")

#                 page_tenders = self._extract_tender_rows_from_table()
#                 print(f"Found {len(page_tenders)} tenders on page {page_count + 1}")

#                 for idx, tender in enumerate(page_tenders):
#                     try:
#                         self.data.append(tender)
#                         print(f"Processed tender {idx + 1}: {tender.get('tender_name', 'Unknown')}")

#                     except Exception as e:
#                         print(f"Error processing tender {idx + 1}: {e}")
#                         continue

#                 if not self._check_for_next_page():
#                     print("No more pages found")
#                     break

#                 page_count += 1
#                 time.sleep(2)

#         except Exception as e:
#             print(f"Error during scraping process: {e}")
#         finally:
#             self.driver.quit()

#         print(f"Scraping completed. Total tenders collected: {len(self.data)}")
#         return self.data

# # ============================================================================
# # MERGE FUNCTION: Combines outputs from both scrapers
# # ============================================================================

# def merge_scraped_data(method1_df,method0_df, method2_data):
#     """
#     Merges data from both scraping methods into single DataFrame
    
#     Args:
#         method1_df: DataFrame from BeautifulSoup scraper (title, link, deadline)
#         method2_data: List of dicts from Umucyo scraper
    
#     Returns:
#         Combined DataFrame with standardized columns
#     """
#     # Convert Method 2 data to DataFrame
#     if method2_data:
#         method2_df = pd.DataFrame(method2_data)
        
#         # Standardize column names to match Method 1
#         method2_df = method2_df.rename(columns={
#             'tender_name': 'title',
#             'tender_link': 'link',
#             'deadline_of_submitting': 'deadline'
#         })
        
#         # Keep only standard columns, add extra info as metadata
#         method2_df['source'] = 'umucyo.gov.rw'
#         if 'advertising_date' in method2_df.columns:
#             method2_df['extra_info'] = method2_df.apply(
#                 lambda x: f"Advertised: {x.get('advertising_date', 'N/A')}, Opens: {x.get('planned_open_date', 'N/A')}", 
#                 axis=1
#             )
#     else:
#         method2_df = pd.DataFrame(columns=['title', 'link', 'deadline'])
    
#     # Add source to Method 1 data
#     method0_df['source'] = 'rwandatenders'
#     method0_df['extra_info'] = ''
#     method1_df['source'] = 'jobinrwanda'
#     method1_df['extra_info'] = ''
    
#     # Combine both dataframes
#     combined_df = pd.concat([method1_df,method0_df, method2_df], ignore_index=True)
    
#     # Remove duplicates based on title and link
#     combined_df = combined_df.drop_duplicates(subset=['title', 'link'], keep='first')
#     combined_df = combined_df.reset_index(drop=True)
    
#     return combined_df

# # ============================================================================
# # SEARCH ENGINE (From original code - unchanged)
# # ============================================================================

# class TenderSearchEngine:
#     def __init__(self):
#         self.df = pd.DataFrame()
#         self.vectorizer = TfidfVectorizer(stop_words='english', max_features=3000)
#         self.tfidf_matrix = None

#     def load_data(self, df):
#         """Load scraped data and prepare for search"""
#         self.df = df.copy()
#         if not df.empty:
#             search_text = df['title'].fillna('').astype(str)
#             self.tfidf_matrix = self.vectorizer.fit_transform(search_text)

#     def categorize_tender(self, title):
#         """Automatically categorize tenders"""
#         title_lower = title.lower()

#         categories = {
#             'Construction': ['construction', 'building', 'road', 'infrastructure', 'bridge', 'renovation'],
#             'IT/Technology': ['software', 'it', 'technology', 'system', 'database', 'network', 'computer'],
#             'Medical/Health': ['medical', 'health', 'hospital', 'clinic', 'equipment', 'pharmaceutical'],
#             'Education': ['school', 'university', 'education', 'training', 'academic', 'student'],
#             'Consultancy': ['consultancy', 'consulting', 'advisory', 'assessment', 'evaluation'],
#             'Supply': ['supply', 'procurement', 'purchase', 'equipment', 'materials', 'goods'],
#             'Services': ['services', 'maintenance', 'cleaning', 'security', 'catering'],
#             'Agriculture': ['agriculture', 'farming', 'crop', 'livestock', 'irrigation'],
#             'Transport': ['transport', 'vehicle', 'logistics', 'shipping', 'delivery'],
#             'Energy': ['energy', 'electricity', 'power', 'solar', 'generator', 'renewable'],
#             'Water': ['water', 'sanitation', 'drinking water', 'wastewater', 'hydro'],
#             'Environment': ['environment', 'conservation', 'sustainability', 'biodiversity'],
#             'Safety': ['safety', 'occupational health', 'hse', 'risk assessment'],
#             'Mining': ['mining', 'mineral', 'ore', 'quarry', 'extraction'],
#             'Air Quality': ['air quality', 'emissions', 'particulate matter', 'monitoring']
#         }

#         for category, keywords in categories.items():
#             if any(keyword in title_lower for keyword in keywords):
#                 return category
#         return 'Other'

#     def get_urgency_level(self, deadline_str):
#         """Determine urgency based on deadline"""
#         if deadline_str == "Not specified":
#             return "Unknown"

#         try:
#             for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y']:
#                 try:
#                     deadline = datetime.strptime(deadline_str, fmt)
#                     break
#                 except ValueError:
#                     continue
#             else:
#                 return "Unknown"

#             days_left = (deadline - datetime.now()).days

#             if days_left < 0:
#                 return "Expired"
#             elif days_left <= 3:
#                 return "Critical"
#             elif days_left <= 7:
#                 return "Urgent"
#             elif days_left <= 14:
#                 return "Medium"
#             else:
#                 return "Low"
#         except:
#             return "Unknown"

#     def smart_search(self, query, category_filter="All", urgency_filter="All", limit=20):
#         """Intelligent search with ranking and filtering"""
#         if self.df.empty:
#             return pd.DataFrame()

#         df_filtered = self.df.copy()

#         # Add categories and urgency
#         df_filtered['category'] = df_filtered['title'].apply(self.categorize_tender)
#         df_filtered['urgency'] = df_filtered['deadline'].apply(self.get_urgency_level)

#         # Apply filters
#         if category_filter != "All":
#             df_filtered = df_filtered[df_filtered['category'] == category_filter]

#         if urgency_filter != "All":
#             df_filtered = df_filtered[df_filtered['urgency'] == urgency_filter]

#         if query.strip():
#             query_vec = self.vectorizer.transform([query])
#             filtered_indices = df_filtered.index.tolist()
#             if filtered_indices:
#                 filtered_tfidf = self.tfidf_matrix[filtered_indices]
#                 scores = cosine_similarity(query_vec, filtered_tfidf).flatten()
#                 df_filtered = df_filtered.iloc[np.argsort(scores)[::-1]]
#                 df_filtered['relevance_score'] = sorted(scores, reverse=True)
#                 df_filtered = df_filtered[df_filtered['relevance_score'] > 0.1]

#         return df_filtered.head(limit)

#     def get_statistics(self):
#         """Generate summary statistics"""
#         if self.df.empty:
#             return {}

#         df_temp = self.df.copy()
#         df_temp['category'] = df_temp['title'].apply(self.categorize_tender)
#         df_temp['urgency'] = df_temp['deadline'].apply(self.get_urgency_level)

#         stats = {
#             'total_tenders': len(df_temp),
#             'categories': df_temp['category'].value_counts().to_dict(),
#             'urgency_levels': df_temp['urgency'].value_counts().to_dict(),
#             'with_deadlines': len(df_temp[df_temp['deadline'] != 'Not specified']),
#             'sources': df_temp['source'].value_counts().to_dict() if 'source' in df_temp.columns else {}
#         }

#         return stats

# search_engine = TenderSearchEngine()

# # ============================================================================
# # GRADIO INTERFACE FUNCTIONS
# # ============================================================================

# def perform_combined_scraping(include_umucyo, progress=gr.Progress()):
#     """
#     Scrapes using both methods and merges the results
#     """
#     progress(0.1, desc="Starting BeautifulSoup scraping...")
    
#     # Method 1: BeautifulSoup scraping
#     websites = [
#         "https://www.jobinrwanda.com/jobs/consultancy",
#         "https://www.jobinrwanda.com/jobs/tender",
#         "https://www.jobinrwanda.com/jobs/all"
#     ]

#     websites_0 = [
#         "https://www.rwandatenders.com/tenders.php"
#     ]
    
#     try:
#         start_time = time.time()
#         method1_df = scrape_multiple_urls_parallel(websites, max_workers=3)
#         progress(0.5, desc=f"Method 1 complete: {len(method1_df)} tenders found")
#         method0_df = scrape_multiple_urls_parallel(websites_0, max_workers=3)
#         progress(0.6, desc=f"Method 1 complete: {len(method0_df)} tenders found")
        
#         # Method 2: Umucyo Selenium scraping (optional)
#         method2_data = []
#         if include_umucyo and SELENIUM_AVAILABLE:
#             progress(0.8, desc="Starting Umucyo scraping (may take longer)...")
#             try:
#                 umucyo_scraper = UmucyoTendersScraper(headless=True)
#                 method2_data = umucyo_scraper.scrape(max_pages=5)
#                 progress(0.85, desc=f"Method 2 complete: {len(method2_data)} tenders found")
#             except Exception as e:
#                 print(f"Umucyo scraping error: {e}")
#         elif include_umucyo and not SELENIUM_AVAILABLE:
#             print("Selenium not available - skipping Umucyo")
        
#         progress(0.9, desc="Merging data from all sources...")
        
#         # MERGE THE TWO METHODS
#         final_df = merge_scraped_data(method1_df,method0_df, method2_data)
        
#         # Load into search engine
#         search_engine.load_data(final_df)
        
#         execution_time = time.time() - start_time

#         if final_df.empty:
#             return "No tenders found. Please check the websites.", pd.DataFrame(), {}

#         # Generate summary
#         stats = search_engine.get_statistics()
#         summary = f"""
# ✅ **Scraping Completed Successfully!**

# **Summary:**
# - Total Tenders Found: {stats['total_tenders']}
# - Tenders with Deadlines: {stats['with_deadlines']}
# - Execution Time: {execution_time:.2f} seconds

# **Sources:**
# """
#         for source, count in stats.get('sources', {}).items():
#             summary += f"\n- {source}: {count} tenders"

#         summary += "\n\n**Categories Found:**"
#         for category, count in stats['categories'].items():
#             summary += f"\n- {category}: {count}"

#         summary += "\n\n**Use the search panel to find specific tenders**"

#         progress(1.0, desc="Complete!")

#         return summary, create_display_dataframe(final_df), final_df.to_dict('records')

#     except Exception as e:
#         return f"❌ Error during scraping: {str(e)}", pd.DataFrame(), {}

# def search_tenders(query, category_filter, urgency_filter, scraped_data):
#     """Search through scraped tenders"""
#     if not scraped_data:
#         return "⚠️ No data available. Please scrape first.", pd.DataFrame()

#     try:
#         df = pd.DataFrame(scraped_data)
#         search_engine.load_data(df)

#         results = search_engine.smart_search(query, category_filter, urgency_filter)

#         if results.empty:
#             return "🔍 No tenders found matching your criteria.", pd.DataFrame()

#         summary = f"🎯 **Found {len(results)} matching tenders**\n\n"

#         if query.strip():
#             summary += f"**Search Query:** '{query}'\n"
#         if category_filter != "All":
#             summary += f"**Category Filter:** {category_filter}\n"
#         if urgency_filter != "All":
#             summary += f"**Urgency Filter:** {urgency_filter}\n"

#         return summary, create_display_dataframe(results)

#     except Exception as e:
#         return f"❌ Search error: {str(e)}", pd.DataFrame()

# def create_display_dataframe(df):
#     """Create a formatted dataframe for display"""
#     if df.empty:
#         return pd.DataFrame()

#     display_df = df.copy()

#     if 'category' not in display_df.columns:
#         display_df['category'] = display_df['title'].apply(search_engine.categorize_tender)
#     if 'urgency' not in display_df.columns:
#         display_df['urgency'] = display_df['deadline'].apply(search_engine.get_urgency_level)

#     columns_order = ['title', 'category', 'deadline', 'urgency', 'source', 'link']
#     display_df = display_df[[col for col in columns_order if col in display_df.columns]]

#     if 'title' in display_df.columns:
#         display_df['title'] = display_df['title'].apply(lambda x: x[:80] + "..." if len(x) > 80 else x)

#     # Format links as clickable HTML
#     if 'link' in display_df.columns:
#         display_df['link'] = display_df['link'].apply(
#             lambda x: f'<a href="{x}" target="_blank">Open Link</a>' if x and x != "No link available" else "N/A"
#         )

#     return display_df

# # ============================================================================
# # CREATE GRADIO INTERFACE
# # ============================================================================

# def create_interface():
#     with gr.Blocks(title="Combined Tender Scraping System", theme=gr.themes.Soft()) as demo:
#         gr.Markdown("""
#         # Combined Rwanda Tender Scraping System
        
#         This system merges two scraping methodologies:
#         - **Method 1**: BeautifulSoup scraping (JobInRwanda, RwandaTenders)
#         - **Method 2**: Selenium scraping (Umucyo Government Portal)
        
#         All results are combined into a single searchable database.
#         """)

#         scraped_data_state = gr.State([])

#         with gr.Tab("🔍 Data Scraping"):
#             gr.Markdown("### Scrape Latest Tender Data from All Sources")

#             include_umucyo_checkbox = gr.Checkbox(
#                 label="Include Umucyo.gov.rw (Requires Selenium, slower but gets government tenders)",
#                 value=SELENIUM_AVAILABLE,
#                 interactive=SELENIUM_AVAILABLE
#             )
            
#             if not SELENIUM_AVAILABLE:
#                 gr.Markdown("⚠️ *Selenium not installed - Umucyo scraping disabled*")

#             scrape_btn = gr.Button("🚀 Start Combined Scraping", variant="primary", size="lg")
#             scraping_status = gr.Textbox(label="Scraping Status", lines=12, interactive=False)
#             scraped_display = gr.Dataframe(
#                 label="Scraped Tenders Preview", 
#                 interactive=False,
#                 datatype=["str", "str", "str", "str", "str", "markdown"]
#             )

#             scrape_btn.click(
#                 fn=perform_combined_scraping,
#                 inputs=[include_umucyo_checkbox],
#                 outputs=[scraping_status, scraped_display, scraped_data_state]
#             )

#         with gr.Tab("🔎 Smart Search"):
#             gr.Markdown("### Search Through All Scraped Tenders")

#             with gr.Row():
#                 with gr.Column(scale=2):
#                     search_query = gr.Textbox(
#                         label="Search Query",
#                         placeholder="e.g., 'medical equipment', 'construction', 'IT services'...",
#                         lines=1
#                     )
                    
#             with gr.Row():

#                 with gr.Column(scale=1):
#                     category_filter = gr.Dropdown(
#                         label="📁 Category Filter",
#                         choices=["All", "Construction", "IT/Technology", "Medical/Health",
#                                 "Education", "Consultancy", "Supply", "Services", 
#                                 "Agriculture", "Transport", "Water", "Energy", 
#                                 "Environment", "Safety", "Mining", "Air Quality", "Other"],
#                         value="All"
#                     )

#                 with gr.Column(scale=1):
#                     urgency_filter = gr.Dropdown(
#                         label="⚡ Urgency Filter",
#                         choices=["All", "Critical", "Urgent", "Medium", "Low", "Unknown", "Expired"],
#                         value="All"
#                     )

#             search_btn = gr.Button("🔍 Search Tenders", variant="primary")

#             search_results_info = gr.Textbox(label="Search Results", lines=5, interactive=False)
#             search_results_table = gr.Dataframe(
#                 label="Matching Tenders", 
#                 interactive=False,
#                 datatype=["str", "str", "str", "str", "str", "markdown"]
#             )

#             search_btn.click(
#                 fn=search_tenders,
#                 inputs=[search_query, category_filter, urgency_filter, scraped_data_state],
#                 outputs=[search_results_info, search_results_table]
#             )

#             search_query.submit(
#                 fn=search_tenders,
#                 inputs=[search_query, category_filter, urgency_filter, scraped_data_state],
#                 outputs=[search_results_info, search_results_table]
#             )

#         with gr.Tab("📊 Analytics"):
#             gr.Markdown("### Data Analytics and Insights")

#             analytics_btn = gr.Button("📈 Generate Analytics", variant="secondary")
#             analytics_output = gr.Textbox(label="Analytics Report", lines=20, interactive=False)

#             def generate_analytics(scraped_data):
#                 if not scraped_data:
#                     return "⚠️ No data available. Please scrape first."

#                 df = pd.DataFrame(scraped_data)
#                 search_engine.load_data(df)
#                 stats = search_engine.get_statistics()

#                 report = f"""
# 📊 **TENDER ANALYTICS REPORT**

# **Overview:**
# - Total Tenders: {stats['total_tenders']}
# - Tenders with Deadlines: {stats['with_deadlines']}
# - Success Rate: {(stats['with_deadlines']/stats['total_tenders']*100):.1f}%

# **Data Sources:**
# """
#                 for source, count in stats.get('sources', {}).items():
#                     percentage = (count / stats['total_tenders']) * 100
#                     report += f"\n- {source}: {count} tenders ({percentage:.1f}%)"

#                 report += "\n\n**Category Distribution:**"
#                 for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
#                     percentage = (count / stats['total_tenders']) * 100
#                     report += f"\n- {category}: {count} tenders ({percentage:.1f}%)"

#                 report += "\n\n⚡ **Urgency Analysis:**"
#                 for urgency, count in sorted(stats['urgency_levels'].items(), key=lambda x: x[1], reverse=True):
#                     percentage = (count / stats['total_tenders']) * 100
#                     report += f"\n- {urgency}: {count} tenders ({percentage:.1f}%)"

#                 report += "\n\n💡 **Key Insights:**"
#                 top_category = max(stats['categories'].items(), key=lambda x: x[1])
#                 report += f"\n- Most active sector: {top_category[0]} ({top_category[1]} tenders)"

#                 urgent_count = stats['urgency_levels'].get('Critical', 0) + stats['urgency_levels'].get('Urgent', 0)
#                 if urgent_count > 0:
#                     report += f"\n- {urgent_count} tenders require immediate attention"

#                 expired_count = stats['urgency_levels'].get('Expired', 0)
#                 if expired_count > 0:
#                     report += f"\n- ⚠️ {expired_count} tenders have already expired"

#                 return report

#             analytics_btn.click(
#                 fn=generate_analytics,
#                 inputs=[scraped_data_state],
#                 outputs=[analytics_output]
#             )

#         with gr.Tab("📖 Help"):
#             gr.Markdown("""
#             ## How This System Works
            
#             ### Two Scraping Methods Combined
            
#             **Method 1 - BeautifulSoup (Fast)**
#             - JobInRwanda.com (consultancy, tenders, all jobs)
#             - RwandaTenders.com
#             - Uses HTTP requests and HTML parsing
#             - Fast and efficient
            
#             **Method 2 - Selenium (Comprehensive)**
#             - Umucyo.gov.rw (Government tender portal)
#             - Uses browser automation
#             - Slower but handles dynamic JavaScript content
#             - Optional (can be disabled)
            
#             ### Data Merging
#             All data from both methods is:
#             1. Standardized to common format (title, link, deadline)
#             2. Combined into single DataFrame
#             3. Deduplicated based on title and link
#             4. Enhanced with source tracking
            
#             ### Search Features
#             - Semantic search using TF-IDF
#             - Category auto-detection
#             - Urgency level calculation
#             - Filter by category and urgency
#             - Source identification
            
#             ### Installation
#             ```bash
#             # Basic requirements
#             pip install gradio pandas beautifulsoup4 requests scikit-learn nltk
            
#             # For Umucyo support (optional)
#             pip install selenium
#             # Also need ChromeDriver
#             ```
#             """)

#     return demo












# Optimized Combined Tender Scraping System
import gradio as gr
import pandas as pd
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from dateutil import parser
import warnings
warnings.filterwarnings('ignore')

# Optional Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# ============================================================================
# OPTIMIZED CONSTANTS AND PRECOMPILED PATTERNS
# ============================================================================

# Precompile all regex patterns (O(1) lookup vs O(n) compilation)
PATTERNS = {
    'tender_keywords': re.compile(
        r'tender|supply|construction|provision|consultancy|proposal|rfp|procurement|'
        r'bidding|contract|services|works|job|hiring|expression of interest|eoi|'
        r'terms of reference|tor|market',
        re.IGNORECASE
    ),
    'skip_keywords': re.compile(
        r'post advert|hr service|employers|testimonials|about us|contact us|'
        r'featured|jobs(?!\w)|tenders(?!\w)|consultancy(?!\w)|internships|'
        r'public(?!\w)|others(?!\w)|home|login|register|search|apply|browse|'
        r'categories|locations|salary|experience|education|skills|follow us|'
        r'social media|facebook|twitter|linkedin|instagram|\+250|phone|email|'
        r'address|contact info|site map|help|faq|support|privacy policy|'
        r'terms of service|copyright',
        re.IGNORECASE
    ),
    'phone': re.compile(r'^\+?\d+[\d\s\-\(\)]+$'),
    'kg_address': re.compile(r'kg\s*\d+', re.IGNORECASE),
    'category_pattern': re.compile(r'^(featured|jobs|tenders|consultancy|internships|public|others)\d+$', re.IGNORECASE),
    'date_patterns': [
        re.compile(r'deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})', re.IGNORECASE),
        re.compile(r'due[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})', re.IGNORECASE),
        re.compile(r'closing[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})', re.IGNORECASE),
        re.compile(r'submit by[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})', re.IGNORECASE),
        re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}'),
        re.compile(r'\d{4}-\d{1,2}-\d{1,2}'),
        re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2}'),
        re.compile(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}', re.IGNORECASE),
        re.compile(r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', re.IGNORECASE)
    ]
}

# Pre-defined sets for O(1) lookup
UNWANTED_KEYWORDS = frozenset([
    'navigation', 'menu', 'footer', 'header', 'sidebar', 'contact',
    'about', 'social', 'copyright', 'terms', 'privacy', 'testimonial',
    'breadcrumb', 'pagination', 'filter', 'search-form'
])

SKIP_LINK_PATTERNS = frozenset([
    '/post-advert', '/all-employers', '/testimonials', '/about', '/contact',
    '/jobs/all', '/jobs/featured', '/jobs/internships', '/jobs/consultancy',
    '/jobs/public-adverts', '/jobs/others', '/page/', '/help', '/support',
    'hrms.rw', 'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
    '/privacy', '/terms', '/sitemap', '/faq'
])

ACCEPT_LINK_PATTERNS = frozenset(['/job/', '/tender/', '/vacancy/', '/opportunity/'])

# Category keywords optimized with frozenset
CATEGORY_KEYWORDS = {
    'Construction': frozenset(['construction', 'building', 'road', 'infrastructure', 'bridge', 'renovation']),
    'IT/Technology': frozenset(['software', 'it', 'technology', 'system', 'database', 'network', 'computer']),
    'Medical/Health': frozenset(['medical', 'health', 'hospital', 'clinic', 'equipment', 'pharmaceutical']),
    'Education': frozenset(['school', 'university', 'education', 'training', 'academic', 'student']),
    'Consultancy': frozenset(['consultancy', 'consulting', 'advisory', 'assessment', 'evaluation']),
    'Supply': frozenset(['supply', 'procurement', 'purchase', 'equipment', 'materials', 'goods']),
    'Services': frozenset(['services', 'maintenance', 'cleaning', 'security', 'catering']),
    'Agriculture': frozenset(['agriculture', 'farming', 'crop', 'livestock', 'irrigation']),
    'Transport': frozenset(['transport', 'vehicle', 'logistics', 'shipping', 'delivery']),
    'Energy': frozenset(['energy', 'electricity', 'power', 'solar', 'generator', 'renewable']),
    'Water': frozenset(['water', 'sanitation', 'drinking water', 'wastewater', 'hydro']),
    'Environment': frozenset(['environment', 'conservation', 'sustainability', 'biodiversity']),
    'Safety': frozenset(['safety', 'occupational health', 'hse', 'risk assessment']),
    'Mining': frozenset(['mining', 'mineral', 'ore', 'quarry', 'extraction']),
    'Air Quality': frozenset(['air quality', 'emissions', 'particulate matter', 'monitoring'])
}

# ============================================================================
# OPTIMIZED BEAUTIFULSOUP SCRAPER (Method 1 & 2)
# ============================================================================

class OptimizedBeautifulSoupScraper:
    """Optimized BeautifulSoup scraper with O(1) lookups and reduced redundancy"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Cache for parsed domains to avoid repeated urlparse calls
        self._domain_cache = {}
    
    def fetch_page_content(self, url):
        """Optimized fetch with session reuse"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _get_domain(self, url):
        """Cached domain extraction - O(1) after first call"""
        if url not in self._domain_cache:
            self._domain_cache[url] = urlparse(url).netloc
        return self._domain_cache[url]
    
    def _is_unwanted_content(self, container):
        """Optimized with set intersection - O(1) average"""
        container_class = ' '.join(container.get('class', [])).lower()
        container_id = container.get('id', '').lower()
        
        # Quick check using substring search on combined string
        combined = container_class + ' ' + container_id
        if any(kw in combined for kw in UNWANTED_KEYWORDS):
            return True
        
        # Only check parent if necessary
        parent = container.parent
        depth = 0
        while parent and parent.name != 'body' and depth < 3:  # Limit depth
            parent_class = ' '.join(parent.get('class', [])).lower()
            parent_id = parent.get('id', '').lower()
            combined = parent_class + ' ' + parent_id
            if any(kw in combined for kw in UNWANTED_KEYWORDS):
                return True
            parent = parent.parent
            depth += 1
        
        return False
    
    def _is_tender_title(self, title):
        """Optimized with precompiled patterns and early returns"""
        if len(title.strip()) < 15 or title.strip().isdigit():
            return False
        
        title_lower = title.lower()
        
        # Use precompiled patterns
        if PATTERNS['skip_keywords'].search(title_lower):
            return False
        
        if PATTERNS['phone'].match(title.strip()) or '@' in title and len(title) < 30:
            return False
        
        if PATTERNS['kg_address'].search(title_lower):
            return False
        
        if PATTERNS['category_pattern'].match(title_lower):
            return False
        
        # Quick tender keyword check
        if PATTERNS['tender_keywords'].search(title_lower):
            return True
        
        # Final length-based check
        return len(title.strip()) > 25
    
    def _is_tender_link(self, link):
        """Optimized with set operations - O(1) average"""
        if link == "No link available":
            return False
        
        link_lower = link.lower()
        
        # Early reject with any()
        if any(pattern in link_lower for pattern in SKIP_LINK_PATTERNS):
            return False
        
        # Must match at least one accept pattern
        if not any(pattern in link_lower for pattern in ACCEPT_LINK_PATTERNS):
            return False
        
        # Avoid category pages
        if link_lower.endswith(('/tender', '/tenders', '/jobs', '/job')):
            return False
        
        return True
    
    def _extract_deadline(self, container_text):
        """Optimized deadline extraction with cached patterns"""
        for pattern in PATTERNS['date_patterns']:
            match = pattern.search(container_text)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return "Not specified"
    
    def _extract_tender_data_batch(self, soup, current_url):
        """Batch process tenders - reduced function calls"""
        tenders = []
        
        # Remove unwanted sections once
        for selector in ['nav', 'header', 'footer', 'sidebar', '.menu', '.navigation']:
            for element in soup.select(selector):
                element.decompose()
        
        # Find all potential containers in one pass
        tender_containers = []
        for tag, class_pattern in [
            ('div', re.compile(r'tender|job|listing|post|item', re.I)),
            ('article', re.compile(r'tender|job|post', re.I)),
            ('tr', re.compile(r'tender|row', re.I)),
            ('li', re.compile(r'tender|job|item', re.I))
        ]:
            tender_containers.extend(soup.find_all(tag, class_=class_pattern))
        
        if not tender_containers:
            main_content = soup.find('main') or soup.find('div', class_=re.compile(r'content|main', re.I))
            tender_containers = (main_content.find_all('a', href=True) if main_content 
                               else soup.find_all('a', href=True))
        
        # Process containers
        for container in tender_containers:
            if self._is_unwanted_content(container):
                continue
            
            # Extract title efficiently
            title = None
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a']:
                element = container.find(tag)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 5:
                        title = text[:150]
                        break
            
            if not title and container.name == 'a':
                title = container.get_text(strip=True)[:150]
            
            if not title or not self._is_tender_title(title):
                continue
            
            # Extract link
            link_element = container.find('a', href=True) if container.name != 'a' else container
            link = (urljoin(current_url, link_element['href']) if link_element and link_element.get('href')
                   else "No link available")
            
            if not self._is_tender_link(link):
                continue
            
            # Extract deadline
            deadline = self._extract_deadline(container.get_text())
            
            # Add if valid
            if deadline != "Not specified" and link != "No link available":
                tenders.append({
                    'title': title.strip(),
                    'link': link,
                    'deadline': deadline
                })
        
        return tenders
    
    def scrape_url(self, base_url):
        """Main scraping method"""
        print(f"Scraping: {base_url}")
        html_content = self.fetch_page_content(base_url)
        
        if not html_content:
            return pd.DataFrame(columns=['title', 'link', 'deadline'])
        
        soup = BeautifulSoup(html_content, "html.parser")
        tenders = self._extract_tender_data_batch(soup, base_url)
        
        if tenders:
            df = pd.DataFrame(tenders)
            df.drop_duplicates(subset=['title', 'link'], keep='first', inplace=True)
            print(f"Found {len(df)} tenders from {base_url}")
            return df
        
        return pd.DataFrame(columns=['title', 'link', 'deadline'])

def scrape_multiple_urls_parallel(urls, max_workers=3):
    """Parallel scraping with optimized scraper"""
    scraper = OptimizedBeautifulSoupScraper()
    all_dfs = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scraper.scrape_url, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                df = future.result()
                if not df.empty:
                    all_dfs.append(df)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
    
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df.drop_duplicates(subset=['title', 'link'], keep='first', inplace=True)
        return combined_df
    
    return pd.DataFrame(columns=['title', 'link', 'deadline'])

# ============================================================================
# OPTIMIZED SELENIUM SCRAPERS
# ============================================================================

class BaseSeleniumScraper:
    """Base class with shared Selenium optimization"""
    
    def __init__(self, base_url, driver_path=None, headless=True):
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not installed")
        
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-images')  # Faster loading
        options.add_argument('--blink-settings=imagesEnabled=false')  # Faster loading
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = (webdriver.Chrome(executable_path=driver_path, options=options) if driver_path
                      else webdriver.Chrome(options=options))
        
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(5)
        self.base_url = base_url
        self.data = []
    
    def _wait_for_page_load(self, timeout=15):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            pass
    
    def cleanup(self):
        try:
            self.driver.quit()
        except:
            pass

class UmucyoTendersScraper(BaseSeleniumScraper):
    """Optimized Umucyo scraper"""
    
    def __init__(self, driver_path=None, headless=True):
        super().__init__("https://www.umucyo.gov.rw", driver_path, headless)
        self.tenders_url = "https://www.umucyo.gov.rw/eb/bav/selectListAdvertisingListForGU.do?menuId=EB01020100&leftTopFlag=l"
        # Cache for date patterns
        self._date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}')
    
    def _wait_for_table(self, timeout=20):
        """Wait for table to load"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
            )
            time.sleep(2)  # Extra wait for dynamic content
            return True
        except TimeoutException:
            print("Table not found within timeout")
            return False
    
    def _extract_all_dates(self, cell_texts):
        """Optimized date extraction"""
        dates_found = []
        for text in cell_texts:
            matches = self._date_pattern.findall(text)
            dates_found.extend(match for match in matches if match not in dates_found)
        return dates_found
    
    def _is_date_string(self, text):
        """Check if text is a date"""
        return bool(self._date_pattern.search(text))
    
    def _extract_tender_rows_from_table(self):
        """Batch process table rows with improved parsing"""
        tender_rows = []
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all tables and process the one with most rows
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables on page")
            
            best_table = None
            max_rows = 0
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > max_rows:
                    max_rows = len(rows)
                    best_table = table
            
            if not best_table or max_rows < 2:
                print("No valid table found")
                return tender_rows
            
            rows = best_table.find_all('tr')
            print(f"Processing table with {len(rows)} rows")
            
            # Identify header row
            header_row = rows[0]
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            print(f"Headers: {headers}")
            
            # Process data rows
            for row_idx, row in enumerate(rows[1:], start=1):
                try:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 3:
                        continue
                    
                    # Extract all cell texts
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # Skip empty rows
                    if not any(cell_texts):
                        continue
                    
                    # Extract dates
                    dates = self._extract_all_dates(cell_texts)
                    
                    # Find tender name - look for text in link or longest non-date text
                    tender_name = "N/A"
                    
                    # First try to find link text
                    for cell in cells:
                        link = cell.find('a', href=True)
                        if link:
                            link_text = link.get_text(strip=True)
                            if len(link_text) > 10 and not self._is_date_string(link_text):
                                tender_name = link_text
                                break
                    
                    # If no link text, find longest non-date text
                    if tender_name == "N/A":
                        candidates = [
                            text for text in cell_texts 
                            if len(text) > 10 and not self._is_date_string(text)
                            and text.upper() not in ['OPEN', 'CLOSED', 'CANCELLED', 'AWARDED']
                        ]
                        if candidates:
                            tender_name = max(candidates, key=len)
                    
                    # Find tender link
                    tender_link = None
                    for cell in cells:
                        link = cell.find('a', href=True)
                        if link and link.get('href'):
                            href = link['href']
                            if href.startswith('/'):
                                tender_link = self.base_url + href
                            elif not href.startswith('http'):
                                tender_link = self.base_url + '/' + href
                            else:
                                tender_link = href
                            break
                    
                    # Only add if we have at least a name or link
                    if tender_name != "N/A" or tender_link:
                        tender_data = {
                            'tender_name': tender_name,
                            'advertising_date': dates[0] if len(dates) > 0 else None,
                            'deadline_of_submitting': dates[1] if len(dates) > 1 else None,
                            'planned_open_date': dates[2] if len(dates) > 2 else None,
                            'tender_link': tender_link
                        }
                        tender_rows.append(tender_data)
                        print(f"Row {row_idx}: {tender_name[:50]}...")
                
                except Exception as e:
                    print(f"Error processing row {row_idx}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error extracting table: {e}")
        
        return tender_rows
    
    def _check_for_next_page(self):
        """Quick next page check"""
        try:
            next_button = self.driver.find_element(By.XPATH,
                "//a[contains(text(), 'Next') or contains(text(), '>')]")
            if next_button.is_enabled() and next_button.is_displayed():
                next_button.click()
                self._wait_for_page_load()
                return True
        except (NoSuchElementException, TimeoutException):
            pass
        return False
    
    def scrape(self, max_pages=5):
        print("Starting Umucyo scraping...")
        try:
            print(f"Navigating to {self.tenders_url}")
            self.driver.get(self.tenders_url)
            self._wait_for_page_load()
            
            # Wait for table to load
            if not self._wait_for_table():
                print("Failed to load table")
                return self.data
            
            page_count = 0
            
            while page_count < max_pages:
                print(f"\n--- Scraping page {page_count + 1} ---")
                
                page_tenders = self._extract_tender_rows_from_table()
                print(f"Found {len(page_tenders)} tenders on page {page_count + 1}")
                
                if page_tenders:
                    self.data.extend(page_tenders)
                else:
                    print("No tenders found on this page")
                
                # Try to go to next page
                if not self._check_for_next_page():
                    print("No more pages available")
                    break
                
                page_count += 1
                time.sleep(2)  # Wait between pages
        
        except Exception as e:
            print(f"Umucyo scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
        
        print(f"\nUmucyo scraping complete: {len(self.data)} tenders collected")
        return self.data

class WorldBankRwandaScraper(BaseSeleniumScraper):
    """Optimized World Bank scraper"""
    
    def __init__(self, driver_path=None, headless=True):
        super().__init__("https://projects.worldbank.org", driver_path, headless)
        self.target_url = "https://projects.worldbank.org/en/projects-operations/opportunities?srce=both&project_ctry_name_exact=Rwanda"
    
    def _format_date(self, date_string):
        """Optimized date formatting"""
        if not date_string or not date_string.strip():
            return ''
        try:
            return parser.parse(date_string).strftime('%d/%m/%Y')
        except:
            return date_string
    
    def _extract_opportunities_from_table(self):
        """Batch process opportunities table"""
        opportunities = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        table = soup.find('table') or soup.select_one('[role="table"]')
        if not table:
            return opportunities
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return opportunities
        
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
        
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Extract link
            tender_link = None
            for cell in cells:
                link = cell.find('a', href=True)
                if link:
                    href = link['href']
                    tender_link = (self.base_url + href if href.startswith('/') else href)
                    break
            
            # Map cells to fields based on headers
            opportunity = {
                'tender_name': '',
                'notice_type': '',
                'published_date': '',
                'deadline_of_submitting': '',
                'tender_link': tender_link
            }
            
            for idx, (header, text) in enumerate(zip(headers, cell_texts)):
                if 'title' in header:
                    opportunity['tender_name'] = text
                elif 'type' in header:
                    opportunity['notice_type'] = text
                elif 'published' in header:
                    opportunity['published_date'] = text
                elif 'deadline' in header:
                    opportunity['deadline_of_submitting'] = self._format_date(text)
            
            # Fallback to positional if headers didn't match
            if not opportunity['tender_name'] and len(cell_texts) >= 6:
                opportunity['tender_name'] = cell_texts[2]
                opportunity['notice_type'] = cell_texts[3]
                opportunity['published_date'] = cell_texts[6] if len(cell_texts) > 6 else ''
                opportunity['deadline_of_submitting'] = self._format_date(cell_texts[1])
            
            if opportunity['tender_name'] or opportunity['notice_type']:
                opportunities.append(opportunity)
        
        return opportunities
    
    def _check_for_next_page(self):
        """Quick next page check"""
        try:
            next_button = self.driver.find_element(By.XPATH,
                "//a[contains(text(), 'Next')] | //button[contains(text(), 'Next')]")
            if next_button.is_displayed() and next_button.is_enabled():
                next_button.click()
                self._wait_for_page_load()
                return True
        except:
            pass
        return False
    
    def scrape(self, max_pages=5):
        print("Starting World Bank scraping...")
        try:
            self.driver.get(self.target_url)
            self._wait_for_page_load()
            
            for page in range(max_pages):
                print(f"Scraping page {page + 1}")
                time.sleep(2)  # Let table load
                page_opportunities = self._extract_opportunities_from_table()
                self.data.extend(page_opportunities)
                
                if not self._check_for_next_page():
                    break
                time.sleep(1)
            
            # Deduplicate by link
            seen_links = set()
            unique_data = []
            for item in self.data:
                link = item.get('tender_link', '')
                if link and link not in seen_links:
                    unique_data.append(item)
                    seen_links.add(link)
                elif not link:
                    unique_data.append(item)
            self.data = unique_data
        
        except Exception as e:
            print(f"World Bank scraping error: {e}")
        finally:
            self.cleanup()
        
        print(f"World Bank: {len(self.data)} opportunities collected")
        return self.data

# ============================================================================
# OPTIMIZED DATA MERGER
# ============================================================================

def merge_scraped_data(method2_data, method3_data, method1_df, method0_df):
    """Optimized merge with minimal DataFrame operations"""
    
    dfs_to_merge = []
    
    # Add source to existing DataFrames
    if not method1_df.empty:
        method1_df['source'] = 'jobinrwanda.com'
        method1_df['extra_info'] = ''
        dfs_to_merge.append(method1_df)
    
    if not method0_df.empty:
        method0_df['source'] = 'rwandatenders.com'
        method0_df['extra_info'] = ''
        dfs_to_merge.append(method0_df)
    
    # Convert Method 2 data
    if method2_data:
        method2_df = pd.DataFrame(method2_data).rename(columns={
            'tender_name': 'title',
            'tender_link': 'link',
            'deadline_of_submitting': 'deadline'
        })
        method2_df['source'] = 'umucyo.gov.rw'
        method2_df['extra_info'] = method2_df.apply(
            lambda x: f"Advertised: {x.get('advertising_date', 'N/A')}, Opens: {x.get('planned_open_date', 'N/A')}", 
            axis=1
        )
        dfs_to_merge.append(method2_df[['title', 'link', 'deadline', 'source', 'extra_info']])
    
    # Convert Method 3 data
    if method3_data:
        method3_df = pd.DataFrame(method3_data).rename(columns={
            'tender_name': 'title',
            'tender_link': 'link',
            'deadline_of_submitting': 'deadline'
        })
        method3_df['source'] = 'worldbank.org'
        method3_df['extra_info'] = method3_df.apply(
            lambda x: f"Type: {x.get('notice_type', 'N/A')}, Published: {x.get('published_date', 'N/A')}", 
            axis=1
        )
        dfs_to_merge.append(method3_df[['title', 'link', 'deadline', 'source', 'extra_info']])
    
    if not dfs_to_merge:
        return pd.DataFrame(columns=['title', 'link', 'deadline', 'source', 'extra_info'])
    
    # Single concat operation
    combined_df = pd.concat(dfs_to_merge, ignore_index=True)
    combined_df.drop_duplicates(subset=['title', 'link'], keep='first', inplace=True)
    
    return combined_df

# ============================================================================
# OPTIMIZED SEARCH ENGINE
# ============================================================================

class TenderSearchEngine:
    """Optimized search with cached categorization"""
    
    def __init__(self):
        self.df = pd.DataFrame()
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=3000)
        self.tfidf_matrix = None
        self._category_cache = {}
        self._urgency_cache = {}
    
    def load_data(self, df):
        """Load and prepare data once"""
        self.df = df.copy()
        if not df.empty:
            self.tfidf_matrix = self.vectorizer.fit_transform(df['title'].fillna('').astype(str))
            # Pre-compute categories and urgency
            self.df['category'] = self.df['title'].apply(self.categorize_tender)
            self.df['urgency'] = self.df['deadline'].apply(self.get_urgency_level)
    
    def categorize_tender(self, title):
        """Optimized categorization with caching and set intersection"""
        if title in self._category_cache:
            return self._category_cache[title]
        
        title_lower = title.lower()
        title_words = set(title_lower.split())
        
        # O(1) set intersection for each category
        for category, keywords in CATEGORY_KEYWORDS.items():
            if keywords & title_words:  # Set intersection
                self._category_cache[title] = category
                return category
        
        self._category_cache[title] = 'Other'
        return 'Other'
    
    def get_urgency_level(self, deadline_str):
        """Optimized urgency with caching"""
        if deadline_str in self._urgency_cache:
            return self._urgency_cache[deadline_str]
        
        if deadline_str == "Not specified":
            return "Unknown"
        
        try:
            deadline = None
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y']:
                try:
                    deadline = datetime.strptime(deadline_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not deadline:
                return "Unknown"
            
            days_left = (deadline - datetime.now()).days
            
            if days_left < 0:
                urgency = "Expired"
            elif days_left <= 3:
                urgency = "Critical"
            elif days_left <= 7:
                urgency = "Urgent"
            elif days_left <= 14:
                urgency = "Medium"
            else:
                urgency = "Low"
            
            self._urgency_cache[deadline_str] = urgency
            return urgency
        except:
            return "Unknown"
    
    def smart_search(self, query, category_filter="All", urgency_filter="All", limit=20):
        """Optimized search with pre-computed fields"""
        if self.df.empty:
            return pd.DataFrame()
        
        df_filtered = self.df.copy()
        
        # Use pre-computed category and urgency
        if category_filter != "All":
            df_filtered = df_filtered[df_filtered['category'] == category_filter]
        
        if urgency_filter != "All":
            df_filtered = df_filtered[df_filtered['urgency'] == urgency_filter]
        
        # Apply text search if query provided
        if query.strip():
            query_vec = self.vectorizer.transform([query])
            filtered_indices = df_filtered.index.tolist()
            
            if filtered_indices:
                filtered_tfidf = self.tfidf_matrix[filtered_indices]
                scores = cosine_similarity(query_vec, filtered_tfidf).flatten()
                
                # Sort by scores efficiently
                sorted_idx = np.argsort(scores)[::-1]
                df_filtered = df_filtered.iloc[sorted_idx]
                df_filtered['relevance_score'] = scores[sorted_idx]
                
                # Filter low relevance
                df_filtered = df_filtered[df_filtered['relevance_score'] > 0.1]
        
        return df_filtered.head(limit)
    
    def get_statistics(self):
        """Optimized statistics with pre-computed fields"""
        if self.df.empty:
            return {}
        
        # Use pre-computed category and urgency columns
        stats = {
            'total_tenders': len(self.df),
            'categories': self.df['category'].value_counts().to_dict(),
            'urgency_levels': self.df['urgency'].value_counts().to_dict(),
            'with_deadlines': len(self.df[self.df['deadline'] != 'Not specified']),
            'sources': self.df['source'].value_counts().to_dict() if 'source' in self.df.columns else {}
        }
        
        return stats

# Global search engine instance
search_engine = TenderSearchEngine()

# ============================================================================
# GRADIO INTERFACE FUNCTIONS
# ============================================================================

def perform_combined_scraping(include_umucyo, include_worldbank, progress=gr.Progress()):
    """Optimized combined scraping with progress tracking"""
    try:
        start_time = time.time()
        
        # Method 1: JobInRwanda (parallel)
        progress(0.05, desc="Scraping JobInRwanda...")
        websites_job = [
            "https://www.jobinrwanda.com/jobs/consultancy",
            "https://www.jobinrwanda.com/jobs/tender",
            "https://www.jobinrwanda.com/jobs/all"
        ]
        method1_df = scrape_multiple_urls_parallel(websites_job, max_workers=3)
        progress(0.25, desc=f"JobInRwanda: {len(method1_df)} tenders")
        
        # Method 0: RwandaTenders (parallel)
        progress(0.3, desc="Scraping RwandaTenders...")
        websites_rw = ["https://www.rwandatenders.com/tenders.php"]
        method0_df = scrape_multiple_urls_parallel(websites_rw, max_workers=1)
        progress(0.4, desc=f"RwandaTenders: {len(method0_df)} tenders")
        
        # Method 2: Umucyo (optional)
        method2_data = []
        if include_umucyo and SELENIUM_AVAILABLE:
            progress(0.5, desc="Scraping Umucyo (slower)...")
            try:
                umucyo_scraper = UmucyoTendersScraper(headless=True)
                method2_data = umucyo_scraper.scrape(max_pages=5)
                progress(0.7, desc=f"Umucyo: {len(method2_data)} tenders")
            except Exception as e:
                print(f"Umucyo error: {e}")
        
        # Method 3: World Bank (optional)
        method3_data = []
        if include_worldbank and SELENIUM_AVAILABLE:
            progress(0.75, desc="Scraping World Bank (slower)...")
            try:
                wb_scraper = WorldBankRwandaScraper(headless=True)
                method3_data = wb_scraper.scrape(max_pages=5)
                progress(0.9, desc=f"World Bank: {len(method3_data)} tenders")
            except Exception as e:
                print(f"World Bank error: {e}")
        
        # Merge all data
        progress(0.95, desc="Merging and processing...")
        final_df = merge_scraped_data(method2_data, method3_data, method1_df, method0_df)
        
        # Load into search engine (pre-computes categories and urgency)
        search_engine.load_data(final_df)
        
        execution_time = time.time() - start_time
        
        if final_df.empty:
            return "No tenders found.", pd.DataFrame(), {}
        
        # Generate summary
        stats = search_engine.get_statistics()
        summary = f"""✅ **Scraping Completed!**

**Summary:**
- Total Tenders: {stats['total_tenders']}
- With Deadlines: {stats['with_deadlines']}
- Time: {execution_time:.2f}s

**Sources:**
"""
        for source, count in stats.get('sources', {}).items():
            summary += f"\n- {source}: {count}"
        
        summary += "\n\n**Top Categories:**"
        for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:5]:
            summary += f"\n- {cat}: {count}"
        
        progress(1.0, desc="Complete!")
        return summary, create_display_dataframe(final_df), final_df.to_dict('records')
    
    except Exception as e:
        return f"❌ Error: {str(e)}", pd.DataFrame(), {}

def search_tenders(query, category_filter, urgency_filter, scraped_data):
    """Optimized search function"""
    if not scraped_data:
        return "⚠️ No data. Please scrape first.", pd.DataFrame()
    
    try:
        results = search_engine.smart_search(query, category_filter, urgency_filter)
        
        if results.empty:
            return "⚠️ No matching tenders found.", pd.DataFrame()
        
        summary = f" **Found {len(results)} tenders**\n\n"
        if query.strip():
            summary += f"Query: '{query}'\n"
        if category_filter != "All":
            summary += f"Category: {category_filter}\n"
        if urgency_filter != "All":
            summary += f"Urgency: {urgency_filter}\n"
        
        return summary, create_display_dataframe(results)
    
    except Exception as e:
        return f"❌ Error: {str(e)}", pd.DataFrame()

def create_display_dataframe(df):
    """Optimized display formatter"""
    if df.empty:
        return pd.DataFrame()
    
    display_df = df.copy()
    
    # Ensure category and urgency exist (should already be pre-computed)
    if 'category' not in display_df.columns:
        display_df['category'] = display_df['title'].apply(search_engine.categorize_tender)
    if 'urgency' not in display_df.columns:
        display_df['urgency'] = display_df['deadline'].apply(search_engine.get_urgency_level)
    
    # Format title length
    display_df['title'] = display_df['title'].str[:80] + display_df['title'].str.len().apply(
        lambda x: "..." if x > 80 else ""
    )
    
    # Format links
    if 'link' in display_df.columns:
        display_df['link'] = display_df['link'].apply(
            lambda x: f'<a href="{x}" target="_blank">Open</a>' 
            if x and x != "No link available" else "N/A"
        )
    
    # Select columns
    columns = ['title', 'category', 'deadline', 'urgency', 'source', 'extra_info', 'link']
    return display_df[[col for col in columns if col in display_df.columns]]

def generate_analytics(scraped_data):
    """Optimized analytics generation"""
    if not scraped_data:
        return "⚠️ No data available."
    
    stats = search_engine.get_statistics()
    
    report = f""" **ANALYTICS REPORT**

**Overview:**
- Total: {stats['total_tenders']}
- With Deadlines: {stats['with_deadlines']}
- Success Rate: {(stats['with_deadlines']/stats['total_tenders']*100):.1f}%

**Sources:**
"""
    for source, count in stats.get('sources', {}).items():
        pct = (count / stats['total_tenders']) * 100
        report += f"\n- {source}: {count} ({pct:.1f}%)"
    
    report += "\n\n**Categories:**"
    for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / stats['total_tenders']) * 100
        report += f"\n- {cat}: {count} ({pct:.1f}%)"
    
    report += "\n\n⚡ **Urgency:**"
    for urg, count in sorted(stats['urgency_levels'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / stats['total_tenders']) * 100
        report += f"\n- {urg}: {count} ({pct:.1f}%)"
    
    report += "\n\n💡 **Insights:**"
    top_cat = max(stats['categories'].items(), key=lambda x: x[1])
    report += f"\n- Top sector: {top_cat[0]} ({top_cat[1]} tenders)"
    
    urgent = stats['urgency_levels'].get('Critical', 0) + stats['urgency_levels'].get('Urgent', 0)
    if urgent > 0:
        report += f"\n- {urgent} urgent tenders"
    
    expired = stats['urgency_levels'].get('Expired', 0)
    if expired > 0:
        report += f"\n- ⚠️ {expired} expired"
    
    return report





# ============================================================================
# GRADIO INTERFACE
# ============================================================================

def create_interface():
    with gr.Blocks(title="Opportunity Search System", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        #  Combined Result
                    
        This system merges two scraping methodologies:
        - **Method 1**: BeautifulSoup scraping (JobInRwanda, RwandaTenders)
        - **Method 2**: Selenium scraping (Umucyo Government Portal, World Bank Portal)
        
        All results are combined into a single searchable database.
        """)
        
        scraped_data_state = gr.State([])
        
        with gr.Tab("Scraping"):
            gr.Markdown("### Scrape Results from All Sources")
            
            with gr.Row():
                include_umucyo = gr.Checkbox(
                    label="Include Umucyo (Government)",
                    value=SELENIUM_AVAILABLE,
                    interactive=SELENIUM_AVAILABLE
                )
                include_worldbank = gr.Checkbox(
                    label="Include World Bank (International)",
                    value=SELENIUM_AVAILABLE,
                    interactive=SELENIUM_AVAILABLE
                )
            
            if not SELENIUM_AVAILABLE:
                gr.Markdown("⚠️ *Selenium not installed*")
            
            scrape_btn = gr.Button("Start Scraping", variant="primary", size="lg")
            scraping_status = gr.Textbox(label="Status", lines=12, interactive=False)
            scraped_display = gr.Dataframe(
                label="Results Preview",
                interactive=False,
                datatype=["str", "str", "str", "str", "str", "str", "markdown"]
            )
            
            scrape_btn.click(
                fn=perform_combined_scraping,
                inputs=[include_umucyo, include_worldbank],
                outputs=[scraping_status, scraped_display, scraped_data_state]
            )
        
        with gr.Tab("Search"):
            gr.Markdown("### Smart Search Engine")
            
            search_query = gr.Textbox(
                label="Search Query",
                placeholder="e.g., 'medical equipment', 'construction'...",
                lines=1
            )
            
            with gr.Row():
                category_filter = gr.Dropdown(
                    label="Category",
                    choices=["All"] + list(CATEGORY_KEYWORDS.keys()) + ["Other"],
                    value="All"
                )
                urgency_filter = gr.Dropdown(
                    label="Urgency",
                    choices=["All", "Critical", "Urgent", "Medium", "Low", "Unknown", "Expired"],
                    value="All"
                )
            
            search_btn = gr.Button("Search", variant="primary")
            search_results_info = gr.Textbox(label="Results", lines=5, interactive=False)
            search_results_table = gr.Dataframe(
                label="Matching Tenders",
                interactive=False,
                datatype=["str", "str", "str", "str", "str", "str", "markdown"]
            )
            
            search_btn.click(
                fn=search_tenders,
                inputs=[search_query, category_filter, urgency_filter, scraped_data_state],
                outputs=[search_results_info, search_results_table]
            )
            
            search_query.submit(
                fn=search_tenders,
                inputs=[search_query, category_filter, urgency_filter, scraped_data_state],
                outputs=[search_results_info, search_results_table]
            )
        
        with gr.Tab("Analytics"):
            gr.Markdown("### Data Analytics")
            
            analytics_btn = gr.Button("Generate Report", variant="secondary")
            analytics_output = gr.Textbox(label="Analytics", lines=25, interactive=False)
            
            analytics_btn.click(
                fn=generate_analytics,
                inputs=[scraped_data_state],
                outputs=[analytics_output]
            )
        
        with gr.Tab("Help"):
            gr.Markdown("""
            ## How This System Works
            
            ### Data Merging
            All data from both methods is:
            1. Standardized to common format (title, link, deadline)
            2. Combined into single DataFrame
            3. Deduplicated based on title and link
            4. Enhanced with source tracking
            
            ### Search Features
            - Semantic search using TF-IDF
            - Category auto-detection
            - Urgency level calculation
            - Filter by category and urgency
            - Source identification
            
            """)
    
    return demo

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=port, share=False, show_error=True)


