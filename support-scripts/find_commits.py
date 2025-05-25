import git
import os

def get_top_commits_by_changes(repo_path='.', top_n=50):
    repo = git.Repo(repo_path)

    if repo.bare:
        raise Exception("Repository is bare.")

    commit_changes = []

    for commit in repo.iter_commits(repo.active_branch):
        message = commit.message.lower()
        if "merge" in message or "reapply" in message or "squashed" in message:
            continue  # skip unwanted commits

        stats = commit.stats.total
        total_changes = stats['insertions'] + stats['deletions']
        commit_changes.append((total_changes, commit))

    # Sort by total changes descending
    commit_changes.sort(reverse=True, key=lambda x: x[0])
    top_commits = commit_changes[:top_n]

    print(f"Top {top_n} commits by total line changes (excluding 'Merge' and 'Reapply'):\n")
    for rank, (changes, commit) in enumerate(top_commits, 1):
        print(f"{rank:2d}. {commit.hexsha[:8]} | {changes} lines changed | "
              f"+{commit.stats.total['insertions']}/-{commit.stats.total['deletions']} | "
              f"{commit.author.name} | {commit.committed_datetime.strftime('%Y-%m-%d')} | "
              f"{commit.message.strip().splitlines()[0]}")

if __name__ == "__main__":
    get_top_commits_by_changes()
