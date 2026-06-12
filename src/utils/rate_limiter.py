from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from github.GithubException import RateLimitExceededException

# Decorator to handle GitHub API rate limits
github_retry = retry(
    retry=retry_if_exception_type(RateLimitExceededException),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True
)
