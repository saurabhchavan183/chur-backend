from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
from bs4 import BeautifulSoup

app = FastAPI()

# Allow your local React app and future Render frontend to connect
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
    url = f"https://codeforces.com/contest/{contest_id}/problem/{index}"
    
    # cloudscraper mimics a real browser to bypass Cloudflare
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        response = scraper.get(url, timeout=15.0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch problem. Codeforces returned status code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    statement_div = soup.find("div", class_="problem-statement")
    
    if not statement_div:
        raise HTTPException(status_code=404, detail="Problem statement not found in the HTML. Cloudflare may have blocked the request.")
    
    test_cases = []
    sample_tests = statement_div.find("div", class_="sample-test")
    
    if sample_tests:
        inputs = sample_tests.find_all("div", class_="input")
        outputs = sample_tests.find_all("div", class_="output")
        
        for in_div, out_div in zip(inputs, outputs):
            in_pre = in_div.find("pre")
            out_pre = out_div.find("pre")
            
            # Extract text, preserving multiline format
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