from typing import List, Optional
from github import Github
from langchain_core.documents import Document
from ..utils.github_utils import parse_github_url
from ..utils.rate_limiter import github_retry

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.cpp', '.md', '.json', '.yaml'}
IGNORE_PATHS = {'node_modules', '__pycache__', 'dist', 'build', '.git'}

from github.GithubException import RateLimitExceededException

def load_repository(repo_url: str, token: Optional[str] = None) -> List[Document]:
    """Fetches all relevant source files from a GitHub repository."""
    documents = []
    
    try:
        g = Github(token, retry=0) if token else Github(retry=0)
        repo_name = parse_github_url(repo_url)
        repo = g.get_repo(repo_name)
        
        default_branch = repo.default_branch
        tree = repo.get_git_tree(default_branch, recursive=True)
        
        all_files = []
        for element in tree.tree:
            if element.type == "blob":
                all_files.append(element.path)
                # Check ignores
                path_parts = element.path.split('/')
                if any(ignored in path_parts for ignored in IGNORE_PATHS):
                    continue
                    
                if any(element.path.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    try:
                        # Fetch the actual file blob
                        file_blob = repo.get_git_blob(element.sha)
                        import base64
                        content = base64.b64decode(file_blob.content).decode('utf-8')
                        
                        metadata = {
                            "source": element.path,
                            "url": f"https://github.com/{repo_name}/blob/{default_branch}/{element.path}",
                            "sha": element.sha,
                            "repo": repo_name
                        }
                        documents.append(Document(page_content=content, metadata=metadata))
                    except Exception as e:
                        print(f"Skipping {element.path} due to error: {e}")
        
        # Add a synthetic document containing the full repository file structure
        if all_files:
            structure_content = "Repository File Structure and Contents List:\n" + "\n".join(all_files)
            structure_doc = Document(
                page_content=structure_content, 
                metadata={
                    "source": "repo_structure.txt", 
                    "url": f"https://github.com/{repo_name}",
                    "repo": repo_name
                }
            )
            documents.append(structure_doc)
    except RateLimitExceededException:
        raise Exception("GitHub API rate limit exceeded. Please provide a GitHub token to continue.")
    except Exception as e:
        raise Exception(f"Failed to fetch repository: {str(e)}")
                    
    return documents
