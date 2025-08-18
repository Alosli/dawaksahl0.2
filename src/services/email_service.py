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
            subject = "تفعيل حساب دواك سهل"
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
                        <h1>مرحباً بك في دواك سهل</h1>
                        <p>منصة الأدوية الرقمية في اليمن</p>
                    </div>
                    <div class="content">
                        <h2>تفعيل حسابك</h2>
                        <p>شكراً لك على التسجيل في دواك سهل. لإكمال عملية التسجيل، يرجى النقر على الرابط أدناه لتفعيل حسابك:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">تفعيل الحساب</a>
                        </div>
                        <p>إذا لم تتمكن من النقر على الرابط، يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
                        <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                        <p><strong>ملاحظة:</strong> هذا الرابط صالح لمدة 24 ساعة فقط.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 دواك سهل. جميع الحقوق محفوظة.</p>
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
            subject = "تفعيل حساب صيدليتك في منصة - دواك سهل"
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
                        <h1>مرحباً بصيدليتك في دواك سهل</h1>
                        <p>منصة الأدوية الرقمية في اليمن</p>
                    </div>
                    <div class="content">
                        <h2>تفعيل حساب الصيدلية</h2>
                        <p>شكراً لك على تسجيل صيدليتك في دواك سهل. لإكمال عملية التسجيل، يرجى النقر على الرابط أدناه لتفعيل حسابك:</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">تفعيل حساب الصيدلية</a>
                        </div>
                        <p>بعد تفعيل البريد الإلكتروني، سيتم مراجعة طلبك من قبل فريقنا وستتلقى إشعاراً بالموافقة خلال 24-48 ساعة.</p>
                        <p>إذا لم تتمكن من النقر على الرابط، يمكنك نسخ ولصق الرابط التالي في متصفحك:</p>
                        <p style="word-break: break-all; color: #10B981;">{verification_url}</p>
                        <p><strong>ملاحظة:</strong> هذا الرابط صالح لمدة 24 ساعة فقط.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 دواك سهل. جميع الحقوق محفوظة.</p>
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
    def send_doctor_verification_email(email, token, language='ar'):
        """Send verification email to doctor"""
        verification_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000' )}/verify-email?token={token}&type=doctor"
        
        if language == 'ar':
            subject = 'تفعيل حساب الطبيب - دواك سهل'
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; direction: rtl; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                    .content {{ padding: 40px 30px; }}
                    .welcome {{ font-size: 24px; color: #333; margin-bottom: 20px; text-align: center; }}
                    .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .info-box {{ background-color: #f8f9ff; border-right: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="font-size: 48px; margin-bottom: 20px;">🩺</div>
                        <div class="logo">دواك سهل</div>
                        <p>منصة الرعاية الصحية الرقمية</p>
                    </div>
                    
                    <div class="content">
                        <h1 class="welcome">مرحباً بك في دواك سهل!</h1>
                        
                        <div class="message">
                            <p>شكراً لك على التسجيل كطبيب في منصة دواك سهل. نحن سعداء لانضمامك إلى شبكتنا من المهنيين الطبيين المتميزين.</p>
                            <p>لإكمال عملية التسجيل وتفعيل حسابك، يرجى النقر على الزر أدناه لتأكيد عنوان بريدك الإلكتروني:</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">تفعيل الحساب</a>
                        </div>
                        
                        <div class="info-box">
                            <h3>📋 الخطوات التالية:</h3>
                            <ol>
                                <li><strong>تفعيل البريد الإلكتروني:</strong> انقر على زر التفعيل أعلاه</li>
                                <li><strong>مراجعة المستندات:</strong> سيقوم فريقنا بمراجعة مستنداتك الطبية</li>
                                <li><strong>الموافقة على الحساب:</strong> ستتلقى إشعاراً عند الموافقة على حسابك</li>
                                <li><strong>بدء الممارسة:</strong> ابدأ في استقبال المرضى وإدارة عيادتك</li>
                            </ol>
                        </div>
                        
                        <div class="message">
                            <p><strong>⏰ مهم:</strong> هذا الرابط صالح لمدة 24 ساعة فقط.</p>
                            <p>إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد الإلكتروني.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>دواك سهل</strong> - منصة الرعاية الصحية الرقمية</p>
                        <p>للمساعدة: support@dawaksahl.com</p>
                        <p>© 2025 دواك سهل. جميع الحقوق محفوظة.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = 'Doctor Account Verification - DawakSahl'
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                    .content {{ padding: 40px 30px; }}
                    .welcome {{ font-size: 24px; color: #333; margin-bottom: 20px; text-align: center; }}
                    .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .info-box {{ background-color: #f8f9ff; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="font-size: 48px; margin-bottom: 20px;">🩺</div>
                        <div class="logo">DawakSahl</div>
                        <p>Digital Healthcare Platform</p>
                    </div>
                    
                    <div class="content">
                        <h1 class="welcome">Welcome to DawakSahl!</h1>
                        
                        <div class="message">
                            <p>Thank you for registering as a doctor on the DawakSahl platform. We're excited to have you join our network of distinguished medical professionals.</p>
                            <p>To complete your registration and activate your account, please click the button below to verify your email address:</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Account</a>
                        </div>
                        
                        <div class="info-box">
                            <h3>📋 Next Steps:</h3>
                            <ol>
                                <li><strong>Email Verification:</strong> Click the verification button above</li>
                                <li><strong>Document Review:</strong> Our team will review your medical credentials</li>
                                <li><strong>Account Approval:</strong> You'll receive notification when your account is approved</li>
                                <li><strong>Start Practicing:</strong> Begin receiving patients and managing your clinic</li>
                            </ol>
                        </div>
                        
                        <div class="message">
                            <p><strong>⏰ Important:</strong> This link is valid for 24 hours only.</p>
                            <p>If you didn't create this account, please ignore this email.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>DawakSahl</strong> - Digital Healthcare Platform</p>
                        <p>Support: support@dawaksahl.com</p>
                        <p>© 2025 DawakSahl. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return EmailService._send_email(email, subject, html_content)


    @staticmethod
    def send_doctor_approval_email(email, doctor_name, language='ar'):
        """Send approval notification to doctor"""
        login_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000' )}/login"
        
        if language == 'ar':
            subject = 'تم الموافقة على حساب الطبيب - دواك سهل'
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; direction: rtl; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                    .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }}
                    .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                    .content {{ padding: 40px 30px; }}
                    .welcome {{ font-size: 24px; color: #333; margin-bottom: 20px; text-align: center; }}
                    .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="font-size: 48px; margin-bottom: 20px;">✅</div>
                        <div class="logo">دواك سهل</div>
                        <p>تم الموافقة على حسابك!</p>
                    </div>
                    
                    <div class="content">
                        <h1 class="welcome">مبروك د. {doctor_name}!</h1>
                        
                        <div class="message">
                            <p>نحن سعداء لإعلامك بأنه تم الموافقة على حساب الطبيب الخاص بك في منصة دواك سهل.</p>
                            <p>يمكنك الآن تسجيل الدخول وبدء استقبال المرضى وإدارة عيادتك الرقمية.</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{login_url}" class="button">تسجيل الدخول</a>
                        </div>
                        
                        <div class="message">
                            <p>مرحباً بك في عائلة دواك سهل! نتطلع إلى تقديم أفضل الخدمات الطبية معاً.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>دواك سهل</strong> - منصة الرعاية الصحية الرقمية</p>
                        <p>© 2025 دواك سهل. جميع الحقوق محفوظة.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = 'Doctor Account Approved - DawakSahl'
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                    .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }}
                    .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                    .content {{ padding: 40px 30px; }}
                    .welcome {{ font-size: 24px; color: #333; margin-bottom: 20px; text-align: center; }}
                    .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="font-size: 48px; margin-bottom: 20px;">✅</div>
                        <div class="logo">DawakSahl</div>
                        <p>Your account has been approved!</p>
                    </div>
                    
                    <div class="content">
                        <h1 class="welcome">Congratulations Dr. {doctor_name}!</h1>
                        
                        <div class="message">
                            <p>We're pleased to inform you that your doctor account on DawakSahl platform has been approved.</p>
                            <p>You can now log in and start receiving patients and managing your digital clinic.</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{login_url}" class="button">Login Now</a>
                        </div>
                        
                        <div class="message">
                            <p>Welcome to the DawakSahl family! We look forward to providing the best medical services together.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>DawakSahl</strong> - Digital Healthcare Platform</p>
                        <p>© 2025 DawakSahl. All rights reserved.</p>
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
            subject = "إعادة تعيين كلمة المرور - دواك سهل"
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
                        <p>دواك سهل</p>
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
                        <p>© 2025 دواك سهل. جميع الحقوق محفوظة.</p>
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

