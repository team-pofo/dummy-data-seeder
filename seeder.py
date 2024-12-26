import requests
import psycopg
import json
from psycopg.rows import dict_row

# 데이터베이스 연결 정보
DB_CONFIG = {
    "dbname": "pofo",
    "user": "postgres",
    "password": "MyStrongcur3P@ssw0rd!",
    "host": "localhost",
    "port": 5432,
}

# GitHub API 정보
GITHUB_API_URL = "https://api.github.com/search/repositories"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
}

INSERT_PROJECT_SQL = """
INSERT INTO project (
    title, bio, urls, image_urls, content, is_approved, category, user_id
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
);
"""

def truncate_bio(bio: str, max_length: int = 255) -> str:
    """bio가 255자를 초과하면 잘라서 반환하는 함수"""
    if bio and len(bio) > max_length:
        return bio[:max_length]
    return bio

def fetch_github_repositories():
    """GitHub에서 인기 저장소 데이터를 가져옴"""
    params = {
        "q": "stars:>10000",
        "sort": "stars",
        "order": "desc",
        "per_page": 100,
    }
    response = requests.get(GITHUB_API_URL, headers=GITHUB_HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"GitHub API로부터 {len(data['items'])}개의 저장소 데이터를 가져왔습니다.")
    print(f"가져온 데이터 예시: {json.dumps(data['items'][0], indent=2)}")
    return data["items"]

def get_readme_content(owner: str, repo_name: str) -> str:
    """GitHub 저장소의 README 파일을 가져오는 함수"""
    url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": ""
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        readme_data = response.json()
        content = readme_data.get("content", "")
        return content
    else:
        print(f"Error fetching README for {repo_name}: {response.status_code}")
        return "No README content available"

def insert_repositories(repositories):
    """가져온 저장소 데이터를 PostgreSQL에 삽입"""
    with psycopg.connect(**DB_CONFIG, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for repo in repositories:
                name = repo["name"]
                truncated_bio = truncate_bio(repo["description"])
                readme_content = get_readme_content(repo["owner"]["login"], repo["name"])
                urls = [repo["html_url"]]
                image_urls = ["https://avatars.githubusercontent.com/u/150318721?v=4"]

                urls_str = json.dumps(urls)
                image_urls_str = json.dumps(image_urls)

                cur.execute(
                    INSERT_PROJECT_SQL,
                    (
                        name,  # title
                        truncated_bio,  # bio
                        urls_str,  # urls
                        image_urls_str,  # image_urls
                        readme_content,  # content
                        False,  # is_approved
                        "CATEGORY_A",  # category
                        1 # user_id,
                    ),
                )
            conn.commit()
            print(f"{len(repositories)}개의 저장소가 삽입되었습니다.")

if __name__ == "__main__":
    print("GitHub에서 인기 저장소를 가져오는 중...")
    repositories = fetch_github_repositories()

    print("가져온 데이터를 데이터베이스에 삽입하는 중...")
    insert_repositories(repositories)
    print("작업 완료!")
