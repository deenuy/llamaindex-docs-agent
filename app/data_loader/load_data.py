import os
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import SimpleDirectoryReader, SummaryIndex, VectorStoreIndex, Settings, StorageContext

from app.utils.config.config_loader import ConfigLoader
from app.utils.logger.logger import setup_logger

# =========================
# ✅ Initial Setup
# =========================
# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger()

# Load environment and config
env = os.getenv("ENVIRONMENT", "dev")
logger.info(f"Environment set to: {env}")

config_loader = ConfigLoader(env)
config = config_loader.load_config()

# =========================
# ✅ Resolve Paths from Config
# =========================
PROJECT_ROOT = os.getcwd()

# Log the full config structure to understand its format
logger.info(f"Config structure: {config.keys()}")

DATA_DIR = os.path.join(PROJECT_ROOT, config["paths"]["data_dir"])
VECTOR_DB_DIR = os.path.join(PROJECT_ROOT, config["paths"]["vector_db_root"])
INDEX_DB_DIR = os.path.join(PROJECT_ROOT, config["paths"]["index_db_dir"])
COLLECTION_NAME = config["paths"]["collection"]

# Ensure required directories exist
for path_name, path in {
    "Data directory": DATA_DIR,
    "Vector DB directory": VECTOR_DB_DIR,
    "Index DB directory": INDEX_DB_DIR,
}.items():
    os.makedirs(path, exist_ok=True)
    logger.info(f"{path_name}: {path}")

# =========================
# ✅ Configure LlamaIndex Settings
# =========================
# Get embedding dimension based on the model
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536  # OpenAI's text-embedding-3-small has 1536 dimensions

Settings.llm = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)
Settings.chunk_size = 1000
Settings.chunk_overlap = 50
Settings.embed_model = OpenAIEmbedding(
    model=EMBED_MODEL,
    api_key=os.getenv("OPENAI_API_KEY")
)

logger.info(f"LlamaIndex settings configured: LLM model: {Settings.llm.model}, Embed model: {Settings.embed_model.model_name}")

# =========================
# ✅ Initialize Qdrant Client
# =========================
# IMPORTANT CHANGE: Use HTTP connection instead of direct file access
# This connects to the Qdrant server started by start_services.sh
HTTP_PORT = 6333  # Default Qdrant HTTP port
qc = QdrantClient(url=f"http://localhost:{HTTP_PORT}")
logger.info(f"Qdrant client initialized with HTTP connection to: http://localhost:{HTTP_PORT}")

# ✅ Check Qdrant health proactively
try:
    collections = qc.get_collections()
    collection_names = [c.name for c in collections.collections]
    logger.info(f"Qdrant is healthy. Existing collections: {collection_names}")
except Exception as e:
    logger.error(f"Qdrant health check failed: {e}")
    raise

# =========================
# ✅ Create or Configure Collection
# =========================
# First check if collection exists
if COLLECTION_NAME not in collection_names:
    logger.info(f"Creating new collection: {COLLECTION_NAME}")

    # Create the collection with proper vector configuration for LlamaIndex
    # IMPORTANT: Must include both text-dense and text vector names for LlamaIndex compatibility
    qc.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "text": rest.VectorParams(
                size=EMBED_DIM,
                distance=rest.Distance.COSINE,
            ),
            "text-dense": rest.VectorParams(  # This is needed for newer LlamaIndex versions
                size=EMBED_DIM,
                distance=rest.Distance.COSINE,
            )
        },
        optimizers_config=rest.OptimizersConfigDiff(
            indexing_threshold=20000  # Indexing threshold for HNSW
        ),
        hnsw_config=rest.HnswConfigDiff(
            m=16,  # Number of connections per node in HNSW graph
            ef_construct=100,  # Controls index quality vs build speed tradeoff
        ),
        on_disk_payload=True,  # Store payload on disk to save RAM
    )
    logger.info(f"Collection {COLLECTION_NAME} created successfully")
else:
    # Check if collection has the right vector dimensions
    collection_info = qc.get_collection(COLLECTION_NAME)
    logger.info(f"Collection vector configuration: {collection_info.config.params.vectors}")

    # If collection exists but doesn't have the right vector config, recreate it
    vector_names = collection_info.config.params.vectors.keys()
    if "text-dense" not in vector_names:
        logger.warning(f"Collection {COLLECTION_NAME} exists but missing required vector names. Recreating...")
        qc.delete_collection(COLLECTION_NAME)

        # Recreate with proper configuration
        qc.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "text": rest.VectorParams(
                    size=EMBED_DIM,
                    distance=rest.Distance.COSINE,
                ),
                "text-dense": rest.VectorParams(
                    size=EMBED_DIM,
                    distance=rest.Distance.COSINE,
                )
            },
            optimizers_config=rest.OptimizersConfigDiff(
                indexing_threshold=20000
            ),
            hnsw_config=rest.HnswConfigDiff(
                m=16,
                ef_construct=100,
            ),
            on_disk_payload=True,
        )
        logger.info(f"Collection {COLLECTION_NAME} recreated successfully")
    else:
        logger.info(f"Collection {COLLECTION_NAME} already exists with proper configuration")

# =========================
# ✅ Configure Vector Store
# =========================
vector_store = QdrantVectorStore(
    collection_name=COLLECTION_NAME,
    client=qc,
    # Don't specify any vector name mapping to let LlamaIndex use its defaults
    enable_hybrid=False  # Set to False until basic functionality is confirmed
)

logger.info(f"Qdrant vector store configured for collection: {COLLECTION_NAME}")

# =========================
# ✅ Load Documents
# =========================
start_time = time.time()
docs = SimpleDirectoryReader(input_dir=DATA_DIR, recursive=True).load_data()
elapsed_time = time.time() - start_time
logger.info(f"{len(docs)} documents loaded from {DATA_DIR} in {elapsed_time:.2f} seconds.")

# =========================
# ✅ Build Vector Index
# =========================
start_time = time.time()
storage_context = StorageContext.from_defaults(vector_store=vector_store)
try:
    logger.info(f"Starting to build vector index with {len(docs)} documents...")
    vector_index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)
    elapsed_time = time.time() - start_time
    logger.info(f"Vector index built successfully in {elapsed_time:.2f} seconds.")
except Exception as e:
    logger.error(f"Error building vector index: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    raise

# =========================
# ✅ Build and Persist Summary Index
# =========================
start_time = time.time()
summary_index = SummaryIndex.from_documents(docs)
summary_index.storage_context.persist(persist_dir=INDEX_DB_DIR)
elapsed_time = time.time() - start_time
logger.info(f"Index database persisted at {INDEX_DB_DIR} in {elapsed_time:.2f} seconds.")

logger.info("✅ Data loading and index building pipeline completed successfully.")