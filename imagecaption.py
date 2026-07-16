"""
Generates a descriptive caption for a local image using the BLIP model.
Uses the Hugging Face Transformers library to load the BLIP model and processor.

"""
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

# Initialize the processor and model once when the module is imported.
# This prevents reloading the model every time the function is called.

processor = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-large')
model = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-large')

def generate_caption(image_path):
  
    try:
        image = Image.open(image_path).convert('RGB')
        
        inputs = processor(images=image, return_tensors="pt")
        
        output = model.generate(**inputs)
        
        caption = processor.decode(output[0], skip_special_tokens=True)
        return caption
        
    except FileNotFoundError:
        return f"Error: Could not find an image at '{image_path}'"
    except Exception as e:
        return f"An error occurred: {e}"