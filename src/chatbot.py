import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import GoogleAPIError

from src.rag import retrieve_context


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")


if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY was not found in .env"
    )


if not GEMINI_MODEL:
    raise ValueError(
        "GEMINI_MODEL was not found in .env"
    )


# ============================================================
# GEMINI MODEL
# ============================================================

llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2
)


# ============================================================
# EXTRACT TEXT FROM GEMINI RESPONSE
# ============================================================

def extract_response_text(response):

    content = response.content

    # New Gemini/LangChain versions may return
    # structured content blocks.
    if isinstance(content, list):

        text_parts = []

        for block in content:

            if isinstance(block, dict):

                text = block.get("text")

                if text:
                    text_parts.append(text)

            elif isinstance(block, str):

                text_parts.append(block)

        return "\n".join(text_parts)

    return str(content)


# ============================================================
# FORMAT RETRIEVED KNOWLEDGE
# ============================================================

def format_rag_context(results):

    context_parts = []

    for number, item in enumerate(
        results,
        start=1
    ):

        document = item["document"]
        metadata = document.metadata

        section = f"""
SOURCE {number}

Condition:
{metadata.get("condition")}

Topic:
{metadata.get("topic")}

Title:
{metadata.get("title")}

Knowledge:
{metadata.get("text")}

Caution:
{metadata.get("caution", "")}

Urgency:
{metadata.get("urgency", "")}
"""

        context_parts.append(section)

    return "\n".join(context_parts)


# ============================================================
# CHATBOT FUNCTION
# ============================================================

def get_chatbot_response(
    question,
    predicted_class,
    confidence
):

    # --------------------------------------------------------
    # Retrieve relevant medical knowledge
    # --------------------------------------------------------

    retrieved_results = retrieve_context(
        question=question,
        predicted_class=predicted_class,
        k=5
    )

    rag_context = format_rag_context(
        retrieved_results
    )


    # --------------------------------------------------------
    # Create grounded prompt
    # --------------------------------------------------------

    prompt = f"""
You are the clinical advisory component of an educational
kidney CT classification research project.

IMPORTANT SAFETY RULES:

1. Do not present the image-classification result as a
   confirmed medical diagnosis.

2. The Swin Transformer prediction is only an AI model output.

3. Base medical information primarily on the supplied
   knowledge-base context.

4. Do not invent information that is missing from the context.

5. Do not prescribe prescription medicines or medication doses.

6. Clearly recommend professional medical assessment when
   appropriate.

7. If symptoms may represent an emergency or serious condition,
   clearly advise urgent medical attention.

8. Do not claim that a high confidence percentage means the
   diagnosis is clinically confirmed.

9. Clearly distinguish general educational information from
   personalized medical advice.

10. Use simple, understandable language.


AI IMAGE CLASSIFIER OUTPUT
--------------------------

Predicted class:
{predicted_class}

Model confidence:
{confidence:.2f}%

This prediction is NOT a confirmed clinical diagnosis.


USER QUESTION
-------------

{question}


RETRIEVED KNOWLEDGE-BASE CONTEXT
--------------------------------

{rag_context}


TASK
----

Answer the user's question using the retrieved context.

Where appropriate, organize the answer into:

- What the result means
- General precautions
- Diet or hydration information
- When medical evaluation is needed
- Warning signs requiring urgent care

Only include sections that are relevant.

Finish with a short statement explaining that the CT
classification is an AI research output and should be
confirmed by a qualified medical professional.
"""


    # --------------------------------------------------------
    # Send grounded prompt to Gemini
    # --------------------------------------------------------

    response = llm.invoke(
        prompt
    )

    answer = extract_response_text(
        response
    )

    return {
        "answer": answer,
        "predicted_class": predicted_class,
        "confidence": confidence,
        "retrieved_documents": retrieved_results
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KIDNEYVISION RAG + GEMINI TEST")
    print("=" * 60)

    # Temporary test values.
    # Later these will come automatically from Swin.
    predicted_class = "Stone"
    confidence = 98.50

    question = (
        "What precautions and diet should I follow?"
    )

    result = get_chatbot_response(
        question=question,
        predicted_class=predicted_class,
        confidence=confidence
    )

    print("\nPrediction:")
    print(result["predicted_class"])

    print("\nConfidence:")
    print(
        f'{result["confidence"]:.2f}%'
    )

    print("\nQuestion:")
    print(question)

    print("\n" + "=" * 60)
    print("GEMINI RAG RESPONSE")
    print("=" * 60)

    print(
        result["answer"]
    )

    print("=" * 60)