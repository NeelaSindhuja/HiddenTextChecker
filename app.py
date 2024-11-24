from flask import Flask, request, render_template
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import cv2
import numpy as np
import html

app = Flask(__name__)

# Function to extract text and color information from a single page
def extract_text_with_colors(page):
    text_color_info = []
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if "lines" in block:  # Check if 'lines' exists in the block
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

# Parse the pages input to get a list of page numbers
def parse_pages(pages_input, total_pages):
    pages = set()
    if pages_input:
        for part in pages_input.split(','):
            if '-' in part:
                start, end = part.split('-')
                pages.update(range(int(start), int(end) + 1))
            else:
                pages.add(int(part))
    else:
        pages = set(range(1, total_pages + 1))
    return sorted(pages)

# Main function to process and analyze specified pages
def process_and_analyze_pdf(pdf_path, pages_to_process, tolerance=30):
    pdf_document = fitz.open(pdf_path)
    total_pages = pdf_document.page_count
    highlighted_images = []
    hidden_text_all_pages = []
    text_color_info_all_pages = []
    hidden_html_all_pages = []

    for page_num in range(total_pages):
        if page_num + 1 in pages_to_process:
            print(f"Processing page {page_num + 1}")
            page = pdf_document.load_page(page_num)

            # Reduce image resolution to save memory
            pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            text_color_info = extract_text_with_colors(page)
            page_image_np = np.array(img)
            hidden_text, hidden_bboxes = identify_hidden_content_with_tolerance(text_color_info, page_image_np, tolerance)

            # Highlight hidden text in the image
            draw = ImageDraw.Draw(img)
            for bbox in hidden_bboxes:
                x0, y0, x1, y1 = map(int, map(round, bbox))
                draw.rectangle([x0, y0, x1, y1], outline="red", width=2)
            
            # Save the highlighted image and prepare HTML content
            img_path = f'static/highlighted_page_{page_num}.png'
            img.save(img_path)
            highlighted_images.append(img_path)
            hidden_text_all_pages.append(hidden_text)
            text_color_info_all_pages.append(text_color_info)

            # Prepare HTML content for hidden text
            hidden_html = ""
            for text in hidden_text:
                hidden_html += f'<span style="color:red;">{html.escape(text)}</span> '
            hidden_html_all_pages.append(hidden_html)

            # Clear memory before processing the next page
            del page
            del pix
            del img
            del page_image_np
    
    return highlighted_images, hidden_text_all_pages, hidden_html_all_pages

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        print("No file part")
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        return 'No selected file'
    pages_input = request.form.get('pages')
    if file:
        file_path = "uploaded.pdf"
        file.save(file_path)
        print(f"File uploaded and saved as {file_path}")

        # Parse pages input to determine which pages to process
        pdf_document = fitz.open(file_path)
        total_pages = pdf_document.page_count
        pages_to_process = parse_pages(pages_input, total_pages)

        highlighted_images, hidden_text_all_pages, hidden_html_all_pages = process_and_analyze_pdf(file_path, pages_to_process)
        
        # Debugging: Print the number of pages to ensure it's defined correctly
        num_pages = len(highlighted_images)
        print(f"Number of pages processed: {num_pages}")

        if num_pages == 0:
            return "No pages were processed. Please check your input."

        # Pass 'pages' and other required variables to the template
        return render_template('result.html', pages=num_pages, hidden_text_all_pages=hidden_text_all_pages, hidden_html_all_pages=hidden_html_all_pages)

if __name__ == '__main__':
    app.run(debug=True)
