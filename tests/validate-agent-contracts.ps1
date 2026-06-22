$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$qaReviewerPath = Join-Path $repoRoot '.claude/agents/qa-reviewer.md'
$qaReviewer = Get-Content -Raw -LiteralPath $qaReviewerPath

$toolsMatch = [regex]::Match(
    $qaReviewer,
    '(?m)^tools:\s*(?<tools>.+)$'
)

if (-not $toolsMatch.Success) {
    throw 'qa-reviewer.md must declare its tools in YAML frontmatter.'
}

$tools = $toolsMatch.Groups['tools'].Value -split ',' | ForEach-Object { $_.Trim() }

if ('Edit' -notin $tools) {
    throw 'qa-reviewer.md must declare Edit because it updates task status and session logs.'
}

Write-Output 'Agent contracts valid.'
