from pathlib import Path

import timm
import torch


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "kidney_swin_final.pth"


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# LOAD TRAINED SWIN TRANSFORMER
# ============================================================

def load_swin_model():

    # Check model file
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found:\n{MODEL_PATH}"
        )

    print("=" * 60)
    print("LOADING KIDNEY SWIN TRANSFORMER")
    print("=" * 60)

    print("Model path :", MODEL_PATH)
    print("Device     :", DEVICE)

    # --------------------------------------------------------
    # Load saved checkpoint
    # --------------------------------------------------------

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=False
    )

    # --------------------------------------------------------
    # Read model configuration
    # --------------------------------------------------------

    model_name = checkpoint.get(
        "model_name",
        "swin_tiny_patch4_window7_224"
    )

    num_classes = checkpoint.get(
        "num_classes",
        4
    )

    classes = checkpoint.get(
        "classes",
        [
            "Cyst",
            "Normal",
            "Stone",
            "Tumor"
        ]
    )

    # --------------------------------------------------------
    # Rebuild Swin architecture
    # --------------------------------------------------------

    model = timm.create_model(
        model_name,
        pretrained=False,
        num_classes=num_classes
    )

    # --------------------------------------------------------
    # Load YOUR fine-tuned weights
    # --------------------------------------------------------

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    # Move model to device
    model = model.to(DEVICE)

    # Inference mode
    model.eval()

    print("\nModel loaded successfully.")
    print("Architecture :", model_name)
    print("Classes      :", classes)
    print("No. classes  :", num_classes)

    if "test_accuracy" in checkpoint:

        print(
            "Test Accuracy:",
            f"{checkpoint['test_accuracy'] * 100:.2f}%"
        )

    if "macro_f1" in checkpoint:

        print(
            "Macro F1     :",
            f"{checkpoint['macro_f1'] * 100:.2f}%"
        )

    print("=" * 60)

    return model, classes, checkpoint


# ============================================================
# TEST model_loader.py
# ============================================================

if __name__ == "__main__":

    model, classes, checkpoint = load_swin_model()

    print("\nSwin Transformer is ready for inference.")