
#############################################################################################################################################################################################################################################
The Hidden Text Highlighter tool detects hidden content within uploaded documents, PDFs, or images by analyzing the text color and background contrast. It identifies text that is invisible to the human eye, such as text that matches the background color or uses hidden fonts. The tool highlights these hidden words in red and displays them alongside visible content for comparison. This is useful for uncovering any potentially concealed information within files. The tool is simple to use, with a user-friendly interface that allows users to upload files and see discrepancies between visible and hidden text.
#############################################################################################################################################################################################################################################

**Note: This tool is still under development and only for experimental purposes only**

**Sample steps for installation:**

1. Activate the Virtual Environment
Make sure your virtual environment is activated. If you haven't already created one, you can create it using:

bash
python3 -m venv venv  # Creates a virtual environment
Activate the virtual environment:

On MacOS/Linux:

bash
source venv/bin/activate

On Windows:
venv\Scripts\activate

2. Install the Dependencies
After activating the virtual environment, install the required dependencies using the requirements.txt file:

pip install -r requirements.txt
This will install Flask, Pillow, OpenCV, and any other libraries the project depends on.

3. Run the Application
Now you can run the Flask application:

python app.py
This will start the Flask development server. You should see output similar to this:

csharp
Copy code
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

4. Open in Your Browser
Open a web browser and navigate to:

http://127.0.0.1:5000/
You should see the application running, where you can upload files for analysis.

