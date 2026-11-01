# scraper.py
import nest_asyncio
nest_asyncio.apply()

from playwright.sync_api import sync_playwright

def fetch_website_content(url):
    """
    Sử dụng Playwright để mở trang web, đợi JavaScript render xong 
    và lấy toàn bộ text hoặc nội dung HTML của trang.
    """
    with sync_playwright() as p:
        # Khởi chạy trình duyệt ẩn danh (headless=True)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        try:
            print(f"Đang cào dữ liệu từ: {url}...")
            # Di chuyển đến URL và đợi cho đến khi mạng ổn định (domcontentloaded hoặc networkidle)
            page.goto(url, wait_until="domcontentloaded")
            
            # Đợi thêm một chút nếu trang web load JS quá nặng (tùy chọn)
            page.wait_for_timeout(2000) 
            
            # Cách 1: Lấy text thuần túy đã loại bỏ các thẻ HTML (Khuyên dùng cho AI summarize)
            content = page.locator("body").inner_text()
            
            # Cách 2: Nếu muốn lấy toàn bộ HTML raw thì dùng dòng dưới:
            # content = page.content()
            
            return content
            
        except Exception as e:
            print(f"Có lỗi xảy ra khi cào web: {e}")
            return ""
        finally:
            browser.close()

# Test nhanh file scraper nếu chạy độc lập
if __name__ == "__main__":
    test_url = "https://openai.com"
    result = fetch_website_content(test_url)
    print("\n--- Kết quả cào thử (500 ký tự đầu tiên) ---")
    print(result[:500])