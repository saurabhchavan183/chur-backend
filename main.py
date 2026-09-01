from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Churbo Backend is Live"}

@app.get("/api/problem/{contest_id}/{index}")
def get_problem(contest_id: str, index: str):
    urls = [
        f"https://codeforces.com/contest/{contest_id}/problem/{index}",
        f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
    ]
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    
    html_content = None
    last_status = 404
    
    for url in urls:
        try:
            resp = scraper.get(url, timeout=15.0)
            if resp.status_code == 200 and "problem-statement" in resp.text:
                html_content = resp.text
                break
            last_status = resp.status_code
        except Exception as e:
            continue
            
    if not html_content:
        raise HTTPException(
            status_code=last_status, 
            detail="Problem statement could not be retrieved. Codeforces may have triggered a Cloudflare challenge on the server IP."
        )
        
    soup = BeautifulSoup(html_content, "html.parser")
    statement_div = soup.find("div", class_="problem-statement")
    
    if not statement_div:
        raise HTTPException(status_code=404, detail="Problem statement element not found in page.")
        
    test_cases = []
    sample_tests = statement_div.find("div", class_="sample-test")
    
    if sample_tests:
        inputs = sample_tests.find_all("div", class_="input")
        outputs = sample_tests.find_all("div", class_="output")
        
        for in_div, out_div in zip(inputs, outputs):
            in_pre = in_div.find("pre")
            out_pre = out_div.find("pre")
            
            in_text = in_pre.get_text(separator="\n").strip() if in_pre else ""
            out_text = out_pre.get_text(separator="\n").strip() if out_pre else ""
            
            test_cases.append({
                "input": in_text,
                "expected": out_text
            })
            
    return {
        "html": str(statement_div),
        "testCases": test_cases
    }