from pathlib import Path
import json

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

KNOWLEDGE_BASE_PATH = (
    BASE_DIR
    / "knowledge_base"
    / "data"
    / "knowledge_base.jsonl"
)

VECTOR_STORE_DIR = (
    BASE_DIR
    / "vector_store"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# CONDITION NORMALIZATION
# ============================================================

def normalize_condition(condition):

    if condition is None:
        return None

    condition = condition.strip().lower()

    aliases = {
        "tumour": "tumor",
        "tumor": "tumor",
        "stone": "stone",
        "cyst": "cyst",
        "normal": "normal"
    }

    return aliases.get(
        condition,
        condition
    )


# ============================================================
# LOAD KNOWLEDGE-BASE RECORDS
# ============================================================

def load_knowledge_base():

    if not KNOWLEDGE_BASE_PATH.exists():

        raise FileNotFoundError(
            f"Knowledge base not found:\n"
            f"{KNOWLEDGE_BASE_PATH}"
        )

    documents = []

    total_records = 0
    indexed_records = 0

    with open(
        KNOWLEDGE_BASE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            total_records += 1

            # Only index approved-for-index records
            if not record.get(
                "index_eligible",
                False
            ):
                continue

            embedding_text = record.get(
                "embedding_text"
            )

            if not embedding_text:
                continue

            indexed_records += 1

            metadata = {
                "id":
                    record.get("id"),

                "condition":
                    record.get("condition"),

                "applies_to":
                    record.get("applies_to", []),

                "topic":
                    record.get("topic"),

                "title":
                    record.get("title"),

                "urgency":
                    record.get("urgency"),

                "population":
                    record.get("population"),

                "caution":
                    record.get("caution", ""),

                "clinical_review_status":
                    record.get(
                        "clinical_review_status"
                    ),

                "patient_care_approved":
                    record.get(
                        "patient_care_approved"
                    ),

                # Keep the actual medical text
                "text":
                    record.get("text", ""),

                # Keep source information
                "source_citations":
                    json.dumps(
                        record.get(
                            "source_citations",
                            []
                        ),
                        ensure_ascii=False
                    )
            }

            document = Document(
                page_content=embedding_text,
                metadata=metadata
            )

            documents.append(document)

    print(
        "Total KB records :",
        total_records
    )

    print(
        "Indexable records:",
        indexed_records
    )

    return documents


# ============================================================
# CREATE EMBEDDING MODEL
# ============================================================

def get_embeddings():

    print(
        "Loading embedding model..."
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        }
    )

    print(
        "Embedding model loaded."
    )

    return embeddings


# ============================================================
# BUILD VECTOR STORE
# ============================================================

def build_vector_store():

    documents = load_knowledge_base()

    if len(documents) == 0:

        raise RuntimeError(
            "No indexable knowledge-base "
            "records were found."
        )

    embeddings = get_embeddings()

    print(
        "\nCreating FAISS vector index..."
    )

    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vector_store.save_local(
        str(VECTOR_STORE_DIR)
    )

    print(
        "\nFAISS index created successfully."
    )

    print(
        "Saved to:",
        VECTOR_STORE_DIR
    )

    return vector_store


# ============================================================
# LOAD EXISTING VECTOR STORE
# ============================================================

def load_vector_store():

    index_file = (
        VECTOR_STORE_DIR
        / "index.faiss"
    )

    if not index_file.exists():

        print(
            "Vector index does not exist."
        )

        print(
            "Creating it now..."
        )

        return build_vector_store()

    embeddings = get_embeddings()

    print(
        "Loading existing FAISS index..."
    )

    vector_store = FAISS.load_local(
        str(VECTOR_STORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    print(
        "FAISS index loaded."
    )

    return vector_store


# ============================================================
# RAG RETRIEVAL
# ============================================================

def retrieve_context(
    question,
    predicted_class=None,
    k=5
):

    predicted_condition = normalize_condition(
        predicted_class
    )

    vector_store = load_vector_store()

    # --------------------------------------------------------
    # We use the Swin prediction as a retrieval HINT,
    # not as an absolute medical fact.
    # --------------------------------------------------------

    query = question

    if predicted_condition:

        query = (
            f"Kidney image classifier hint: "
            f"{predicted_condition}. "
            f"User question: {question}"
        )

    # Retrieve more than we finally return
    candidates = (
        vector_store
        .similarity_search_with_score(
            query,
            k=max(k * 3, 10)
        )
    )

    selected = []
    seen_ids = set()

    # --------------------------------------------------------
    # Prefer relevant predicted-class + shared records,
    # but do NOT strictly restrict retrieval to that class.
    # --------------------------------------------------------

    for document, score in candidates:

        record_id = document.metadata.get(
            "id"
        )

        if record_id in seen_ids:
            continue

        condition = document.metadata.get(
            "condition"
        )

        applies_to = document.metadata.get(
            "applies_to",
            []
        )

        relevant_to_prediction = (
            predicted_condition is None
            or condition == "shared"
            or condition == predicted_condition
            or predicted_condition in applies_to
        )

        if relevant_to_prediction:

            selected.append(
                {
                    "document": document,
                    "score": float(score)
                }
            )

            seen_ids.add(record_id)

        if len(selected) >= k:
            break

    # --------------------------------------------------------
    # If filtering left too few documents,
    # fill remaining slots from semantic results.
    # --------------------------------------------------------

    if len(selected) < k:

        for document, score in candidates:

            record_id = document.metadata.get(
                "id"
            )

            if record_id in seen_ids:
                continue

            selected.append(
                {
                    "document": document,
                    "score": float(score)
                }
            )

            seen_ids.add(record_id)

            if len(selected) >= k:
                break

    return selected


# ============================================================
# TEST RAG DIRECTLY
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "KIDNEY RAG TEST"
    )

    print(
        "=" * 60
    )

    question = (
        "What precautions and diet "
        "should I follow?"
    )

    predicted_class = "Stone"

    results = retrieve_context(
        question=question,
        predicted_class=predicted_class,
        k=5
    )

    print(
        "\nPrediction hint:",
        predicted_class
    )

    print(
        "Question:",
        question
    )

    print(
        "\nRetrieved records:"
    )

    print(
        "-" * 60
    )

    for index, item in enumerate(
        results,
        start=1
    ):

        document = item[
            "document"
        ]

        metadata = document.metadata

        print(
            f"\nRESULT {index}"
        )

        print(
            "ID:",
            metadata.get("id")
        )

        print(
            "Condition:",
            metadata.get("condition")
        )

        print(
            "Topic:",
            metadata.get("topic")
        )

        print(
            "Title:",
            metadata.get("title")
        )

        print(
            "Text:",
            metadata.get("text")
        )

        print(
            "-" * 60
        )