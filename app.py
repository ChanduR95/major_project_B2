from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename

from src.pipeline import analyze_kidney_ct


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


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
# START FLASK SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )