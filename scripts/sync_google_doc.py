#!/usr/bin/env python3
"""
Script to sync content from a Google Doc to data/index.md

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib markdownify

Setup:
    1. Go to https://console.cloud.google.com/
    2. Create a new project or select existing one
    3. Enable Google Docs API
    4. Create OAuth 2.0 credentials (Desktop app)
    5. Download credentials JSON and save as 'credentials.json' in this directory
    6. Share your Google Doc with the service account email (or make it publicly viewable)
    7. Get the document ID from the Google Doc URL:
       https://docs.google.com/document/d/DOCUMENT_ID/edit

Usage:
    python scripts/sync_google_doc.py --doc-id DOCUMENT_ID --output data/index.md

Or set environment variables:
    export GOOGLE_DOC_ID="your-document-id"
    python scripts/sync_google_doc.py
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
except ImportError:
    print("Error: Missing required packages. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

try:
    from markdownify import markdownify as md
except ImportError:
    print("Error: Missing markdownify. Install with:")
    print("  pip install markdownify")
    sys.exit(1)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def get_credentials():
    """Get valid user credentials from storage or prompt for authorization."""
    creds = None
    script_dir = Path(__file__).parent
    token_file = script_dir / 'token.pickle'
    credentials_file = script_dir / 'credentials.json'
    
    # The file token.pickle stores the user's access and refresh tokens.
    if token_file.exists():
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_file.exists():
                print(f"Error: credentials.json not found in {script_dir}")
                print("Please download OAuth 2.0 credentials from Google Cloud Console")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_document_content(doc_id):
    """Fetch content from Google Doc."""
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)
    
    # Get the document
    doc = service.documents().get(documentId=doc_id).execute()
    
    # Extract text content
    content = doc.get('body', {}).get('content', [])
    
    # Convert to HTML first (Google Docs API returns structured content)
    html_content = []
    
    def extract_text(element):
        """Recursively extract text from document elements."""
        text = ''
        if 'paragraph' in element:
            para = element['paragraph']
            for elem in para.get('elements', []):
                if 'textRun' in elem:
                    text += elem['textRun'].get('content', '')
                elif 'inlineObjectElement' in elem:
                    # Handle images/objects if needed
                    pass
        elif 'table' in element:
            # Handle tables if needed
            pass
        elif 'sectionBreak' in element:
            text = '\n\n'
        return text
    
    def extract_html(element, level=0):
        """Convert document structure to HTML."""
        html = ''
        if 'paragraph' in element:
            para = element['paragraph']
            para_elements = para.get('elements', [])
            para_text = ''
            for elem in para_elements:
                if 'textRun' in elem:
                    text_run = elem['textRun']
                    content = text_run.get('content', '')
                    style = text_run.get('textStyle', {})
                    
                    # Apply formatting
                    if style.get('bold'):
                        content = f'<b>{content}</b>'
                    if style.get('italic'):
                        content = f'<em>{content}</em>'
                    
                    para_text += content
            
            # Check paragraph style
            para_style = para.get('paragraphStyle', {})
            named_style = para_style.get('namedStyleType', 'NORMAL_TEXT')
            
            if named_style == 'HEADING_1':
                html = f'<h1>{para_text}</h1>\n'
            elif named_style == 'HEADING_2':
                html = f'<h2>{para_text}</h2>\n'
            elif named_style == 'HEADING_3':
                html = f'<h3>{para_text}</h3>\n'
            else:
                html = f'<p>{para_text}</p>\n'
        
        return html
    
    # Process all content elements
    for element in content:
        html = extract_html(element)
        if html:
            html_content.append(html)
    
    html_string = ''.join(html_content)
    
    # Convert HTML to Markdown
    markdown_content = md(html_string, heading_style="ATX")
    
    return markdown_content

def update_data_page(doc_id, output_file):
    """Update data/index.md with content from Google Doc."""
    print(f"Fetching content from Google Doc: {doc_id}")
    
    # Get content from Google Doc
    markdown_content = get_document_content(doc_id)
    
    # Read existing file to preserve front matter
    output_path = Path(output_file)
    front_matter = []
    if output_path.exists():
        with open(output_path, 'r') as f:
            lines = f.readlines()
            in_front_matter = False
            front_matter_done = False
            
            for i, line in enumerate(lines):
                if line.strip() == '---':
                    if not in_front_matter:
                        in_front_matter = True
                        front_matter.append(line)
                    else:
                        front_matter.append(line)
                        front_matter_done = True
                        break
                elif in_front_matter:
                    front_matter.append(line)
    else:
        # Default front matter if file doesn't exist
        front_matter = [
            '---\n',
            'title: Data\n',
            'layout: page\n',
            'order: date\n',
            'banner: OIBcrop.jpg\n',
            'banner_position: left\n',
            '---\n',
            '\n'
        ]
    
    # Write updated file
    with open(output_path, 'w') as f:
        f.writelines(front_matter)
        f.write('\n')
        f.write(markdown_content)
    
    print(f"Successfully updated {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Sync content from Google Doc to data/index.md'
    )
    parser.add_argument(
        '--doc-id',
        default=os.getenv('GOOGLE_DOC_ID'),
        help='Google Doc document ID (or set GOOGLE_DOC_ID env var)'
    )
    parser.add_argument(
        '--output',
        default='data/index.md',
        help='Output markdown file path (default: data/index.md)'
    )
    
    args = parser.parse_args()
    
    if not args.doc_id:
        print("Error: Document ID required. Use --doc-id or set GOOGLE_DOC_ID env var")
        sys.exit(1)
    
    update_data_page(args.doc_id, args.output)

if __name__ == '__main__':
    main()
