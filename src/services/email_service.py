import os
from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime

class EmailService:
    """Email service with SendGrid integration and multilingual support."""
    
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=current_app.config.get('SENDGRID_API_KEY'))
        self.from_email = current_app.config.get('SENDGRID_FROM_EMAIL')
        self.from_name = current_app.config.get('SENDGRID_FROM_NAME')
        self.frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using SendGrid."""
        try:
            from_email = Email(self.from_email, self.from_name)
            to_email = To(to_email)
            
            if text_content:
                content = Content("text/plain", text_content)
                mail = Mail(from_email, to_email, subject, content)
                mail.add_content(Content("text/html", html_content))
            else:
                content = Content("text/html", html_content)
                mail = Mail(from_email, to_email, subject, content)
            
            response = self.sg.send(mail)
            current_app.logger.info(f"Email sent successfully to {to_email.email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_verification_email(self, user):
        """Send email verification email in user's preferred language."""
        
        # Determine language based on user preference or default to Arabic
        language = getattr(user, 'preferred_language', 'ar')
        
        verification_url = f"{self.frontend_url}/verify-email?token={user.email_verification_token}"
        
        if language == 'ar':
            subject = "تأكيد البريد الإلكتروني - دواكسهل"
            html_content = self._get_verification_email_template_ar(user, verification_url)
            text_content = f"""
مرحباً {user.get_full_name()},

شكراً لك على التسجيل في دواكسهل. يرجى النقر على الرابط أدناه لتأكيد بريدك الإلكتروني:

{verification_url}

إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد الإلكتروني.

مع أطيب التحيات،
فريق دواكسهل
            """
        else:
            subject = "Email Verification - DawakSahl"
            html_content = self._get_verification_email_template_en(user, verification_url)
            text_content = f"""
Hello {user.get_full_name()},

Thank you for registering with DawakSahl. Please click the link below to verify your email address:

{verification_url}

If you didn't create this account, please ignore this email.

Best regards,
DawakSahl Team
            """
        
        return self.send_email(user.email, subject, html_content, text_content)
    
    def send_password_reset_email(self, user):
        """Send password reset email in user's preferred language."""
        
        # Determine language based on user preference or default to Arabic
        language = getattr(user, 'preferred_language', 'ar')
        
        reset_url = f"{self.frontend_url}/reset-password?token={user.password_reset_token}"
        
        if language == 'ar':
            subject = "إعادة تعيين كلمة المرور - دواكسهل"
            html_content = self._get_password_reset_email_template_ar(user, reset_url)
            text_content = f"""
مرحباً {user.get_full_name()},

تلقينا طلباً لإعادة تعيين كلمة المرور لحسابك. يرجى النقر على الرابط أدناه لإعادة تعيين كلمة المرور:

{reset_url}

إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد الإلكتروني.

مع أطيب التحيات،
فريق دواكسهل
            """
        else:
            subject = "Password Reset - DawakSahl"
            html_content = self._get_password_reset_email_template_en(user, reset_url)
            text_content = f"""
Hello {user.get_full_name()},

We received a request to reset your password. Please click the link below to reset your password:

{reset_url}

If you didn't request a password reset, please ignore this email.

Best regards,
DawakSahl Team
            """
        
        return self.send_email(user.email, subject, html_content, text_content)
    
    def send_order_confirmation_email(self, user, order, language='ar'):
        """Send order confirmation email."""
        
        if language == 'ar':
            subject = f"تأكيد الطلب #{order.order_number} - دواكسهل"
            html_content = self._get_order_confirmation_email_template_ar(user, order)
        else:
            subject = f"Order Confirmation #{order.order_number} - DawakSahl"
            html_content = self._get_order_confirmation_email_template_en(user, order)
        
        return self.send_email(user.email, subject, html_content)
    
    def send_order_status_email(self, user, order, language='ar'):
        """Send order status update email."""
        
        if language == 'ar':
            subject = f"تحديث الطلب #{order.order_number} - دواكسهل"
            html_content = self._get_order_status_email_template_ar(user, order)
        else:
            subject = f"Order Update #{order.order_number} - DawakSahl"
            html_content = self._get_order_status_email_template_en(user, order)
        
        return self.send_email(user.email, subject, html_content)
    
    def _get_verification_email_template_ar(self, user, verification_url):
        """Arabic email verification template."""
        return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد البريد الإلكتروني</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; direction: rtl; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>مرحباً بك في دواكسهل</h1>
            <p>منصة الصيدليات الرقمية الرائدة</p>
        </div>
        <div class="content">
            <h2>مرحباً {user.get_full_name()}</h2>
            <p>شكراً لك على التسجيل في دواكسهل. لإكمال عملية التسجيل، يرجى تأكيد بريدك الإلكتروني بالنقر على الزر أدناه:</p>
            
            <div style="text-align: center;">
                <a href="{verification_url}" class="button">تأكيد البريد الإلكتروني</a>
            </div>
            
            <p>أو يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
            <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
            
            <p><strong>ملاحظة:</strong> هذا الرابط صالح لمدة 24 ساعة فقط.</p>
            
            <p>إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد الإلكتروني.</p>
        </div>
        <div class="footer">
            <p>© 2024 دواكسهل. جميع الحقوق محفوظة.</p>
            <p>هذا بريد إلكتروني تلقائي، يرجى عدم الرد عليه.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_verification_email_template_en(self, user, verification_url):
        """English email verification template."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to DawakSahl</h1>
            <p>Leading Digital Pharmacy Platform</p>
        </div>
        <div class="content">
            <h2>Hello {user.get_full_name()}</h2>
            <p>Thank you for registering with DawakSahl. To complete your registration, please verify your email address by clicking the button below:</p>
            
            <div style="text-align: center;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </div>
            
            <p>Or you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
            
            <p><strong>Note:</strong> This link is valid for 24 hours only.</p>
            
            <p>If you didn't create this account, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>© 2024 DawakSahl. All rights reserved.</p>
            <p>This is an automated email, please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_password_reset_email_template_ar(self, user, reset_url):
        """Arabic password reset email template."""
        return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إعادة تعيين كلمة المرور</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; direction: rtl; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>إعادة تعيين كلمة المرور</h1>
            <p>دواكسهل</p>
        </div>
        <div class="content">
            <h2>مرحباً {user.get_full_name()}</h2>
            <p>تلقينا طلباً لإعادة تعيين كلمة المرور لحسابك. يمكنك إعادة تعيين كلمة المرور بالنقر على الزر أدناه:</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="button">إعادة تعيين كلمة المرور</a>
            </div>
            
            <p>أو يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
            <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
            
            <div class="warning">
                <p><strong>تنبيه أمني:</strong></p>
                <ul>
                    <li>هذا الرابط صالح لمدة ساعة واحدة فقط</li>
                    <li>إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد</li>
                    <li>لا تشارك هذا الرابط مع أي شخص آخر</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 دواكسهل. جميع الحقوق محفوظة.</p>
            <p>هذا بريد إلكتروني تلقائي، يرجى عدم الرد عليه.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_password_reset_email_template_en(self, user, reset_url):
        """English password reset email template."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset</h1>
            <p>DawakSahl</p>
        </div>
        <div class="content">
            <h2>Hello {user.get_full_name()}</h2>
            <p>We received a request to reset your password. You can reset your password by clicking the button below:</p>
            
            <div style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </div>
            
            <p>Or you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
            
            <div class="warning">
                <p><strong>Security Notice:</strong></p>
                <ul>
                    <li>This link is valid for 1 hour only</li>
                    <li>If you didn't request a password reset, please ignore this email</li>
                    <li>Don't share this link with anyone else</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 DawakSahl. All rights reserved.</p>
            <p>This is an automated email, please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_order_confirmation_email_template_ar(self, user, order):
        """Arabic order confirmation email template."""
        return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تأكيد الطلب</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; direction: rtl; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .order-details {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>تم تأكيد طلبك!</h1>
            <p>رقم الطلب: {order.order_number}</p>
        </div>
        <div class="content">
            <h2>مرحباً {user.get_full_name()}</h2>
            <p>شكراً لك على طلبك من دواكسهل. تم تأكيد طلبك وهو قيد المعالجة.</p>
            
            <div class="order-details">
                <h3>تفاصيل الطلب:</h3>
                <p><strong>رقم الطلب:</strong> {order.order_number}</p>
                <p><strong>تاريخ الطلب:</strong> {order.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>المبلغ الإجمالي:</strong> {order.final_amount} ريال</p>
                <p><strong>حالة الطلب:</strong> {order.get_status_display('ar')}</p>
            </div>
            
            <p>سنقوم بإرسال تحديثات حول حالة طلبك عبر البريد الإلكتروني والإشعارات.</p>
        </div>
        <div class="footer">
            <p>© 2024 دواكسهل. جميع الحقوق محفوظة.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_order_confirmation_email_template_en(self, user, order):
        """English order confirmation email template."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Confirmation</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .order-details {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Order Confirmed!</h1>
            <p>Order Number: {order.order_number}</p>
        </div>
        <div class="content">
            <h2>Hello {user.get_full_name()}</h2>
            <p>Thank you for your order from DawakSahl. Your order has been confirmed and is being processed.</p>
            
            <div class="order-details">
                <h3>Order Details:</h3>
                <p><strong>Order Number:</strong> {order.order_number}</p>
                <p><strong>Order Date:</strong> {order.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Total Amount:</strong> {order.final_amount} SAR</p>
                <p><strong>Order Status:</strong> {order.get_status_display('en')}</p>
            </div>
            
            <p>We'll send you updates about your order status via email and notifications.</p>
        </div>
        <div class="footer">
            <p>© 2024 DawakSahl. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_order_status_email_template_ar(self, user, order):
        """Arabic order status update email template."""
        return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحديث الطلب</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; direction: rtl; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .status-update {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>تحديث طلبك</h1>
            <p>رقم الطلب: {order.order_number}</p>
        </div>
        <div class="content">
            <h2>مرحباً {user.get_full_name()}</h2>
            <p>تم تحديث حالة طلبك:</p>
            
            <div class="status-update">
                <h3>الحالة الجديدة: {order.get_status_display('ar')}</h3>
                <p><strong>رقم الطلب:</strong> {order.order_number}</p>
                <p><strong>تاريخ التحديث:</strong> {order.updated_at.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 دواكسهل. جميع الحقوق محفوظة.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_order_status_email_template_en(self, user, order):
        """English order status update email template."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Update</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .status-update {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Order Update</h1>
            <p>Order Number: {order.order_number}</p>
        </div>
        <div class="content">
            <h2>Hello {user.get_full_name()}</h2>
            <p>Your order status has been updated:</p>
            
            <div class="status-update">
                <h3>New Status: {order.get_status_display('en')}</h3>
                <p><strong>Order Number:</strong> {order.order_number}</p>
                <p><strong>Update Time:</strong> {order.updated_at.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 DawakSahl. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

