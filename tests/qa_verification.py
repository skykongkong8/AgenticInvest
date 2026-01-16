import os
import sys
import glob
import json
import subprocess
from pathlib import Path

def run_cli(ticker):
    print(f"Running CLI for {ticker}...")
    cmd = [sys.executable, "-m", "src.cli", "--ticker", ticker, "--horizon", "1m", "--risk", "normal"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("CLI Failed!")
        print(result.stderr)
        sys.exit(1)
    print("CLI completed.")

def get_latest_run_dir():
    runs = glob.glob("runs/*")
    if not runs:
        return None
    return max(runs, key=os.path.getmtime)

def analyze_run(run_dir):
    print(f"Analyzing run: {run_dir}")
    
    # Check JSON Report
    json_path = Path(run_dir) / "final_report.json"
    if not json_path.exists():
        print("final_report.json missing!")
        return False
        
    with open(json_path, "r") as f:
        report = json.load(f)
        
    verdict = report.get("verdict")
    print(f"Verdict: {verdict}")
    if verdict not in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "DO_NOT_TOUCH"]:
        print("Invalid verdict label!")
        return False
        
    rationale = report.get("rationale", {})
    bull = rationale.get("bull_case", "")
    bear = rationale.get("bear_case", "")
    
    if not bull and not bear:
        print("Rationale missing bull/bear cases!")
        return False
        
    # Check for citations in rationale
    import re
    citation_pattern = r"\[[a-f0-9]{6}\]"
    
    citations_bull = re.findall(citation_pattern, bull)
    citations_bear = re.findall(citation_pattern, bear)
    print(f"Citations in Bull Case: {len(citations_bull)}")
    print(f"Citations in Bear Case: {len(citations_bear)}")
    
    if len(citations_bull) + len(citations_bear) == 0:
        print("No citations found in rationale!")
        return False

    # Check Markdown Report
    md_path = Path(run_dir) / "final_report.md"
    if not md_path.exists():
        print("final_report.md missing!")
        return False
        
    with open(md_path, "r") as f:
        md_content = f.read()
        
    # Count total citations in MD
    all_citations = re.findall(citation_pattern, md_content)
    unique_citations = set(all_citations)
    print(f"Total Citations in MD: {len(all_citations)}")
    print(f"Unique Citations in MD: {len(unique_citations)}")
    
    if len(unique_citations) < 5:
        print(f"FAILURE: Expected at least 5 unique citations, found {len(unique_citations)}")
        return False
        
    return True

def run_pytest():
    print("\nRunning pytest...")
    cmd = [sys.executable, "-m", "pytest", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Pytest failed!")
        print(result.stderr)
        return False
    return True

def main():
    ticker = "TSLA"
    run_cli(ticker)
    
    latest_run = get_latest_run_dir()
    if not latest_run:
        print("No run directory found.")
        sys.exit(1)
        
    passed = analyze_run(latest_run)
    
    if not passed:
        print("\nFAILURE: Phase 4 Verification Failed.")
        sys.exit(1)
    else:
        print("\nSUCCESS: Phase 4 Verification Passed.")
        
    tests_passed = run_pytest()
    if not tests_passed:
        sys.exit(1)
        
    print("\nQA Verification Complete.")

if __name__ == "__main__":
    main()
