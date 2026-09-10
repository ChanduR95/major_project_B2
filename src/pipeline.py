from pathlib import Path

from src.predictor import predict_image
from src.chatbot import get_chatbot_response


def analyze_kidney_ct(image_path, question):

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"CT image not found: {image_path}"
        )

    # ========================================================
    # STEP 1: SWIN TRANSFORMER CLASSIFICATION
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 1: SWIN TRANSFORMER CLASSIFICATION")
    print("=" * 60)

    prediction = predict_image(
        image_path
    )

    predicted_class = prediction[
        "predicted_class"
    ]

    confidence = prediction[
        "confidence"
    ]

    probabilities = prediction[
        "probabilities"
    ]

    print(
        "Prediction:",
        predicted_class
    )

    print(
        "Confidence:",
        f"{confidence:.2f}%"
    )

    print("\nClass probabilities:")

    for class_name, probability in probabilities.items():

        print(
            f"{class_name}: {probability:.2f}%"
        )


    # ========================================================
    # STEP 2: RAG + GEMINI
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 2: RAG + GEMINI")
    print("=" * 60)

    chatbot_result = get_chatbot_response(
        question=question,
        predicted_class=predicted_class,
        confidence=confidence
    )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "prediction": {
            "predicted_class":
                predicted_class,

            "confidence":
                confidence,

            "probabilities":
                probabilities
        },

        "question":
            question,

        "answer":
            chatbot_result["answer"],

        "retrieved_documents":
            chatbot_result[
                "retrieved_documents"
            ]
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            'Usage: python -m src.pipeline '
            '"uploads\\test_ct.jpg"'
        )

        sys.exit(1)

    image_path = sys.argv[1]

    question = (
        "What does this result mean, "
        "and what precautions should I follow?"
    )

    result = analyze_kidney_ct(
        image_path=image_path,
        question=question
    )

    print("\n" + "=" * 60)
    print("FINAL KIDNEYVISION RESULT")
    print("=" * 60)

    print(
        "\nPredicted class:",
        result["prediction"][
            "predicted_class"
        ]
    )

    print(
        "Confidence:",
        f'{result["prediction"]["confidence"]:.2f}%'
    )

    print(
        "\nUser question:",
        result["question"]
    )

    print("\nAI Advisory:\n")

    print(
        result["answer"]
    )

    print("\n" + "=" * 60)