#!/usr/bin/env python3
"""
Google Maps Scraper — 100% bepul, API kerak emas
GitHub: omkarcloud/google-maps-scraper ilhomi asosida
Playwright orqali brauzer avtomatlashtirish
"""

import csv
import json
import sys
import time
from playwright.sync_api import sync_playwright

def scrape_google_maps(query: str, max_results: int = 50) -> list:
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled'
        ])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US'
        )
        page = context.new_page()

        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        print(f"🔍 Qidirilmoqda: {query}")
        print(f"🌐 URL: {search_url}")

        page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
        time.sleep(3)

        # Cookie bannerni yopish
        for selector in ['button[aria-label*="Accept"]', 'button:text("Accept all")', 'button:text("Reject all")']:
            try:
                page.click(selector, timeout=2000)
                break
            except:
                pass

        print(f"📜 Natijalar yuklanmoqda...")

        result_links = []
        scroll_count = 0
        max_scrolls = 15

        while len(result_links) < max_results and scroll_count < max_scrolls:
            links = page.query_selector_all('a[href*="/maps/place/"]')

            for link in links:
                href = link.get_attribute('href')
                if href and '/maps/place/' in href and href not in result_links:
                    result_links.append(href)

            print(f"  ✓ {len(result_links)} ta joy topildi")

            # Scroll
            try:
                panel = page.query_selector('div[role="feed"]')
                if panel:
                    panel.evaluate('el => el.scrollTop += 3000')
                else:
                    page.keyboard.press('End')
            except:
                page.keyboard.press('End')

            time.sleep(2)
            scroll_count += 1

            # Oxirini tekshirish
            try:
                end = page.query_selector('span:has-text("You\'ve reached the end")')
                if end:
                    print("  ✓ Barcha natijalar yuklandi")
                    break
            except:
                pass

        print(f"\n📍 Jami {len(result_links)} ta joy. Ma'lumotlar olinmoqda...\n")

        for i, link in enumerate(result_links[:max_results]):
            try:
                print(f"  [{i+1}/{min(len(result_links), max_results)}] Tekshirilmoqda...")

                page.goto(link, wait_until='domcontentloaded', timeout=20000)
                time.sleep(1.5)

                business = {
                    'name': '',
                    'website': '',
                    'phone': '',
                    'address': '',
                    'rating': '',
                    'reviews': '',
                    'category': '',
                    'google_maps_url': link
                }

                # Nom
                try:
                    name_el = page.query_selector('h1.DUwDvf, h1[class*="fontHeadlineLarge"]')
                    if name_el:
                        business['name'] = name_el.inner_text().strip()
                except:
                    pass

                # Reyting
                try:
                    rating_el = page.query_selector('div.F7nice span[aria-hidden="true"]')
                    if rating_el:
                        business['rating'] = rating_el.inner_text().strip()
                except:
                    pass

                # Izohlar soni
                try:
                    reviews_el = page.query_selector('div.F7nice span[aria-label*="reviews"]')
                    if reviews_el:
                        business['reviews'] = reviews_el.inner_text().strip('()')
                except:
                    pass

                # Kategoriya
                try:
                    cat_el = page.query_selector('button.DkEaL')
                    if cat_el:
                        business['category'] = cat_el.inner_text().strip()
                except:
                    pass

                # Manzil
                try:
                    addr_btn = page.query_selector('button[data-item-id="address"]')
                    if addr_btn:
                        business['address'] = addr_btn.inner_text().strip()
                except:
                    pass

                # Telefon
                try:
                    phone_els = page.query_selector_all('button[data-item-id*="phone"]')
                    for el in phone_els:
                        text = el.inner_text().strip()
                        if text:
                            business['phone'] = text
                            break
                except:
                    pass

                # Veb-sayt — ENG MUHIM
                try:
                    website_el = page.query_selector('a[data-item-id="authority"]')
                    if website_el:
                        business['website'] = website_el.get_attribute('href')
                    else:
                        # Backup
                        all_links = page.query_selector_all('a[href^="http"]')
                        for a in all_links:
                            href = a.get_attribute('href') or ''
                            aria = a.get_attribute('aria-label') or ''
                            if 'google' not in href and ('website' in aria.lower() or 'visit' in aria.lower()):
                                business['website'] = href
                                break
                except:
                    pass

                if business['name']:
                    results.append(business)
                    site = f"🌐 {business['website'][:40]}" if business['website'] else "❌ sayt yo'q"
                    print(f"    ✅ {business['name']} — {site}")

            except Exception as e:
                print(f"    ⚠️  Xato: {str(e)[:60]}")
                continue

        browser.close()

    return results


def save_results(results: list, query: str):
    safe_name = "".join(c if c.isalnum() or c == '_' else '_' for c in query)[:30]

    csv_file = f"results_{safe_name}.csv"
    if results:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\n💾 CSV: {csv_file}")

    json_file = f"results_{safe_name}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON: {json_file}")

    with_website = [r for r in results if r.get('website')]
    print(f"\n📊 Statistika:")
    print(f"   Jami: {len(results)} ta joy")
    print(f"   Veb-sayt bor: {len(with_website)}")
    print(f"   Veb-sayt yo'q: {len(results) - len(with_website)}")

    return csv_file, json_file


def main():
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("🔍 Qidiruv so'rovi (masalan: restaurants Moscow): ").strip()
        if not query:
            query = "restaurants Moscow"

    max_results = 20  # Ko'proq kerak bo'lsa oshiring

    print(f"\n{'='*50}")
    print(f"🗺️  Google Maps Scraper — 100% Bepul")
    print(f"{'='*50}")
    print(f"Qidiruv: {query}")
    print(f"Max: {max_results} ta natija")
    print(f"{'='*50}\n")

    results = scrape_google_maps(query, max_results)

    if results:
        save_results(results, query)
        print(f"\n✅ Tayyor!")
    else:
        print("\n❌ Natija topilmadi")


if __name__ == "__main__":
    main()
