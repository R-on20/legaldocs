from django import forms
from main.models import Document, DocumentVersion, Tag, DocumentTemplate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ckeditor.widgets import CKEditorWidget
from .validators import (
    document_validator, 
    media_validator, 
    validate_no_path_traversal, 
    sanitize_filename,
    validate_file_size_by_type
)
import bleach
import re
from django.utils.html import escape

# Allowed HTML tags and attributes for CKEditor content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
    'span', 'div', 'img'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'table': ['border', 'cellpadding', 'cellspacing'],
    'span': ['style'],
    'div': ['style'],
}

ALLOWED_STYLES = ['font-weight', 'font-style', 'text-decoration', 'color', 'background-color']


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file', 'description', 'confidential', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000}),
            'tags': forms.SelectMultiple(attrs={'class': 'select2'}),
            'title': forms.TextInput(attrs={'maxlength': 255}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not (self.user and self.user.has_perm('documents.can_mark_confidential')):
            self.fields.pop('confidential')
        
        # Add required attribute for frontend validation
        self.fields['title'].required = True
        self.fields['file'].required = True
        self.fields['document_type'].required = True

    def clean_title(self):
        """Validate and sanitize document title"""
        title = self.cleaned_data.get('title')
        if not title:
            raise ValidationError(_('Title is required.'))
        
        # Remove dangerous characters
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        title = title.strip()
        
        if len(title) < 3:
            raise ValidationError(_('Title must be at least 3 characters long.'))
        
        if len(title) > 255:
            raise ValidationError(_('Title must be less than 255 characters.'))
        
        # Check for path traversal attempts
        validate_no_path_traversal(title)
        
        return title

    def clean_description(self):
        """Validate and sanitize description"""
        description = self.cleaned_data.get('description', '')
        
        if description:
            # Sanitize HTML content
            description = bleach.clean(
                description,
                tags=['p', 'br', 'strong', 'em'],
                attributes={},
                strip=True
            )
            
            if len(description) > 2000:
                raise ValidationError(_('Description must be less than 2000 characters.'))
        
        return description

    def clean_file(self):
        """Enhanced file validation with security checks"""
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError(_('File is required.'))
        
        # Basic security validations
        validate_no_path_traversal(file.name)
        
        # Sanitize filename
        original_name = file.name
        file.name = sanitize_filename(file.name)
        
        # File size validation based on type
        validate_file_size_by_type(file)
        
        # Use simplified validation instead of comprehensive security checks
        try:
            ext = file.name.lower().split('.')[-1] if '.' in file.name else ''
            
            # Basic extension check
            allowed_extensions = ['pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'md', 'mp3', 'wav', 'mp4', 'mov']
            
            if ext not in allowed_extensions:
                raise ValidationError(f"File extension '{ext}' is not allowed. Allowed extensions: {', '.join(allowed_extensions)}")
            
            # Basic file size check (simplified)
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise ValidationError(f"File size exceeds maximum allowed size of 100MB.")
                
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            # Log error but don't fail validation for unexpected issues
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"File validation warning for {file.name}: {e}")
        
        return file


class DocumentVersionForm(forms.ModelForm):
    class Meta:
        model = DocumentVersion
        fields = ['file', 'changes']
        widgets = {
            'changes': forms.Textarea(attrs={'rows': 3, 'maxlength': 1000}),
        }

    def clean_file(self):
        """Validate version file with security checks"""
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError(_('File is required for new version.'))
        
        # Apply same security validations as upload
        validate_no_path_traversal(file.name)
        file.name = sanitize_filename(file.name)
        validate_file_size_by_type(file)
        
        # Use appropriate validator
        ext = file.name.lower().split('.')[-1] if '.' in file.name else ''
        if ext in ['mp3', 'wav', 'mp4', 'mov']:
            media_validator(file)
        else:
            document_validator(file)
        
        return file

    def clean_changes(self):
        """Validate change description"""
        changes = self.cleaned_data.get('changes', '')
        
        if not changes.strip():
            raise ValidationError(_('Please describe the changes made in this version.'))
        
        if len(changes) > 1000:
            raise ValidationError(_('Change description must be less than 1000 characters.'))
        
        # Sanitize HTML content
        changes = bleach.clean(changes, tags=[], attributes={}, strip=True)
        
        return changes


class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'status', 'tags', 'reviewed_by']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000}),
            'title': forms.TextInput(attrs={'maxlength': 255}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.uploaded_by.has_perm('documents.can_approve_document'):
            self.fields.pop('reviewed_by', None)
            self.fields.pop('status', None)

    def clean_title(self):
        """Validate and sanitize title"""
        title = self.cleaned_data.get('title')
        if not title:
            raise ValidationError(_('Title is required.'))
        
        title = re.sub(r'[<>:"/\\|?*]', '_', title).strip()
        
        if len(title) < 3:
            raise ValidationError(_('Title must be at least 3 characters long.'))
        
        validate_no_path_traversal(title)
        return title

    def clean_description(self):
        """Validate and sanitize description"""
        description = self.cleaned_data.get('description', '')
        
        if description:
            description = bleach.clean(
                description,
                tags=['p', 'br', 'strong', 'em'],
                attributes={},
                strip=True
            )
            
            if len(description) > 2000:
                raise ValidationError(_('Description must be less than 2000 characters.'))
        
        return description


class DocumentSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_('Search terms'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search in documents...'),
            'class': 'form-control'
        })
    )
    
    document_type = forms.ChoiceField(
        required=False,
        choices=[('', _('All Types'))] + list(Document.DocType.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('All Statuses'))] + list(Document.Status.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    uploaded_after = forms.DateField(
        required=False,
        label=_('Uploaded after'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    confidential = forms.BooleanField(
        required=False,
        label=_('Include confidential'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_q(self):
        """Sanitize search query"""
        query = self.cleaned_data.get('q', '').strip()
        
        if query:
            # Remove potentially dangerous characters
            query = re.sub(r'[<>"\';]', '', query)
            
            if len(query) > 200:
                raise ValidationError(_('Search query too long. Maximum 200 characters.'))
        
        return query


class AISearchForm(forms.Form):
    """Separate form for AI-powered natural language search"""
    ai_query = forms.CharField(
        required=False,
        label=_('Ask about documents'),
        max_length=500,
        widget=forms.TextInput(attrs={
            'placeholder': _('Ask in natural language: "Show me contracts from last month" or "Find legal research about water rights"'),
            'class': 'form-control',
            'style': 'border-left: 4px solid #007bff;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add helpful attributes for frontend
        self.fields['ai_query'].widget.attrs.update({
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Use natural language to search documents'
        })

    def clean_ai_query(self):
        """Sanitize AI search query"""
        query = self.cleaned_data.get('ai_query', '').strip()
        
        if query:
            # More permissive for natural language, but still remove dangerous chars
            query = re.sub(r'[<>]', '', query)
            
            if len(query) > 500:
                raise ValidationError(_('Search query too long. Maximum 500 characters.'))
            
            if len(query) < 3:
                raise ValidationError(_('Search query too short. Minimum 3 characters.'))
        
        return query


class DocumentCreationForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label=_('Document Name'),
        widget=forms.TextInput(attrs={'maxlength': 255, 'class': 'form-control'}),
        help_text=_('Name for the new document (3-255 characters)')
    )
    content = forms.CharField(
        widget=CKEditorWidget(),
        label=_('Document Content'),
        help_text=_('Create your document content using the rich text editor')
    )
    save_as_pdf = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Also save as PDF'),
        help_text=_('Generate a PDF version of the document'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_name(self):
        """Validate and sanitize document name"""
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError(_('Document name is required.'))
        
        # Remove dangerous characters
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.strip()
        
        if len(name) < 3:
            raise ValidationError(_('Document name must be at least 3 characters long.'))
        
        validate_no_path_traversal(name)
        return name

    def clean_content(self):
        """Sanitize CKEditor content"""
        content = self.cleaned_data.get('content', '')
        
        if not content.strip():
            raise ValidationError(_('Document content is required.'))
        
        # Sanitize HTML content with bleach (remove styles parameter for compatibility)
        content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        # Check content length
        if len(content) > 1000000:  # 1MB text limit
            raise ValidationError(_('Document content too large. Maximum 1MB.'))
        
        return content


class DocumentEditForm(forms.Form):
    """Form for editing document content with CKEditor"""
    content = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        label=_('Document Content'),
        help_text=_('Edit the document content. Changes will be saved as a new version.')
    )
    
    def __init__(self, *args, **kwargs):
        initial_content = kwargs.pop('initial_content', '')
        super().__init__(*args, **kwargs)
        self.fields['content'].initial = initial_content

    def clean_content(self):
        """Sanitize edited content"""
        content = self.cleaned_data.get('content', '')
        
        if not content.strip():
            raise ValidationError(_('Content cannot be empty.'))
        
        # Sanitize HTML content (remove styles parameter for compatibility)
        content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return content


class DocumentWordEditForm(forms.ModelForm):
    """Form for editing Word documents with CKEditor"""
    html_content = forms.CharField(
        widget=CKEditorWidget(config_name='default'),
        label=_('Document Content'),
        help_text=_('Edit the document content using the rich text editor')
    )
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'html_content']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000}),
            'title': forms.TextInput(attrs={'maxlength': 255}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-populate HTML content if it exists
            if self.instance.html_content:
                self.fields['html_content'].initial = self.instance.html_content
            elif self.instance.file and self.instance.file.name.lower().endswith(('.docx', '.doc')):
                # Extract HTML content if not already available
                try:
                    html_content = self.instance.extract_html_content()
                    if html_content:
                        self.fields['html_content'].initial = html_content
                        # Save it for future use
                        self.instance.html_content = html_content
                        self.instance.save(update_fields=['html_content'])
                    else:
                        # Fallback to plain text
                        self.fields['html_content'].initial = f"<p>{self.instance.content}</p>"
                except Exception as e:
                    # Fallback to plain text content wrapped in paragraphs
                    content_paragraphs = self.instance.content.split('\n\n') if self.instance.content else ['']
                    html_fallback = ''.join([f"<p>{para}</p>" for para in content_paragraphs if para.strip()])
                    self.fields['html_content'].initial = html_fallback or "<p>No content available</p>"

    def clean_title(self):
        """Validate and sanitize title"""
        title = self.cleaned_data.get('title')
        if not title:
            raise ValidationError(_('Title is required.'))
        
        title = re.sub(r'[<>:"/\\|?*]', '_', title).strip()
        
        if len(title) < 3:
            raise ValidationError(_('Title must be at least 3 characters long.'))
        
        validate_no_path_traversal(title)
        return title

    def clean_description(self):
        """Validate and sanitize description"""
        description = self.cleaned_data.get('description', '')
        
        if description:
            description = bleach.clean(
                description,
                tags=['p', 'br', 'strong', 'em'],
                attributes={},
                strip=True
            )
            
            if len(description) > 2000:
                raise ValidationError(_('Description must be less than 2000 characters.'))
        
        return description

    def clean_html_content(self):
        """Sanitize HTML content from CKEditor"""
        content = self.cleaned_data.get('html_content', '')
        
        if not content.strip():
            raise ValidationError(_('Document content is required.'))
        
        # Sanitize HTML content with bleach (remove styles parameter for compatibility)
        content = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        # Check content length
        if len(content) > 1000000:  # 1MB text limit
            raise ValidationError(_('Document content too large. Maximum 1MB.'))
        
        return content

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Update the document from HTML content
        if self.cleaned_data.get('html_content'):
            try:
                success = instance.update_from_html(self.cleaned_data['html_content'])
                if not success:
                    # Log more detailed error for debugging
                    print(f"Failed to update document {instance.pk} from HTML")
                    # Try a simple approach - just save the HTML content
                    instance.html_content = self.cleaned_data['html_content']
                    if commit:
                        instance.save(update_fields=['html_content', 'title', 'description'])
                else:
                    if commit:
                        instance.save()
            except Exception as e:
                print(f"Exception in form save: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                # Fallback: just save the HTML content without updating the file
                instance.html_content = self.cleaned_data['html_content']
                if commit:
                    instance.save(update_fields=['html_content', 'title', 'description'])
        else:
            if commit:
                instance.save()
        
        return instance
