/**
 * Main JavaScript file for Menu Extractor
 * Handles file upload UI interactions and preview
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const fileList = document.getElementById('file-list');
    const fileCount = document.getElementById('file-count');
    const submitBtn = document.getElementById('submit-btn');
    
    // Helper function to format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Update file preview
    function updateFilePreview(files) {
        // Clear the file list
        fileList.innerHTML = '';
        
        if (files.length > 0) {
            filePreview.classList.remove('d-none');
            fileCount.textContent = files.length;
            submitBtn.disabled = false;
            
            // Add each file to the preview
            Array.from(files).forEach((file, index) => {
                const fileItem = document.createElement('li');
                fileItem.className = 'list-group-item file-preview-item';
                
                const fileName = document.createElement('div');
                fileName.innerHTML = `<i class="fas fa-file-image text-info me-2"></i>${file.name}`;
                
                const fileDetails = document.createElement('div');
                fileDetails.className = 'text-muted small';
                fileDetails.textContent = formatFileSize(file.size);
                
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn btn-sm btn-outline-danger';
                removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                removeBtn.title = 'Remove file';
                removeBtn.onclick = function() {
                    // Create a new FileList without this file
                    const dt = new DataTransfer();
                    const newFiles = Array.from(fileInput.files).filter((f, i) => i !== index);
                    newFiles.forEach(f => dt.items.add(f));
                    fileInput.files = dt.files;
                    
                    // Update the preview
                    updateFilePreview(fileInput.files);
                };
                
                fileItem.appendChild(fileName);
                fileItem.appendChild(fileDetails);
                fileItem.appendChild(removeBtn);
                fileList.appendChild(fileItem);
            });
        } else {
            filePreview.classList.add('d-none');
            submitBtn.disabled = true;
        }
    }
    
    // Handle file input change
    fileInput.addEventListener('change', function() {
        updateFilePreview(this.files);
    });
    
    // Handle drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', function() {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        // Get the dropped files
        fileInput.files = e.dataTransfer.files;
        updateFilePreview(fileInput.files);
    });
    
    // Handle click on upload area
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle form submission
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', function(e) {
        if (fileInput.files.length === 0) {
            e.preventDefault();
            alert('Please select at least one file to process.');
        } else {
            // Show loading indicator
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
            submitBtn.disabled = true;
        }
    });
});
