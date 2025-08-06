import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import current_app, render_template_string
import logging

class EmailService:
    """Email service using SendGrid"""
    
    @staticmethod
    def _get_sendgrid_client():
        """Get SendGrid client"""
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            raise ValueError("SENDGRID_API_KEY environment variable is required")
        return SendGridAPIClient(api_key)
    
    @staticmethod
    def _send_email(to_email, subject, html_content, from_email=None):
        """Send email using SendGrid"""
        try:
            if not from_email:
                from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@dawaksahl.com')
            
            sg = EmailService._get_sendgrid_client()
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = sg.send(message)
            
            if response.status_code >= 200 and response.status_code < 300:
                current_app.logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                current_app.logger.error(f"Failed to send email to {to_email}: {response.status_code}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Email sending error: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_email(email, token, language='ar'):
        """Send email verification email"""
        base_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{base_url}/verify-email?token={token}"
        
        if language == 'ar':
            subject = "تفعيل حساب دواك صحل"
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>تفعيل الحساب</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>مرحباً بك في دواك صحل</h1>
                        <p>منصة الأدوية الرقمية في اليمن</p>
                    </div>
                    <div class="content">
                        <h2>تفعيل حسابك</h2>
                        <p>شكراً لك على التسجيل في دواك صحل. لإكمال عملية التسجيل، يرجى النقر على الرابط أدناه لتفعيل حسابك:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">تفعيل الحساب</a>
                        </div>
                        <p>إذا لم تتمكن من النقر على الرابط، يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
                        <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                        <p><strong>ملاحظة:</strong> هذا الرابط صالح لمدة 24 ساعة فقط.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 دواك صحل. جميع الحقوق محفوظة.</p>
                        <p>إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد الإلكتروني.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = "Verify Your Dawaksahl Account"
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Account Verification</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to Dawaksahl</h1>
                        <p>Yemen's Digital Pharmacy Platform</p>
                    </div>
                    <div class="content">
                        <h2>Verify Your Account</h2>
                        <p>Thank you for registering with Dawaksahl. To complete your registration, please click the link below to verify your account:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Account</a>
                        </div>
                        <p>If you can't click the button, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                        <p><strong>Note:</strong> This link is valid for 24 hours only.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Dawaksahl. All rights reserved.</p>
                        <p>If you didn't create this account, please ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return EmailService._send_email(email, subject, html_content)
    
    @staticmethod
    def send_pharmacy_verification_email(email, token, language='ar'):
        """Send pharmacy verification email"""
        base_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{base_url}/verify-email?token={token}"
        
        if language == 'ar':
            subject = "تفعيل حساب الصيدلية - دواك صحل"
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>تفعيل حساب الصيدلية</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>مرحباً بصيدليتك في دواك صحل</h1>
                        <p>منصة الأدوية الرقمية في اليمن</p>
                    </div>
                    <div class="content">
                        <h2>تفعيل حساب الصيدلية</h2>
                        <p>شكراً لك على تسجيل صيدليتك في دواك صحل. لإكمال عملية التسجيل، يرجى النقر على الرابط أدناه لتفعيل حسابك:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">تفعيل حساب الصيدلية</a>
                        </div>
                        <p>بعد تفعيل البريد الإلكتروني، سيتم مراجعة طلبك من قبل فريقنا وستتلقى إشعاراً بالموافقة خلال 24-48 ساعة.</p>
                        <p>إذا لم تتمكن من النقر على الرابط، يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
                        <p style="word-break: break-all; color: #10B981;">{verification_url}</p>
                        <p><strong>ملاحظة:</strong> هذا الرابط صالح لمدة 24 ساعة فقط.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 دواك صحل. جميع الحقوق محفوظة.</p>
                        <p>إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد الإلكتروني.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = "Verify Your Pharmacy Account - Dawaksahl"
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Pharmacy Account Verification</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome Your Pharmacy to Dawaksahl</h1>
                        <p>Yemen's Digital Pharmacy Platform</p>
                    </div>
                    <div class="content">
                        <h2>Verify Your Pharmacy Account</h2>
                        <p>Thank you for registering your pharmacy with Dawaksahl. To complete your registration, please click the link below to verify your account:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Pharmacy Account</a>
                        </div>
                        <p>After email verification, your application will be reviewed by our team and you'll receive approval notification within 24-48 hours.</p>
                        <p>If you can't click the button, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #10B981;">{verification_url}</p>
                        <p><strong>Note:</strong> This link is valid for 24 hours only.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Dawaksahl. All rights reserved.</p>
                        <p>If you didn't create this account, please ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return EmailService._send_email(email, subject, html_content)
    
    @staticmethod
    def send_password_reset_email(email, token, language='ar'):
        """Send password reset email"""
        base_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{base_url}/reset-password?token={token}"
        
        if language == 'ar':
            subject = "إعادة تعيين كلمة المرور - دواك صحل"
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>إعادة تعيين كلمة المرور</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>إعادة تعيين كلمة المرور</h1>
                        <p>دواك صحل</p>
                    </div>
                    <div class="content">
                        <h2>طلب إعادة تعيين كلمة المرور</h2>
                        <p>تلقينا طلباً لإعادة تعيين كلمة المرور لحسابك. إذا كنت قد طلبت ذلك، يرجى النقر على الرابط أدناه لإعادة تعيين كلمة المرور:</p>
                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">إعادة تعيين كلمة المرور</a>
                        </div>
                        <p>إذا لم تتمكن من النقر على الرابط، يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
                        <p style="word-break: break-all; color: #F59E0B;">{reset_url}</p>
                        <p><strong>ملاحظة:</strong> هذا الرابط صالح لمدة ساعة واحدة فقط.</p>
                        <p>إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد الإلكتروني.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 دواك صحل. جميع الحقوق محفوظة.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = "Reset Your Password - Dawaksahl"
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset</h1>
                        <p>Dawaksahl</p>
                    </div>
                    <div class="content">
                        <h2>Password Reset Request</h2>
                        <p>We received a request to reset the password for your account. If you made this request, please click the link below to reset your password:</p>
                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </div>
                        <p>If you can't click the button, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #F59E0B;">{reset_url}</p>
                        <p><strong>Note:</strong> This link is valid for 1 hour only.</p>
                        <p>If you didn't request a password reset, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 Dawaksahl. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return EmailService._send_email(email, subject, html_content)

