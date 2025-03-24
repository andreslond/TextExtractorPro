"""
Menu Extractor Web Application

This is a Flask web application that provides a user interface for the menu extraction functionality.
"""

import os
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from werkzeug.utils import secure_filename

from menu_extractor import MenuExtractor
from utils.logging_config import setup_logging

# Configure logging
setup_logging(logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_menu_extractor_secret")

# Configure upload settings
UPLOAD_FOLDER = os.path.join("results/", "menu_extractor_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OUTPUT_FOLDER = os.path.join("results/", "menu_extractor_results")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Initialize Menu Extractor
menu_extractor = MenuExtractor()

def allowed_file(filename):
    """Check if a filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process the images."""
    # Check if files were submitted
    if 'files[]' not in request.files:
        flash('No files selected', 'error')
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    
    # Check if any file was selected
    if not files or files[0].filename == '':
        flash('No files selected', 'error')
        return redirect(request.url)
    
    # Create a session ID for this batch
    session_id = str(uuid.uuid4())
    session['current_session'] = session_id
    
    # Create directories for this session
    session_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    
    session_output_dir = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_output_dir, exist_ok=True)
    
    # Process each uploaded file
    valid_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_upload_dir, filename)
            file.save(file_path)
            valid_files.append(file_path)
        else:
            flash(f'File {file.filename} has an unsupported format. Skipping.', 'warning')
    
    if not valid_files:
        flash('No valid files were uploaded', 'error')
        return redirect(url_for('index'))
    
    # Save file paths to session
    session['uploaded_files'] = valid_files
    session['output_dir'] = session_output_dir
    
    # Get language selection (default to Spanish)
    language = request.form.get('language', 'spa')
    
    # Process the images
    try:
        menu_extractor = MenuExtractor(language=language)
        results = menu_extractor.process_images(valid_files)
        
        # Export results
        output_files = menu_extractor.export_results(
            results, 
            session_output_dir, 
            formats=['csv', 'json']
        )
        
        # Get statistics
        stats = menu_extractor.get_statistics(results)
        
        # Save results to session
        session['results'] = {
            'stats': stats,
            'output_files': output_files,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Return success and redirect to results page
        flash('Files processed successfully!', 'success')
        return redirect(url_for('results'))
        
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}", exc_info=True)
        flash(f'Error processing files: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    """Display processing results."""
    # Check if there are results in the session
    if 'results' not in session:
        flash('No results found. Please upload files first.', 'warning')
        return redirect(url_for('index'))
    
    # Get results from session
    results = session['results']
    
    return render_template('results.html', results=results)

@app.route('/download/<format>')
def download_file(format):
    """Download processed data files."""
    if 'output_dir' not in session or 'results' not in session:
        flash('No results available for download', 'error')
        return redirect(url_for('index'))
    
    output_dir = session['output_dir']
    
    if format == 'csv':
        file_path = os.path.join(output_dir, 'menu_items.csv')
        return send_file(file_path, as_attachment=True, download_name='menu_items.csv')
    elif format == 'json':
        file_path = os.path.join(output_dir, 'menu_items.json')
        return send_file(file_path, as_attachment=True, download_name='menu_items.json')
    elif format == 'hierarchical_json':
        file_path = os.path.join(output_dir, 'menu_structure.json')
        return send_file(file_path, as_attachment=True, download_name='menu_structure.json')
    else:
        flash('Invalid format requested', 'error')
        return redirect(url_for('results'))

@app.route('/clear')
def clear_session():
    """Clear session data and return to index."""
    session.clear()
    flash('Session data cleared', 'info')
    return redirect(url_for('index'))

# Add error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(e)}", exc_info=True)
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
