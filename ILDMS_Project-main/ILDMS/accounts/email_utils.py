import logging
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def send_email_async(subject, html_content, recipient_list, from_email=None):
    """
    Send email in a background thread to avoid blocking the main request.
    Fails silently if there are any issues.
    """
    def _send_email():
        try:
            # Create plain text version from HTML
            plain_message = strip_tags(html_content)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_content,
                from_email=from_email or settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True  # Don't raise exceptions
            )
            logger.info(f"Email sent successfully to {recipient_list}")
        except Exception as e:
            logger.warning(f"Failed to send email to {recipient_list}: {str(e)}")
    
    # Start email sending in background thread
    email_thread = threading.Thread(target=_send_email)
    email_thread.daemon = True  # Dies when main thread dies
    email_thread.start()

def send_verification_email_async(user, verification_link):
    """
    Send verification email in background thread
    """
    try:
        # Render email template
        html_content = render_to_string('accounts/emails/verification_email.html', {
            'user': user,
            'verification_link': verification_link,
        })
        
        subject = 'Verify Your ILDMS Account'
        recipient_list = [user.email]
        
        send_email_async(subject, html_content, recipient_list)
        logger.info(f"Verification email queued for {user.email}")
        
    except Exception as e:
        logger.warning(f"Failed to queue verification email for {user.email}: {str(e)}")

def send_password_reset_email_async(user, reset_link):
    """
    Send password reset email in background thread
    """
    try:
        # Render email template
        html_content = render_to_string('registration/password_reset_email.html', {
            'user': user,
            'password_reset_url': reset_link,
        })
        
        subject = 'Reset Your ILDMS Password'
        recipient_list = [user.email]
        
        send_email_async(subject, html_content, recipient_list)
        logger.info(f"Password reset email queued for {user.email}")
        
    except Exception as e:
        logger.warning(f"Failed to queue password reset email for {user.email}: {str(e)}")

def send_welcome_email_async(user):
    """
    Send welcome email after successful registration
    """
    try:
        # Render email template
        html_content = render_to_string('accounts/emails/welcome_email.html', {
            'user': user,
        })
        
        subject = 'Welcome to ILDMS - Intelligent Library Document Management System'
        recipient_list = [user.email]
        
        send_email_async(subject, html_content, recipient_list)
        logger.info(f"Welcome email queued for {user.email}")
        
    except Exception as e:
        logger.warning(f"Failed to queue welcome email for {user.email}: {str(e)}")
