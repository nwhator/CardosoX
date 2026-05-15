"""
Web Scraper Module
Handles website scraping with anti-bot detection bypass
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import random
import time

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import cloudscraper

logger = logging.getLogger(__name__)


class WebScraper:
    """Advanced web scraper with anti-bot detection bypass"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.cs = cloudscraper.create_scraper()
        self.max_retries = 3
        self.timeout = 30
        
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently"""
        try:
            # Run async scraping
            results = asyncio.run(self._scrape_multiple_async(urls))
            return results
        except Exception as e:
            logger.error(f"Error in concurrent scraping: {str(e)}")
            # Fallback to sequential scraping
            return [self.scrape_url(url) for url in urls]
    
    async def _scrape_multiple_async(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Async concurrent scraping"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            tasks = [
                self._scrape_url_with_browser(browser, url)
                for url in urls
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            await browser.close()
            
            # Handle exceptions in results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in async scraping: {str(result)}")
                    processed_results.append({
                        'url': 'unknown',
                        'company_name': None,
                        'emails': [],
                        'phone_numbers': [],
                        'addresses': [],
                        'status': 'error'
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
    
    async def _scrape_url_with_browser(self, browser: Browser, url: str) -> Dict[str, Any]:
        """Scrape a single URL using Playwright"""
        context = None
        page = None
        
        try:
            # Create context with anti-detection features
            context = await browser.new_context(
                user_agent=self.ua.random,
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': 'https://www.google.com/',
                }
            )
            
            page = await context.new_page()
            
            # Hide webdriver
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """)
            
            # Navigate with retry logic
            for attempt in range(self.max_retries):
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt + random.uniform(0, 1)
                        logger.info(f"Retry {attempt + 1} for {url} after {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
            
            # Wait for dynamic content
            await asyncio.sleep(random.uniform(1, 3))
            
            # Get page content
            html_content = await page.content()
            
            # Parse with BeautifulSoup
            result = self._parse_page(url, html_content)
            
            # Try to scrape related pages (contact, about)
            await self._scrape_related_pages(page, url, result)
            
            result['status'] = 'success'
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'company_name': None,
                'emails': [],
                'phone_numbers': [],
                'addresses': [],
                'status': 'error',
                'error': str(e)
            }
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Synchronous single URL scraping with fallback to cloudscraper"""
        try:
            # Try Playwright first
            try:
                result = asyncio.run(self._scrape_url_async(url))
                return result
            except Exception as e:
                logger.warning(f"Playwright failed for {url}, trying cloudscraper: {str(e)}")
                # Fallback to cloudscraper for Cloudflare-protected sites
                return self._scrape_with_cloudscraper(url)
                
        except Exception as e:
            logger.error(f"Final error scraping {url}: {str(e)}")
            return {
                'url': url,
                'company_name': None,
                'emails': [],
                'phone_numbers': [],
                'addresses': [],
                'status': 'error'
            }
    
    async def _scrape_url_async(self, url: str) -> Dict[str, Any]:
        """Async scraping for single URL"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.ua.random)
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
                await asyncio.sleep(random.uniform(1, 2))
                
                html_content = await page.content()
                result = self._parse_page(url, html_content)
                result['status'] = 'success'
                
                return result
            finally:
                await context.close()
                await browser.close()
    
    def _scrape_with_cloudscraper(self, url: str) -> Dict[str, Any]:
        """Fallback scraping using cloudscraper (for Cloudflare)"""
        try:
            response = self.cs.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            result = self._parse_page(url, response.text)
            result['status'] = 'success'
            return result
            
        except Exception as e:
            logger.error(f"Cloudscraper error for {url}: {str(e)}")
            return {
                'url': url,
                'company_name': None,
                'emails': [],
                'phone_numbers': [],
                'addresses': [],
                'status': 'error'
            }
    
    async def _scrape_related_pages(self, page: Page, base_url: str, result: Dict) -> None:
        """Try to scrape contact and about pages for more info"""
        related_paths = ['/contact', '/about', '/contact-us', '/contact-information']
        
        for path in related_paths:
            try:
                related_url = urljoin(base_url, path)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                await page.goto(related_url, wait_until='domcontentloaded', timeout=10000)
                await asyncio.sleep(random.uniform(0.5, 1))
                
                html = await page.content()
                related_data = self._extract_contact_info(html)
                
                # Merge results
                result['emails'].extend(related_data.get('emails', []))
                result['phone_numbers'].extend(related_data.get('phone_numbers', []))
                result['addresses'].extend(related_data.get('addresses', []))
                
            except Exception as e:
                logger.debug(f"Could not scrape {related_url}: {str(e)}")
                continue
    
    def _parse_page(self, url: str, html: str) -> Dict[str, Any]:
        """Parse HTML content and extract information"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract company name
            company_name = self._extract_company_name(soup, url)
            
            # Extract contact information
            contact_info = self._extract_contact_info(html)
            
            return {
                'url': url,
                'company_name': company_name,
                'emails': list(set(contact_info.get('emails', []))),  # Remove duplicates
                'phone_numbers': list(set(contact_info.get('phone_numbers', []))),
                'addresses': list(set(contact_info.get('addresses', []))),
                'status': 'pending'
            }
        except Exception as e:
            logger.error(f"Parse error for {url}: {str(e)}")
            return {
                'url': url,
                'company_name': None,
                'emails': [],
                'phone_numbers': [],
                'addresses': [],
                'status': 'error'
            }
    
    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract company name from page"""
        try:
            # Try various common selectors
            selectors = [
                'h1',
                '.company-name',
                '[property="og:site_name"]',
                'meta[name="application-name"]',
                '.logo-text',
                'title'
            ]
            
            for selector in selectors:
                if selector.startswith('['):
                    elem = soup.select_one(selector)
                    if elem:
                        name = elem.get('content')
                        if name:
                            return name
                else:
                    elem = soup.select_one(selector)
                    if elem and elem.get_text(strip=True):
                        return elem.get_text(strip=True)[:100]
            
            # Fallback to domain name
            domain = urlparse(url).netloc.replace('www.', '')
            return domain.split('.')[0].title() if domain else None
            
        except Exception as e:
            logger.debug(f"Error extracting company name: {str(e)}")
            return None
    
    def _extract_contact_info(self, html: str) -> Dict[str, List[str]]:
        """Extract emails, phones, and addresses from HTML"""
        emails = []
        phones = []
        addresses = []
        
        try:
            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = list(set(re.findall(email_pattern, html)))
            
            # Filter out common false positives
            emails = [e for e in emails if not any(
                skip in e.lower() for skip in 
                ['example.com', 'test.com', 'domain.com', 'placeholder']
            )][:10]  # Limit to 10 emails
            
        except Exception as e:
            logger.debug(f"Error extracting emails: {str(e)}")
        
        try:
            # Extract phone numbers (basic patterns)
            phone_patterns = [
                r'\+?1?\s*[-.\s]?\(?([2-9]\d{2})\)?[-.\s]?([2-9]\d{2})[-.\s]?(\d{4})',  # US
                r'\+\d{1,3}[-.\s]?\(??\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
                r'\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # Common
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if isinstance(match, tuple):
                        phone = ''.join(match)
                    else:
                        phone = match
                    if len(phone) >= 7:  # Minimum phone number length
                        phones.append(phone)
            
            phones = list(set(phones))[:10]  # Deduplicate and limit
            
        except Exception as e:
            logger.debug(f"Error extracting phones: {str(e)}")
        
        try:
            # Extract addresses (simple pattern matching)
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for common address containers
            address_selectors = [
                '.address',
                '.contact-address',
                '.location',
                'address',
                '[data-address]',
                '.business-address'
            ]
            
            for selector in address_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    addr_text = elem.get_text(strip=True)
                    if addr_text and len(addr_text) > 10:
                        addresses.append(addr_text[:200])
            
            addresses = list(set(addresses))[:10]  # Deduplicate and limit
            
        except Exception as e:
            logger.debug(f"Error extracting addresses: {str(e)}")
        
        return {
            'emails': emails,
            'phone_numbers': phones,
            'addresses': addresses
        }
