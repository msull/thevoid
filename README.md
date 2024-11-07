# The Void 🌌

A Streamlit-based application that provides two unique experiences:

1. **The Void** - A space to cast your thoughts and receive empathetic, abstract responses
2. **Magic Mirror** - An interactive mirror experience that uses AI and computer vision

## Main Features

### The Void
- Text input area for users to share their thoughts and feelings
- Generates empathetic responses using AI
- Creates abstract interpretations in various forms:
  - Poetry
  - Haiku
  - SVG graphics
  - ASCII art
  - Emoji sequences
  - Mindfulness exercises
  - And more

### Magic Mirror
- Camera-based interactive experience
- Responds to the classic "Mirror, mirror on the wall..." prompt
- Uses AI vision to analyze user appearance
- Provides witty, personalized responses
- Text-to-speech functionality for spoken responses

## Installation

1. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run streamlit_app.py
   ```

## Requirements
- Python 3.x
- Streamlit
- OpenAI API access
- Additional dependencies listed in requirements.txt

## Environment Variables
- Requires OpenAI API configuration
- DynamoDB table configuration (for Magic Mirror feature)

## Usage
- Access the main void experience at the root URL
- Navigate to /mirror for the Magic Mirror experience
- Use the camera interface in the Mirror page to interact
