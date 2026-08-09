# Quick test in python terminal or test script
from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever

dense = DenseRetriever(vectorstore_dir="vectorstore")
sparse = SparseRetriever(vectorstore_dir="vectorstore")

print("Dense results:", dense.retrieve("CVE-2024-3094", top_k=5))
print("Sparse results:", sparse.retrieve("CVE-2024-3094", top_k=5))
