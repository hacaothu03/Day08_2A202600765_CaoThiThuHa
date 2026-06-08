# --- GROUP C6 - RAG PIPELINE PROJECT ---
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Khai báo để import được code từ src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric, FaithfulnessMetric,
    ContextualPrecisionMetric, ContextualRecallMetric
)
from deepeval.test_case import LLMTestCase
from src.task10_generation import generate_with_citation
from group_project.hyde import generate_hypothetical_document

EVAL_MODEL = "gpt-4o-mini"

def load_dataset():
    filepath = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def create_test_cases(dataset, use_hyde=False):
    test_cases = []
    for i, item in enumerate(dataset):
        query = item["input"]
        expected = item["expected_output"]
        
        search_query = query
        if use_hyde:
            search_query = generate_hypothetical_document(query)
            
        print(f"[{'HyDE' if use_hyde else 'Baseline'}] Generating answer for Q{i+1}: {query}")
        result = generate_with_citation(query=query, search_query=search_query)
        
        actual_output = result["answer"]
        retrieval_context = [chunk["content"] for chunk in result["sources"]]
        
        test_case = LLMTestCase(
            input=query,
            actual_output=actual_output,
            expected_output=expected,
            retrieval_context=retrieval_context
        )
        test_cases.append(test_case)
    return test_cases

def run_ab_test():
    dataset = load_dataset()
    
    # ĐỂ TIẾT KIỆM THỜI GIAN VÀ CHI PHÍ API (chạy 15 câu mất khoảng 3-5 phút), 
    # Ta chọn ngẫu nhiên 4 câu (2 câu luật, 2 câu tin tức) để làm A/B Testing Demo
    subset = [dataset[1], dataset[3], dataset[10], dataset[12]]
    
    print("\n" + "="*50)
    print("🚀 ĐANG CHUẨN BỊ ĐỀ THI CHO CONFIG A (KHÔNG HYDE)")
    test_cases_baseline = create_test_cases(subset, use_hyde=False)
    
    print("\n" + "="*50)
    print("🚀 ĐANG CHUẨN BỊ ĐỀ THI CHO CONFIG B (CÓ HYDE)")
    test_cases_hyde = create_test_cases(subset, use_hyde=True)

    metrics = [
        AnswerRelevancyMetric(threshold=0.5, model=EVAL_MODEL),
        FaithfulnessMetric(threshold=0.5, model=EVAL_MODEL),
        ContextualPrecisionMetric(threshold=0.5, model=EVAL_MODEL),
        ContextualRecallMetric(threshold=0.5, model=EVAL_MODEL)
    ]

    print("\n" + "="*50)
    print("⚖️ BẮT ĐẦU CHẤM ĐIỂM CONFIG A (BASELINE)...")
    evaluate(test_cases_baseline, metrics)
    
    print("\n" + "="*50)
    print("⚖️ BẮT ĐẦU CHẤM ĐIỂM CONFIG B (HYDE)...")
    evaluate(test_cases_hyde, metrics)
    
    print("\n✅ KIỂM THỬ A/B HOÀN TẤT!")

if __name__ == "__main__":
    run_ab_test()
