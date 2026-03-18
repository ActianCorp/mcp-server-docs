"""
MkDocs hook to generate proper Bitbucket Server edit URLs.
"""

def on_page_context(context, page, config, nav):
    """
    Generate proper Bitbucket edit URLs for each page.
    
    Bitbucket Server format:
    https://server/browse/docs/path/file.md?mode=edit&at=refs%2Fheads%2Fbranch
    """
    repo_url = config.get('repo_url', '')
    edit_uri = config.get('edit_uri', '')
    
    if repo_url and page.file.src_uri:
        # Get the file path relative to docs directory
        file_path = page.file.src_uri
        
        # Construct Bitbucket edit URL
        # Format: repo_url/browse/docs/file.md?at=refs%2Fheads%2Fbranch&mode=edit
        edit_url = f"{repo_url}/browse/docs/{file_path}?at=refs%2Fheads%2Fmcpdocs&mode=edit"
        
        # Override the edit_url in context
        context['page'].edit_url = edit_url
    
    return context
