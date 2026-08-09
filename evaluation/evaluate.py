import json
import os
from datetime import datetime
import pandas as pd
from datasets import Dataset
import sys
import types

# Workaround for RAGAS import bug with newer langchain-community
try:
    import langchain_community.chat_models.vertexai
except ModuleNotFoundError:
    stub = types.ModuleType("langchain_community.chat_models.vertexai")
    stub.ChatVertexAI = None
    sys.modules["langchain_community.chat_models.vertexai"] = stub

from ragas import evaluate

from app.core.logger import logger
from app.pipeline.retrieve import RetrievalPipeline
from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import CrossEncoderReranker
from app.rag.llm import LLMEngine
from app.pipeline.rag_pipeline import RAGPipeline
from evaluation.metrics import EVALUATION_METRICS, get_ragas_evaluator_models

DATASET_PATH = "evaluation/datasets/questions.json"
REPORTS_DIR = "evaluation/reports"


def load_evaluation_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_rag_pipeline() -> RAGPipeline:
    logger.info("Initializing RAG Pipeline for Phase 8 evaluation...")
    dense = DenseRetriever(vectorstore_dir="vectorstore")
    sparse = SparseRetriever(vectorstore_dir="vectorstore")
    hybrid = HybridRetriever(dense, sparse)
    reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-base")
    retrieval_pipeline = RetrievalPipeline(hybrid, reranker)

    llm_engine = LLMEngine(
        provider="nvidia",
        model_name="nvidia/nemotron-3-nano-30b-a3b",
        temperature=0.0,
    )

    return RAGPipeline(retrieval_pipeline=retrieval_pipeline, llm_engine=llm_engine)


def run_evaluation():
    logger.info("Starting evaluation execution flow...")
    pipeline = build_rag_pipeline()

    test_cases = load_evaluation_dataset(DATASET_PATH)
    logger.info(f"Loaded {len(test_cases)} evaluation samples from {DATASET_PATH}")

    questions, ground_truths, answers, contexts = [], [], [], []

    for item in test_cases:
        query = item["question"]
        gt = item["ground_truth"]

        logger.info(f"Evaluating Query: {query}")

        retrieval_output = pipeline.retriever.run(raw_query=query, top_n=5)
        reranked_results = retrieval_output.get("results", [])
        chunk_texts = [chunk.text for chunk, _ in reranked_results]

        result = pipeline.answer(question=query, top_n=5)
        generated_answer = result.get("answer", "")

        questions.append(query)
        ground_truths.append(gt)
        answers.append(generated_answer)
        contexts.append(chunk_texts)

    eval_data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }

    ragas_dataset = Dataset.from_dict(eval_data)

    logger.info("Computing RAGAS Evaluation Metrics...")
    eval_llm, eval_embeddings = get_ragas_evaluator_models()

    results = evaluate(
        dataset=ragas_dataset,
        metrics=EVALUATION_METRICS,
        llm=eval_llm,
        embeddings=eval_embeddings,
    )

    df_results = results.to_pandas()
    os.makedirs(REPORTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    json_report_path = os.path.join(REPORTS_DIR, f"evaluation_{timestamp}.json")
    csv_report_path = os.path.join(REPORTS_DIR, f"evaluation_{timestamp}.csv")

    df_results.to_json(json_report_path, orient="records", indent=4)
    df_results.to_csv(csv_report_path, index=False)

    logger.success(
        f"Evaluation finished! Reports saved to:\n - {json_report_path}\n - {csv_report_path}"
    )


if __name__ == "__main__":
    run_evaluation()
