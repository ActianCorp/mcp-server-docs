"""
MkDocs hook to generate proper GitHub edit URLs.
"""

def on_page_context(context, page, config, nav):
    """
    Generate proper GitHub edit URLs for each page.
    
    GitHub format:
    https://github.com/ORG/REPO/edit/BRANCH/docs/path/file.md
    """
    repo_url = config.get('repo_url', '')
    branch = config.get('repo_branch', 'main')
    
    if repo_url and page.file.src_uri:
        # Get the file path relative to docs directory
        file_path = page.file.src_uri
        
        # Construct GitHub edit URL
        # Format: repo_url/edit/branch/docs/file.md
        edit_url = f"{repo_url}/edit/{branch}/docs/{file_path}"
        
        # Override the edit_url in context
        context['page'].edit_url = edit_url
    
    return context
