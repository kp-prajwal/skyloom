#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

fail() {
  echo "Setup stopped: $*" >&2
  exit 1
}

for command_name in git gh python3; do
  command -v "$command_name" >/dev/null 2>&1 || fail "Install $command_name, then run this command again."
done

echo "1/7  Testing Skyloom"
python3 -m unittest discover -s tests -v

echo "2/7  Checking GitHub sign-in"
if ! gh auth status >/dev/null 2>&1; then
  echo
  echo "GitHub needs a one-time sign-in. Run:"
  echo "  gh auth login"
  echo "Then run ./scripts/setup.sh again."
  exit 1
fi

github_user="$(gh api user --jq .login)"
default_repo="$github_user/skyloom"
printf "GitHub repository [%s]: " "$default_repo"
read -r repository
repository="${repository:-$default_repo}"
[[ "$repository" == */* ]] || fail "Use the form owner/repository, for example $default_repo."

echo "3/7  Preparing the public GitHub repository"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init
fi
git add .
if ! git diff --cached --quiet; then
  git commit -m "Launch Skyloom"
fi
git branch -M main

if gh repo view "$repository" >/dev/null 2>&1; then
  visibility="$(gh repo view "$repository" --json visibility --jq .visibility)"
  [[ "$visibility" == "PUBLIC" ]] || fail "The repository exists but is not public. Skyloom's zero-cost setup requires a public repository."
  if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "https://github.com/$repository.git"
  fi
  git push -u origin main
else
  gh repo create "$repository" --public --source=. --remote=origin --push
fi

echo "4/7  Collecting Cloudflare Workers AI credentials"
echo "Open Cloudflare Dashboard → Workers AI → Use REST API."
printf "Cloudflare Account ID: "
read -r cloudflare_account_id
[[ -n "$cloudflare_account_id" ]] || fail "Cloudflare Account ID cannot be empty."
printf "Cloudflare API token (hidden): "
read -r -s cloudflare_api_token
echo
[[ -n "$cloudflare_api_token" ]] || fail "Cloudflare API token cannot be empty."

echo "5/7  Saving encrypted GitHub Actions secrets"
printf '%s' "$cloudflare_account_id" | gh secret set CLOUDFLARE_ACCOUNT_ID --repo "$repository"
printf '%s' "$cloudflare_api_token" | gh secret set CLOUDFLARE_API_TOKEN --repo "$repository"
unset cloudflare_api_token

echo "6/7  Enabling workflow writes and GitHub Pages"
gh api --method PUT "repos/$repository/actions/permissions/workflow" \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=false >/dev/null

if ! gh api "repos/$repository/pages" >/dev/null 2>&1; then
  gh api --method POST "repos/$repository/pages" \
    -f 'source[branch]=main' \
    -f 'source[path]=/docs' >/dev/null
fi

echo "7/7  Starting the first cloud generation"
gh workflow run daily.yml --repo "$repository"

owner="${repository%%/*}"
repo_name="${repository##*/}"
echo
echo "Skyloom setup is complete."
echo "Watch the first run: gh run watch --repo $repository"
echo "Gallery: https://${owner}.github.io/${repo_name}/"

