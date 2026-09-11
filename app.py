from pathlib import Path
import os
import secrets
from uuid import uuid4

from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src.pipeline import analyze_kidney_ct
from src.chatbot import get_chatbot_response


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
chat_context = URLSafeTimedSerializer(
    os.getenv("SECRET_KEY") or secrets.token_hex(32),
    salt="clinical-advisory"
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png"
}

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)


# ============================================================
# CHECK FILE TYPE
# ============================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "OK"
    })


# ============================================================
# ANALYZE CT IMAGE
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    # --------------------------------------------------------
    # Check image
    # --------------------------------------------------------

    if "image" not in request.files:

        return jsonify({
            "error":
                "No CT image was uploaded."
        }), 400


    image = request.files["image"]

    if image.filename == "":

        return jsonify({
            "error":
                "No image was selected."
        }), 400


    if not allowed_file(
        image.filename
    ):

        return jsonify({
            "error":
                "Only JPG, JPEG and PNG images are allowed."
        }), 400


    # --------------------------------------------------------
    # Get user question
    # --------------------------------------------------------

    question = request.form.get(
        "question",
        ""
    ).strip()

    if not question:

        question = (
            "What does this result mean "
            "and what precautions should I follow?"
        )


    # --------------------------------------------------------
    # Create safe unique filename
    # --------------------------------------------------------

    original_filename = secure_filename(
        image.filename
    )

    extension = original_filename.rsplit(
        ".",
        1
    )[1].lower()

    unique_filename = (
        f"{uuid4().hex}.{extension}"
    )

    image_path = (
        UPLOAD_FOLDER
        / unique_filename
    )


    try:

        # ----------------------------------------------------
        # Save image temporarily
        # ----------------------------------------------------

        image.save(
            image_path
        )


        # ----------------------------------------------------
        # SWIN + RAG + GEMINI
        # ----------------------------------------------------

        result = analyze_kidney_ct(
            image_path=image_path,
            question=question
        )


        prediction = result[
            "prediction"
        ]


        # ----------------------------------------------------
        # JSON RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success":
                True,

            "prediction":
                prediction[
                    "predicted_class"
                ],

            "confidence":
                prediction[
                    "confidence"
                ],

            "probabilities":
                prediction[
                    "probabilities"
                ],

            "question":
                result[
                    "question"
                ],

            "advisory":
                result[
                    "answer"
                ],

            "chat_context": chat_context.dumps({
                "predicted_class": prediction["predicted_class"],
                "confidence": float(prediction["confidence"])
            }),

            "disclaimer":
                (
                    "This system is an educational "
                    "AI research prototype and does "
                    "not provide a confirmed medical "
                    "diagnosis."
                )
        })


    except Exception as error:

        print(
            "\nERROR:",
            str(error)
        )

        return jsonify({
            "success":
                False,

            "error":
                str(error)
        }), 500


    finally:

        # ----------------------------------------------------
        # Remove temporary uploaded image
        # ----------------------------------------------------

        if image_path.exists():

            try:
                image_path.unlink()

            except Exception:
                pass


# ============================================================
# FOLLOW-UP CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send a JSON message."), 400

    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="Please enter a message."), 400
    message = message.strip()
    if len(message) > 2000:
        return jsonify(error="Please keep your message under 2,000 characters."), 400

    token = data.get("chat_context")
    if not isinstance(token, str) or not token:
        return jsonify(error="Analyze a CT image before starting a conversation."), 400
    try:
        prediction = chat_context.loads(token, max_age=24 * 60 * 60)
    except BadSignature:
        return jsonify(error="This analysis session has expired. Please analyze the image again."), 400

    history = data.get("history", [])
    if not isinstance(history, list) or len(history) > 20:
        return jsonify(error="Send at most 20 previous messages."), 400
    for index, turn in enumerate(history):
        expected_role = "user" if index % 2 == 0 else "assistant"
        if (
            not isinstance(turn, dict)
            or turn.get("role") != expected_role
            or not isinstance(turn.get("content"), str)
            or not turn["content"].strip()
            or len(turn["content"]) > 12000
        ):
            return jsonify(error="Invalid conversation history."), 400
    if len(history) % 2:
        return jsonify(error="Conversation history must contain completed replies."), 400

    try:
        result = get_chatbot_response(
            question=message,
            predicted_class=prediction["predicted_class"],
            confidence=prediction["confidence"],
            history=history
        )
        answer = result.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            return jsonify(error="The assistant returned an empty reply. Please try again."), 502
        return jsonify(success=True, answer=answer)
    except Exception:
        return jsonify(error="The assistant could not reply right now. Please try sending your message again."), 502


# ============================================================
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8765,
        debug=False
    )
