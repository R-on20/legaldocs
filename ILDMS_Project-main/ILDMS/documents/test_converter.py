#!/usr/bin/env python
"""
Test script to check the improved DOCX converter
"""
import os
import sys
import django

# Setup Django
sys.path.append(r'c:\Users\User\ILDMS_Project\ILDMS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ILDMS.settings')
django.setup()

from documents.docx_converter import convert_docx_to_html

def test_converter():
    """Test the converter with a sample HTML"""
    sample_html = """
    <p>This is some text before the table.</p>
    <p>More text here.</p>
    <table>
        <tr>
            <th>Header 1</th>
            <th>Header 2</th>
        </tr>
        <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
        </tr>
    </table>
    <p>Text after the table.</p>
    """
    
    print("Original HTML:")
    print(sample_html)
    print("\n" + "="*50 + "\n")
    
    # Test the HTML cleaning function
    from documents.docx_converter import DocxToHtmlConverter
    converter = DocxToHtmlConverter()
    cleaned_html = converter._clean_html_for_editor(sample_html)
    
    print("Cleaned HTML:")
    print(cleaned_html)

if __name__ == "__main__":
    test_converter()
