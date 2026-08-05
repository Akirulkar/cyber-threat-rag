import os
import glob
import shutil
import logging
from app.pipeline.build_index import run_build_pipeline
from app.vectorstore.faiss_store import FAISSVectorStore
from app.embedding.embedder import TextEmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mini_build_pipeline(
    raw_data_dir: str = "data/raw",
    test_vectorstore_dir: str = "vectorstore_test",
    max_test_files: int = 10,
    batch_size: int = 5,
):
    """Runs a quick end-to-end test of the ingestion-to-FAISS pipeline on a small subset of files."""
    logger.info("Starting Mini-Pipeline Test...")

    # 1. Discover files and select a mini subset
    all_files = glob.glob(os.path.join(raw_data_dir, "**/*.json"), recursive=True)
    if not all_files:
        logger.error(f"No raw JSON files found in {raw_data_dir} to test.")
        return

    test_files = all_files[:max_test_files]
    logger.info(
        f"Selected {len(test_files)} files out of {len(all_files)} for testing."
    )

    # 2. Run pipeline into an isolated test directory
    try:
        run_build_pipeline(
            raw_data_dir=raw_data_dir,
            vectorstore_dir=test_vectorstore_dir,
            chunk_size=300,
            chunk_overlap=50,
            batch_size=batch_size,
            max_files=max_test_files,  # <--- Ensure this argument is passed!
        )

        # 3. Verify that test files were written to disk
        index_path = os.path.join(test_vectorstore_dir, "faiss.index")
        metadata_path = os.path.join(test_vectorstore_dir, "metadata.pkl")

        assert os.path.exists(index_path), "faiss.index was not created!"
        assert os.path.exists(metadata_path), "metadata.pkl was not created!"

        # 4. Load the generated test store and check chunk counts
        store = FAISSVectorStore.load(test_vectorstore_dir)
        total_indexed = store.index.ntotal
        logger.info(
            f"Verification Success! Total vectors in test index: {total_indexed}"
        )
        assert total_indexed > 0, "FAISS index was created but contains 0 vectors."

        # 5. Quick sanity retrieval query test
        embedder = TextEmbedder()
        query_vec = embedder.embed_query("vulnerability privilege escalation")
        results = store.search(query_vec, top_k=2)

        assert len(results) > 0, "Retrieval returned no results from test store!"
        logger.info("\n--- Test Query Retrieval Sample ---")
        for chunk, score in results:
            logger.info(
                f"Score: {score:.4f} | ID: {chunk.chunk_id} | Title: {chunk.metadata.title}"
            )

        logger.info("\n✅ PIPELINE TEST PASSED SUCCESSFULLY!")

    finally:
        # Cleanup test vectorstore directory after run
        if os.path.exists(test_vectorstore_dir):
            shutil.rmtree(test_vectorstore_dir)
            logger.info(
                f"Cleaned up temporary test directory: '{test_vectorstore_dir}'"
            )


if __name__ == "__main__":
    test_mini_build_pipeline()
