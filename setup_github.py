#!/usr/bin/env python3
import os
import json
import subprocess
import requests

# Get GitHub token from Replit connection
def get_github_token():
    """Get GitHub token from Replit environment"""
    # Try to get from Replit connection
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
            # Try alternative path
            token = connection.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
            if token:
                return token
    except Exception as e:
        print(f"Error getting token from Replit: {e}")
    
    return None

# Create repository on GitHub
def create_github_repo(token, repo_name="discord-bot"):
    """Create a GitHub repository"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'name': repo_name,
        'description': 'Discord Bot for Gaming Tournaments with Web Dashboard',
        'private': False,
        'auto_init': False
    }
    
    try:
        response = requests.post(
            'https://api.github.com/user/repos',
            headers=headers,
            json=data
        )
        
        if response.status_code in [201, 200]:
            repo_data = response.json()
            print(f"✅ Repository created: {repo_data['html_url']}")
            return repo_data
        else:
            print(f"Error creating repo: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Setup git and push
def setup_git_and_push(token, repo_url, username="deividdarosa"):
    """Setup git and push to GitHub"""
    try:
        # Configure git
        subprocess.run(['git', 'config', 'user.email', 'deividdarosa4@gmail.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', username], check=True)
        
        # Check if repo already initialized
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            subprocess.run(['git', 'init'], check=True)
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Check for changes
        status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if status_result.stdout.strip():
            # Commit
            subprocess.run(['git', 'commit', '-m', 'Discord Bot - Tournaments & Dashboard'], check=True)
        
        # Set remote
        try:
            subprocess.run(['git', 'remote', 'remove', 'origin'], capture_output=True)
        except:
            pass
        
        # Use token-based URL
        remote_url = repo_url.replace('https://', f'https://{username}:{token}@')
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
        
        # Push
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
        
        print("✅ Code pushed to GitHub!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    os.chdir('/home/runner/workspace')
    
    print("🔧 Setting up GitHub repository...")
    
    # Get token
    token = get_github_token()
    if not token:
        print("❌ Could not get GitHub token from Replit connection")
        print("Please ensure GitHub is connected via the integration")
        exit(1)
    
    print(f"✅ GitHub token obtained")
    
    # Create repository
    repo_data = create_github_repo(token, "discord-bot")
    if not repo_data:
        # Repository might already exist
        print("⚠️ Repository creation failed (may already exist)")
        repo_url = "https://github.com/deividdarosa/discord-bot.git"
    else:
        repo_url = repo_data['clone_url']
    
    print(f"📍 Repository URL: {repo_url}")
    
    # Setup git and push
    if setup_git_and_push(token, repo_url):
        print("\n✅ GitHub setup complete!")
        print(f"✅ Your repository: https://github.com/deividdarosa/discord-bot")
        print("\n🚀 Next: Go to Railway.app to deploy!")
    else:
        print("\n❌ Failed to push code")
