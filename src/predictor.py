from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from src.model_loader import load_swin_model, DEVICE


# Load trained Swin model
model, classes, checkpoint = load_swin_model()


# Same preprocessing used during testing
IMAGE_SIZE = 224

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=IMAGENET_MEAN,
        std=IMAGENET_STD
    )
])


def predict_image(image_path):

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # Open image
    image = Image.open(
        image_path
    ).convert("RGB")

    # Preprocess
    image_tensor = transform(
        image
    ).unsqueeze(0).to(DEVICE)

    # Prediction
    model.eval()

    with torch.no_grad():

        outputs = model(image_tensor)

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

    confidence, predicted_index = torch.max(
        probabilities,
        dim=1
    )

    predicted_index = predicted_index.item()

    predicted_class = classes[
        predicted_index
    ]

    confidence = confidence.item() * 100

    class_probabilities = {}

    for i, class_name in enumerate(classes):

        class_probabilities[class_name] = round(
            probabilities[0][i].item() * 100,
            2
        )

    return {
        "predicted_class": predicted_class,
        "confidence": round(confidence, 2),
        "probabilities": class_probabilities
    }


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            'Usage: python -m src.predictor "uploads\\test_ct.jpg"'
        )

        sys.exit(1)

    image_path = sys.argv[1]

    result = predict_image(
        image_path
    )

    print("\n" + "=" * 50)
    print("KIDNEY CT CLASSIFICATION")
    print("=" * 50)

    print(
        "Prediction:",
        result["predicted_class"]
    )

    print(
        "Confidence:",
        f'{result["confidence"]}%'
    )

    print("\nProbabilities:")

    for class_name, probability in result[
        "probabilities"
    ].items():

        print(
            f"{class_name}: {probability}%"
        )

    print("=" * 50)