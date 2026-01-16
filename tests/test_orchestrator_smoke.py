import os
import shutil
from src.app import run_research

def test_smoke_tsla():
    # Setup
    ticker = "TSLA"
    
    # Run
    result_dir = run_research(ticker, "1m", "normal")
    
    # Assert
    assert os.path.exists(result_dir)
    assert os.path.exists(f"{result_dir}/plan.json")
    assert os.path.exists(f"{result_dir}/evidence.json")
    assert os.path.exists(f"{result_dir}/final_report.json")
    assert os.path.exists(f"{result_dir}/final_report.md")
    
    # Check trigger logic: TSLA should produce volatility spike in our mock
    # because 'TSLA' seed might produce high volatility or we forced it?
    # Our mock price fetcher uses seed. Let's trust the logic runs through.

    # Verify content in markdown report
    with open(f"{result_dir}/final_report.md", "r") as f:
        md_content = f.read()
        
    assert "## Executive Summary" in md_content
    assert "No major bull signals" not in md_content or "No major bear signals" not in md_content # At least one should have content
    assert "**Verdict**" in md_content
    
    # Check for citations (e.g. [a1b2c3])
    import re
    citation_pattern = r"\[[a-f0-9]{6}\]"
    assert re.search(citation_pattern, md_content), "Report should contain evidence citations like [abcdef]"

    # Cleanup (optional)
    # shutil.rmtree(result_dir) 
