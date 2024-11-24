from flask import Flask, request, render_template
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import cv2
import numpy as np
import html

app = Flask(__name__)

# Function to extract text and color information from PDF
def extract_text_with_colors(pdf_path):
    pdf_document = fitz.open(pdf_path)
    text_color_info = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    color = span["color"]
                    bbox = span["bbox"]
                    # Convert color to RGB tuple if necessary
                    if isinstance(color, int):
                        color = (
                            (color >> 16) & 0xFF,
                            (color >> 8) & 0xFF,
                            color & 0xFF,
                        )
                    text_color_info.append((text, color, bbox))
    
    return text_color_info

# Function to check if colors are similar within a tolerance level
def colors_are_similar(color1, color2, tolerance=30):
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

# Function to identify hidden content with color tolerance
def identify_hidden_content_with_tolerance(text_color_info, page_image, tolerance=30):
    hidden_text = []
    hidden_bboxes = []
    
    for text, color, bbox in text_color_info:
        x0, y0, x1, y1 = map(int, bbox)
        # Extract the region of the text from the image
        region = page_image[y0:y1, x0:x1]
        
        # Get the dominant color in the region (assuming background color)
        dominant_color = cv2.mean(region)[:3]
        dominant_color = tuple(map(int, dominant_color))
        
        # Check if text color matches the dominant background color within tolerance
        if colors_are_similar(color, dominant_color, tolerance):
            hidden_text.append(text)
            hidden_bboxes.append(bbox)
    
    return hidden_text, hidden_bboxes

# Convert PDF to images
def pdf_to_images(pdf_path):
    pdf_document = fitz.open(pdf_path)
    images = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images

# Main function to extract and identify hidden text with tolerance
def main_with_tolerance(pdf_path, tolerance=30):
    text_color_info = extract_text_with_colors(pdf_path)
    images = pdf_to_images(pdf_path)
    
    hidden_text_all_pages = []
    hidden_bboxes_all_pages = []
    for page_num, page_image in enumerate(images):
        page_image_np = np.array(page_image)
        hidden_text, hidden_bboxes = identify_hidden_content_with_tolerance(text_color_info, page_image_np, tolerance)
        hidden_text_all_pages.extend(hidden_text)
        hidden_bboxes_all_pages.append(hidden_bboxes)
    
    return images, hidden_text_all_pages, hidden_bboxes_all_pages, text_color_info

# Function to highlight hidden text in red color
def highlight_hidden_text(images, hidden_bboxes_all_pages):
    highlighted_images = []
    
    for image, bboxes in zip(images, hidden_bboxes_all_pages):
        draw = ImageDraw.Draw(image)
        for bbox in bboxes:
            x0, y0, x1, y1 = map(int, map(round, bbox))  # Ensure bbox values are integers
            draw.rectangle([x0, y0, x1, y1], outline="red", width=2)
        highlighted_images.append(image)
    
    return highlighted_images

# Function to create HTML representation with hidden text highlighted in red
def create_html_with_highlighted_text(text_color_info, hidden_text):
    html_content = ""
    for text, color, bbox in text_color_info:
        if text in hidden_text:
            html_content += f'<span style="color:red; font-family:Arial; font-size:10pt;">{html.escape(text)}</span>'
        else:
            html_content += f'<span style="font-family:Arial; font-size:10pt;">{html.escape(text)}</span>'
    return html_content

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        file_path = "uploaded.pdf"
        file.save(file_path)
        
        images, hidden_text, hidden_bboxes, text_color_info = main_with_tolerance(file_path)
        highlighted_images = highlight_hidden_text(images, hidden_bboxes)
        
        for i, img in enumerate(highlighted_images):
            img.save(f'static/highlighted_page_{i}.png')

        highlighted_html = create_html_with_highlighted_text(text_color_info, hidden_text)

        return render_template('result.html', pages=len(highlighted_images), highlighted_html=highlighted_html)

if __name__ == '__main__':
    app.run(debug=True)
