from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, DataError
from marshmallow import ValidationError

def register_error_handlers(app):
    """Register error handlers for the Flask application."""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors."""
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'message_ar': 'خطأ في التحقق من صحة البيانات',
            'errors': error.messages
        }), 400
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        """Handle database integrity errors."""
        current_app.logger.error(f"Database integrity error: {error}")
        
        # Check for common integrity violations
        error_message = str(error.orig)
        
        if 'UNIQUE constraint failed' in error_message or 'duplicate key' in error_message:
            if 'email' in error_message:
                return jsonify({
                    'success': False,
                    'message': 'Email address already exists',
                    'message_ar': 'عنوان البريد الإلكتروني موجود بالفعل'
                }), 409
            elif 'phone' in error_message:
                return jsonify({
                    'success': False,
                    'message': 'Phone number already exists',
                    'message_ar': 'رقم الهاتف موجود بالفعل'
                }), 409
            else:
                return jsonify({
                    'success': False,
                    'message': 'Duplicate entry detected',
                    'message_ar': 'تم اكتشاف إدخال مكرر'
                }), 409
        
        return jsonify({
            'success': False,
            'message': 'Database error occurred',
            'message_ar': 'حدث خطأ في قاعدة البيانات'
        }), 500
    
    @app.errorhandler(DataError)
    def handle_data_error(error):
        """Handle database data errors."""
        current_app.logger.error(f"Database data error: {error}")
        return jsonify({
            'success': False,
            'message': 'Invalid data format',
            'message_ar': 'تنسيق البيانات غير صحيح'
        }), 400
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'message_ar': 'طلب غير صحيح'
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            'success': False,
            'message': 'Unauthorized access',
            'message_ar': 'وصول غير مصرح به'
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            'success': False,
            'message': 'Access forbidden',
            'message_ar': 'الوصول محظور'
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'message_ar': 'المورد غير موجود'
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'message_ar': 'الطريقة غير مسموحة'
        }), 405
    
    @app.errorhandler(409)
    def handle_conflict(error):
        """Handle 409 Conflict errors."""
        return jsonify({
            'success': False,
            'message': 'Resource conflict',
            'message_ar': 'تعارض في المورد'
        }), 409
    
    @app.errorhandler(413)
    def handle_payload_too_large(error):
        """Handle 413 Payload Too Large errors."""
        return jsonify({
            'success': False,
            'message': 'File too large',
            'message_ar': 'الملف كبير جداً'
        }), 413
    
    @app.errorhandler(415)
    def handle_unsupported_media_type(error):
        """Handle 415 Unsupported Media Type errors."""
        return jsonify({
            'success': False,
            'message': 'Unsupported file type',
            'message_ar': 'نوع الملف غير مدعوم'
        }), 415
    
    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors."""
        return jsonify({
            'success': False,
            'message': 'Unprocessable entity',
            'message_ar': 'كيان غير قابل للمعالجة'
        }), 422
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors."""
        return jsonify({
            'success': False,
            'message': 'Rate limit exceeded. Please try again later.',
            'message_ar': 'تم تجاوز حد المعدل. يرجى المحاولة مرة أخرى لاحقاً.'
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle 500 Internal Server Error."""
        current_app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'message_ar': 'خطأ داخلي في الخادم'
        }), 500
    
    @app.errorhandler(502)
    def handle_bad_gateway(error):
        """Handle 502 Bad Gateway errors."""
        return jsonify({
            'success': False,
            'message': 'Bad gateway',
            'message_ar': 'بوابة سيئة'
        }), 502
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        return jsonify({
            'success': False,
            'message': 'Service temporarily unavailable',
            'message_ar': 'الخدمة غير متاحة مؤقتاً'
        }), 503
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle generic HTTP exceptions."""
        return jsonify({
            'success': False,
            'message': error.description or 'HTTP error occurred',
            'message_ar': 'حدث خطأ HTTP'
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle generic exceptions."""
        current_app.logger.error(f"Unhandled exception: {error}")
        
        # Don't expose internal errors in production
        if current_app.config.get('DEBUG'):
            return jsonify({
                'success': False,
                'message': str(error),
                'message_ar': 'حدث خطأ غير متوقع'
            }), 500
        else:
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred',
                'message_ar': 'حدث خطأ غير متوقع'
            }), 500

