#!/usr/bin/env python3
import os
import requests
import base64
import json
from pathlib import Path

def get_github_token():
    """Get GitHub token from environment or Replit connection"""
    token = os.getenv('GITHUB_TOKEN')
    if token:
        return token
    
    hostname = os.getenv('REPLIT_CONNECTORS_HOSTNAME')
    repl_identity = os.getenv('REPL_IDENTITY')
    web_repl_renewal = os.getenv('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        return None
    
    if not hostname:
        return None
    
    try:
        response = requests.get(
            f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=github',
            headers={
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': x_replit_token
            }
        )
        data = response.json()
        if data.get('items'):
            connection = data['items'][0]
            token = connection.get('settings', {}).get('access_token')
            if token:
                return token
            token = connection.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
            if token:
                return token
    except Exception as e:
        print(f"Error getting token: {e}")
    
    return None

def get_repo_info(token, owner, repo):
    """Get repository information"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    url = f'https://api.github.com/repos/{owner}/{repo}'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting repo info: {response.status_code}")
        return None

def upload_file(token, owner, repo, file_path, content, branch='main'):
    """Upload a single file to GitHub"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    # Encode content
    try:
        content_str = content.decode('utf-8') if isinstance(content, bytes) else content
        is_binary = False
    except UnicodeDecodeError:
        content_str = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode('utf-8')
        is_binary = True
    
    data = {
        'message': f'Add {file_path}',
        'content': content_str,
        'branch': branch
    }
    
    if is_binary:
        data['encoding'] = 'base64'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}'
    response = requests.put(url, headers=headers, json=data)
    
    return response.status_code in [201, 200], response.status_code, response.text

if __name__ == '__main__':
    print("🚀 Starting GitHub file upload...")
    
    token = get_github_token()
    if not token:
        print("❌ Could not get GitHub token")
        print(f"GITHUB_TOKEN env: {os.getenv('GITHUB_TOKEN')}")
        exit(1)
    
    print("✅ Token obtained")
    
    owner = "deividdarosa"
    repo = "discord-bot"
    
    # Check repo exists
    repo_info = get_repo_info(token, owner, repo)
    if not repo_info:
        print("❌ Repository not found")
        exit(1)
    
    print(f"✅ Repository found: {repo_info.get('html_url')}")
    
    base_path = Path('/home/runner/workspace')
    
    # Files to exclude
    exclude_dirs = {'.git', 'node_modules', '.cache', '.pythonlibs', '.local', '__pycache__', '.pytest_cache'}
    exclude_files = {'.DS_Store', 'desktop.ini'}
    exclude_ext = {'.pyc', '.pyo', '.so'}
    
    def should_exclude(path):
        # Check path parts
        for part in path.parts:
            if part.startswith('.') and part not in {'.gitignore', '.env.example', '.replit', '.upm'}:
                if part in exclude_dirs:
                    return True
        # Check extensions
        if path.suffix in exclude_ext:
            return True
        # Check filenames
        if path.name in exclude_files:
            return True
        return False
    
    # Collect files
    files_to_upload = []
    for file_path in sorted(base_path.rglob('*')):
        if file_path.is_file() and not should_exclude(file_path):
            rel_path = str(file_path.relative_to(base_path))
            files_to_upload.append((file_path, rel_path))
    
    print(f"📁 Found {len(files_to_upload)} files to upload")
    print()
    
    # Upload files
    successful = 0
    failed = []
    
    for file_path, rel_path in files_to_upload:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            success, status, text = upload_file(token, owner, repo, rel_path, content)
            
            if success:
                print(f"✅ {rel_path}")
                successful += 1
            else:
                print(f"⚠️  {rel_path} ({status})")
                failed.append((rel_path, status))
        except Exception as e:
            print(f"❌ {rel_path}: {e}")
            failed.append((rel_path, str(e)))
    
    print()
    print(f"✅ Successfully uploaded: {successful} files")
    if failed:
        print(f"⚠️  Failed: {len(failed)} files")
        for path, error in failed[:5]:
            print(f"   - {path}: {error}")
    
    print()
    print(f"📍 Repository: https://github.com/{owner}/{repo}")
    print("✅ Code is ready in GitHub!")
    print("\n🚀 Go to Railway.app and deploy!")
