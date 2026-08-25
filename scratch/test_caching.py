from backend.llm import build_llm
from langchain_core.messages import HumanMessage
import time

def test_caching():
    llm = build_llm(model_name="meta-llama/llama-3.1-8b-instruct")
    
    msg = [HumanMessage(content="Hello, what is 2+2? Only output the number.")]
    
    print("First call (should take a moment)...")
    start = time.time()
    res1 = llm.invoke(msg)
    elapsed1 = time.time() - start
    print(f"Result: {res1.content}")
    print(f"Time: {elapsed1:.2f}s")
    
    print("\nSecond call (should be instant from cache)...")
    start = time.time()
    res2 = llm.invoke(msg)
    elapsed2 = time.time() - start
    print(f"Result: {res2.content}")
    print(f"Time: {elapsed2:.2f}s")
    
    if elapsed2 < 0.05:
        print("\nCaching is working!")
    else:
        print("\nCaching might not be working as expected.")

if __name__ == "__main__":
    test_caching()
