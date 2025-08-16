"""
File Upload Utility for DawakSahl Backend
Handles file uploads for profile pictures, documents, and other media
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import magic
from flask import current_app

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# Maximum file sizes (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename, file_type='any'):
    """Check if file extension is allowed"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        return extension in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'document':
        return extension in ALLOWED_DOCUMENT_EXTENSIONS
    else:
        return extension in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Get file type based on extension"""
    if not filename or '.' not in filename:
        return 'unknown'
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif extension in ALLOWED_DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'unknown'

def validate_file_size(file, file_type):
    """Validate file size based on type"""
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_type == 'image' and file_size > MAX_IMAGE_SIZE:
        return False, f"Image file too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB"
    elif file_type == 'document' and file_size > MAX_DOCUMENT_SIZE:
        return False, f"Document file too large. Maximum size is {MAX_DOCUMENT_SIZE // (1024*1024)}MB"
    elif file_size > MAX_DOCUMENT_SIZE:  # Default to document size limit
        return False, f"File too large. Maximum size is {MAX_DOCUMENT_SIZE // (1024*1024)}MB"
    
    return True, "File size is valid"

def validate_image_content(file):
    """Validate that the file is actually an image"""
    try:
        # Reset file pointer
        file.seek(0)
        
        # Try to open with PIL
        with Image.open(file) as img:
            img.verify()  # Verify it's a valid image
        
        # Reset file pointer again
        file.seek(0)
        return True, "Valid image file"
    except Exception as e:
        file.seek(0)  # Reset file pointer
        return False, f"Invalid image file: {str(e)}"

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the extension"""
    if not original_filename or '.' not in original_filename:
        return f"{uuid.uuid4().hex}.bin"
    
    name, extension = original_filename.rsplit('.', 1)
    secure_name = secure_filename(name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    
    return f"{secure_name}_{timestamp}_{unique_id}.{extension.lower()}"

def create_upload_directory(upload_path):
    """Create upload directory if it doesn't exist"""
    try:
        os.makedirs(upload_path, exist_ok=True)
        return True, "Directory created successfully"
    except Exception as e:
        return False, f"Failed to create directory: {str(e)}"

def resize_image(file_path, max_width=1200, max_height=1200, quality=85):
    """Resize image if it's too large"""
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Calculate new dimensions
            width, height = img.size
            if width > max_width or height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(file_path, optimize=True, quality=quality)
        
        return True, "Image resized successfully"
    except Exception as e:
        return False, f"Failed to resize image: {str(e)}"

def upload_file(file, upload_type='general', user_id=None, resize_images=True):
    """
    Main file upload function
    
    Args:
        file: FileStorage object from Flask request
        upload_type: Type of upload ('profile', 'document', 'license', 'general')
        user_id: ID of the user uploading the file
        resize_images: Whether to resize images automatically
    
    Returns:
        tuple: (success: bool, data: dict or error_message: str)
    """
    try:
        # Validate file exists
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check if file extension is allowed
        if not allowed_file(file.filename):
            return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Get file type
        file_type = get_file_type(file.filename)
        
        # Validate file size
        size_valid, size_message = validate_file_size(file, file_type)
        if not size_valid:
            return False, size_message
        
        # Validate image content if it's an image
        if file_type == 'image':
            content_valid, content_message = validate_image_content(file)
            if not content_valid:
                return False, content_message
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        
        # Determine upload directory based on type
        base_upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        if upload_type == 'profile':
            upload_dir = os.path.join(base_upload_dir, 'profiles')
        elif upload_type == 'document':
            upload_dir = os.path.join(base_upload_dir, 'documents')
        elif upload_type == 'license':
            upload_dir = os.path.join(base_upload_dir, 'licenses')
        else:
            upload_dir = os.path.join(base_upload_dir, 'general')
        
        # Add user subdirectory if user_id provided
        if user_id:
            upload_dir = os.path.join(upload_dir, str(user_id))
        
        # Create directory if it doesn't exist
        dir_created, dir_message = create_upload_directory(upload_dir)
        if not dir_created:
            return False, dir_message
        
        # Full file path
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Resize image if needed
        if file_type == 'image' and resize_images:
            resize_success, resize_message = resize_image(file_path)
            if not resize_success:
                # Log warning but don't fail the upload
                current_app.logger.warning(f"Failed to resize image: {resize_message}")
        
        # Get file size after processing
        file_size = os.path.getsize(file_path)
        
        # Generate file URL (relative to upload directory)
        file_url = file_path.replace(base_upload_dir, '').replace('\\', '/').lstrip('/')
        
        # Return success with file information
        return True, {
            'filename': unique_filename,
            'original_filename': file.filename,
            'file_path': file_path,
            'file_url': file_url,
            'file_type': file_type,
            'file_size': file_size,
            'upload_type': upload_type,
            'uploaded_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return False, f"Upload failed: {str(e)}"

def delete_file(file_path):
    """Delete a file from the filesystem"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, "File deleted successfully"
        else:
            return False, "File not found"
    except Exception as e:
        current_app.logger.error(f"File deletion error: {str(e)}")
        return False, f"Failed to delete file: {str(e)}"

def get_file_info(file_path):
    """Get information about a file"""
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_type = get_file_type(filename)
        
        return {
            'filename': filename,
            'file_path': file_path,
            'file_type': file_type,
            'file_size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        current_app.logger.error(f"Error getting file info: {str(e)}")
        return None

# Utility functions for specific upload types
def upload_profile_picture(file, user_id):
    """Upload profile picture with specific settings"""
    return upload_file(file, upload_type='profile', user_id=user_id, resize_images=True)

def upload_document(file, user_id):
    """Upload document file"""
    return upload_file(file, upload_type='document', user_id=user_id, resize_images=False)

def upload_license(file, user_id):
    """Upload license document"""
    return upload_file(file, upload_type='license', user_id=user_id, resize_images=False)

