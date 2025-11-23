#!/usr/bin/env python3
import os
import requests
import base64
import json
from pathlib import Path

def get_github_token():
    """Get GitHub token from Replit connection"""
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

def upload_files_to_github(token, owner, repo):
    """Upload all files to GitHub using API"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    base_path = Path('/home/runner/workspace')
    files_uploaded = 0
    
    # Files to exclude
    exclude = {'.git', 'node_modules', '.cache', '.pythonlibs', '.local', '__pycache__', '.pytest_cache', 'dist', 'build'}
    exclude_extensions = {'.pyc', '.pyo', '.so', '.egg-info'}
    
    def should_exclude(path):
        for part in path.parts:
            if part in exclude:
                return True
        if path.suffix in exclude_extensions:
            return True
        return False
    
    # Collect all files
    files_to_upload = []
    for file_path in base_path.rglob('*'):
        if file_path.is_file() and not should_exclude(file_path):
            rel_path = file_path.relative_to(base_path)
            files_to_upload.append((file_path, str(rel_path)))
    
    print(f"📁 Found {len(files_to_upload)} files to upload")
    
    # Upload each file
    for file_path, rel_path in files_to_upload:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Try to decode as text for text files
            try:
                content_str = content.decode('utf-8')
                is_binary = False
            except UnicodeDecodeError:
                content_str = base64.b64encode(content).decode('utf-8')
                is_binary = True
            
            data = {
                'message': f'Add {rel_path}',
                'content': content_str,
                'branch': 'main'
            }
            
            if is_binary:
                data['encoding'] = 'base64'
            
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{rel_path}'
            response = requests.put(url, headers=headers, json=data)
            
            if response.status_code in [201, 200]:
                files_uploaded += 1
                print(f"✅ {rel_path}")
            else:
                print(f"⚠️  {rel_path}: {response.status_code}")
        except Exception as e:
            print(f"❌ {rel_path}: {e}")
    
    return files_uploaded

if __name__ == '__main__':
    print("🚀 Uploading code to GitHub...")
    
    token = get_github_token()
    if not token:
        print("❌ Could not get GitHub token")
        exit(1)
    
    print("✅ Token obtained")
    
    owner = "deividdarosa"
    repo = "discord-bot"
    
    files_uploaded = upload_files_to_github(token, owner, repo)
    
    print(f"\n✅ Uploaded {files_uploaded} files!")
    print(f"📍 Repository: https://github.com/{owner}/{repo}")
    print("\n🚀 Go to Railway.app and deploy!")
