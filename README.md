# KidneyVision SwinLLM

## Kidney CT Classification Using Swin Transformer with LangChain-Powered RAG Chatbot

KidneyVision SwinLLM is an AI-based kidney CT image analysis system developed as an academic research project.

The system uses a fine-tuned **Swin Transformer** to classify kidney CT images into four categories:

- Cyst
- Normal
- Stone
- Tumor

After classification, the predicted class and model confidence are passed to a **Retrieval-Augmented Generation (RAG)** pipeline. Relevant kidney-related medical information is retrieved from a local knowledge base using **FAISS** and **Sentence Transformers**.

The retrieved knowledge is then provided to a **Gemini LLM through LangChain** to generate an educational advisory response.

A Flask-based web interface allows users to upload kidney CT images, view prediction probabilities, and receive RAG-grounded information.

After an analysis, the **Clinical Advisory** box supports a conversation with the
Gemini assistant. Type a follow-up question and select **Send message** or press
Enter (Shift + Enter adds a new line). Replies use the scan result, relevant
knowledge, and the most recent 10 exchanges. Failed messages remain in the input
so they can be sent again. Starting another analysis or reloading the page clears
the conversation.

The `/chat` endpoint uses a signed analysis context returned by `/analyze`;
follow-up messages do not upload or classify the image again. Context expires
after 24 hours. For multiple server workers or sessions that survive a server
restart, configure the same private `SECRET_KEY` for every worker. Without it,
the app generates a temporary signing key at startup.

---

## Project Architecture

```text
Kidney CT Image
        |
        v
Image Preprocessing
224 x 224
        |
        v
Swin Transformer
        |
        v
4-Class Classification
        |
        +----------------------------+
        |                            |
        v                            v
Predicted Class                Confidence Score
Cyst / Normal /
Stone / Tumor
        |
        v
RAG Retrieval
        |
        v
Sentence Transformer Embeddings
        |
        v
FAISS Vector Store
        |
        v
Kidney Knowledge Base
        |
        v
Relevant Context
        |
        v
LangChain
        |
        v
Gemini LLM
        |
        v
Educational Advisory
        |
        v
Flask Web Interface

Features
 ->Kidney CT image upload
 ->Four-class kidney CT classification
 ->Swin Transformer-based image classifier
 ->Prediction confidence score
 ->Individual probability for all four classes
 ->Local kidney medical knowledge base
 ->Retrieval-Augmented Generation
 ->FAISS vector similarity search
 ->Sentence Transformer embeddings
 ->LangChain integration
 ->Gemini-powered response generation
 ->Flask web application
 ->Responsive frontend
 ->CT image preview
 ->Animated probability visualization
 ->Medical safety disclaimer


 Class    Description                                        
 ------  -------------------------------------------------- 
 Cyst   - Kidney CT images containing cyst-related findings  
 Normal - Kidney CT images without the target abnormalities  
 Stone  - Kidney CT images containing kidney stones          
 Tumor  - Kidney CT images containing tumor-related findings 


Swin Transformer Model

The image classification component uses:
swin_tiny_patch4_window7_224

The model receives RGB kidney CT images resized to:
224 x 224
ImageNet normalization is used before inference.

Model Performance
Final evaluation on the held-out test set:
 Metric             Result 
 -----------------  -----: 
 Test Accuracy      98.88% 
 Macro Precision    98.24% 
 Macro Recall       98.80% 
 Macro F1 Score     98.50% 
 Weighted F1 Score  98.88% 

The final test set contained:1790 images

Correct predictions:1770

Incorrect predictions:20

Confusion Matrix
             Predicted
             Cyst Normal Stone Tumor

Cyst          477    0    10     6
Normal          0  751     0     0
Stone           1    1   202     0
Tumor           0    2     0   340

The reported evaluation is image-level performance from the project dataset and should not be interpreted as clinical diagnostic accuracy.

RAG Knowledge System

The project uses Retrieval-Augmented Generation to provide relevant information after CT classification.
The pipeline is:
User Question
      +
Swin Prediction
      |
      v
Sentence Transformer
      |
      v
Query Embedding
      |
      v
FAISS Vector Search
      |
      v
Relevant Kidney Knowledge
      |
      v
Gemini LLM
      |
      v
Grounded Response

The knowledge base contains information related to:

Kidney stones
Kidney cysts
Kidney tumors
Normal kidney findings
Symptoms
Diagnosis
Precautions
Diet
Hydration
Treatment overview
Warning signs
When medical evaluation may be required

Technologies Used

Machine Learning
Python
PyTorch
torchvision
timm
Swin Transformer
Pillow
NumPy

RAG and LLM
LangChain
LangChain Google GenAI
LangChain Hugging Face
Sentence Transformers
FAISS
Gemini API

Web Application
Flask
HTML
CSS
JavaScript

KidneyVision_App/
│
├── app.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
├── models/
│   └── kidney_swin_final.pth
│
├── knowledge_base/
│   └── data/
│       ├── knowledge_base.jsonl
│       ├── manifest.json
│       ├── schema.json
│       ├── sources.json
│       └── by_condition/
│
├── src/
│   ├── __init__.py
│   ├── model_loader.py
│   ├── predictor.py
│   ├── rag.py
│   ├── chatbot.py
│   └── pipeline.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── uploads/
│
└── vector_store/

Installation
1. Clone the Repository
git clone YOUR_GITHUB_REPOSITORY_URL
Move into the project:
cd KidneyVision_App

2. Create Virtual Environment
Windows:
py -3.11 -m venv .venv
Activate:
.\.venv\Scripts\Activate.ps1

Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt



Environment Configuration
Create a .env file in the root project directory.

GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_GEMINI_MODEL

Example:

GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

Do not upload the .env file to GitHub.

The .gitignore file should contain:

.env
.venv/
uploads/
vector_store/
__pycache__/
*.pyc
.vscode/

Run the Application
Activate the virtual environment:
.\.venv\Scripts\Activate.ps1

Start Flask:
python app.py

Open the following address in your browser:
http://127.0.0.1:8765

Future Improvements
Possible future extensions include:

->Patient-level dataset splitting
->Larger external validation datasets
->DICOM image support
->Segmentation of kidney abnormalities
->Explainable AI visualization
->Grad-CAM visualization
->User authentication
->Doctor dashboard
->Persistent conversation history across sessions
->Improved source citation display
->Cloud deployment
->REST API deployment
->Database integration

Academic Project

Project Title:
Kidney CT Classification Using Swin Transformer with LangChain-Powered Clinical Advisory Chatbot

Domain:
Artificial Intelligence, Deep Learning, Computer Vision, Large Language Models and Retrieval-Augmented Generation

University:
Visvesvaraya Technological University (VTU)

Department:
Computer Science and Engineering

License
This project is intended primarily for academic and educational use.
Please verify dataset licenses, model licenses and third-party API terms before commercial or clinical use.
