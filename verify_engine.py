import os
import sys
import numpy as np

# Add the project directory to sys.path so we can import 'app'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.recommender import ContentBasedRecommender, clean_and_tokenize

def run_tests():
    print("=== STARTING MATHEMATICAL ENGINE VALIDATION ===")
    
    csv_path = os.path.join("dataset", "raw_skills.csv")
    if not os.path.exists(csv_path):
        print(f"FAILED: Dataset not found at {csv_path}")
        return False
        
    recommender = ContentBasedRecommender(csv_path)
    print("Dataset loaded successfully.")
    print(f"Total vocabulary size: {len(recommender.vocabulary)} terms.")
    print(f"First 10 terms in vocab: {recommender.vocabulary[:10]}")
    
    # Test 1: Cosine Similarity mathematical properties
    print("\n--- Test 1: Cosine Similarity Core Math ---")
    vec_a = np.array([1.0, 1.0, 0.0])
    vec_b = np.array([1.0, 1.0, 0.0])
    vec_c = np.array([0.0, 0.0, 1.0])
    vec_d = np.array([1.0, 0.0, 0.0])
    
    sim_ab = recommender.get_cosine_similarity(vec_a, vec_b)
    sim_ac = recommender.get_cosine_similarity(vec_a, vec_c)
    sim_ad = recommender.get_cosine_similarity(vec_a, vec_d)
    
    print(f"Sim(A, B) [Perfect Alignment - expected ~1.0]: {sim_ab:.4f}")
    print(f"Sim(A, C) [Orthogonal - expected ~0.0]: {sim_ac:.4f}")
    print(f"Sim(A, D) [Partial Angle - expected ~0.7071]: {sim_ad:.4f}")
    
    assert abs(sim_ab - 1.0) < 1e-6, "Perfect similarity test failed!"
    assert abs(sim_ac - 0.0) < 1e-6, "Orthogonal similarity test failed!"
    assert abs(sim_ad - 0.7071) < 1e-3, "Partial similarity test failed!"
    print("[PASS] Test 1 Passed: Cosine similarity mathematics are correct.")

    # Test 2: Clean & Tokenize Utility
    print("\n--- Test 2: Text Cleaning & Tokenization ---")
    raw_text = "Python Developer, building cool systems! Docker & Cloud automation."
    tokens = clean_and_tokenize(raw_text)
    print(f"Raw: '{raw_text}'")
    print(f"Tokens: {tokens}")
    expected_removed = {'developer', 'systems', 'and', 'for', 'or'}
    for r in expected_removed:
        assert r not in tokens, f"Stopword '{r}' was not removed!"
    print("[PASS] Test 2 Passed: Stop words and non-alphanumeric characters filtered properly.")

    # Test 3: Cold Start Detection
    print("\n--- Test 3: Cold Start Scenario ---")
    results = recommender.recommend(skills=[], interests=[], goals=[], top_n=3)
    print(f"Empty Input results -> cold_start = {results['cold_start']}, recommendations = {results['recommendations']}")
    assert results["cold_start"] is True, "Cold start not detected for empty list!"
    
    results_unknown = recommender.recommend(skills=["xyz123abc"], interests=["nonexistentword"], goals=[], top_n=3)
    print(f"Unknown Input results -> cold_start = {results_unknown['cold_start']}")
    assert results_unknown["cold_start"] is True, "Cold start not detected for out-of-vocabulary list!"
    print("[PASS] Test 3 Passed: Cold Start handled correctly.")

    # Test 4: Dynamic Matching Accuracy
    print("\n--- Test 4: Dynamic Matching Accuracy ---")
    # Case A: AI Enthusiast
    print("Case A: AI Enthusiast inputs (Python, PyTorch, Deep Learning)")
    res_ai = recommender.recommend(
        skills=["python", "pytorch"],
        interests=["deep-learning", "large-language-models"],
        goals=["build neural networks"],
        top_n=3
    )
    print("Top Recommendations:")
    for i, r in enumerate(res_ai["recommendations"]):
        print(f"  {i+1}. {r['role']} (Score: {r['similarity_score']:.4f}) - Matches: {r['matched_skills']}")
    
    assert res_ai["recommendations"][0]["role"] == "AI Engineer", "Case A failed to rank AI Engineer first!"
    print("[PASS] Case A Passed: Matches AI Engineer correctly.")

    # Case B: Cloud / Infrastructure Automation
    print("\nCase B: Infrastructure / DevOps inputs (Kubernetes, AWS, Terraform)")
    res_devops = recommender.recommend(
        skills=["kubernetes", "aws", "terraform"],
        interests=["automation", "ci-cd"],
        goals=["cloud pipelines"],
        top_n=3
    )
    print("Top Recommendations:")
    for i, r in enumerate(res_devops["recommendations"]):
        print(f"  {i+1}. {r['role']} (Score: {r['similarity_score']:.4f}) - Matches: {r['matched_skills']}")
        
    assert res_devops["recommendations"][0]["role"] == "DevOps Engineer", "Case B failed to rank DevOps Engineer first!"
    print("[PASS] Case B Passed: Matches DevOps Engineer correctly.")

    # Case C: Web Frontend Developer
    print("\nCase C: Frontend Developer inputs (React, TailwindCSS, CSS3)")
    res_fe = recommender.recommend(
        skills=["react", "tailwindcss", "css3"],
        interests=["ui-ux", "web-dev"],
        goals=["beautiful responsive interface"],
        top_n=3
    )
    print("Top Recommendations:")
    for i, r in enumerate(res_fe["recommendations"]):
        print(f"  {i+1}. {r['role']} (Score: {r['similarity_score']:.4f}) - Matches: {r['matched_skills']}")
        
    assert res_fe["recommendations"][0]["role"] == "Frontend Engineer", "Case C failed to rank Frontend Engineer first!"
    print("[PASS] Case C Passed: Matches Frontend Engineer correctly.")

    print("\n=============================================")
    print("ALL MATHEMATICAL TESTS PASSED SUCCESSFULLY! [OK]")
    print("=============================================")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
