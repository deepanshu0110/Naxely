# Read-only: verify all article links resolve + curl timing proxy (PSI unavailable)
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Web
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'
$out = @()
function W($s) { $script:out += $s; Write-Output $s }

# 1. og fields sanity
$lp = @(Get-Content "$rawDir\live_posts.json" -Raw | ConvertFrom-Json)
W '===== OG fields per post ====='
foreach ($p in $lp) {
  $ogOk = ($p.og_title -and $p.og_desc -and $p.og_image)
  W "$($p.slug): og_title='$($p.og_title)' og_image=$($p.og_image) tw_card=$($p.tw_card) -> ok=$([bool]$ogOk)"
}

# 2. unique hrefs from article bodies
$as = @(Get-Content "$rawDir\article_summary.json" -Raw | ConvertFrom-Json)
$hrefs = New-Object System.Collections.Generic.HashSet[string]
foreach ($p in $as) {
  foreach ($l in $p.internal_links) { [void]$hrefs.Add($l) }
  foreach ($e in $p.external_links) { [void]$hrefs.Add($e) }
}
W ''
W '===== link status check ====='
foreach ($h in ($hrefs | Sort-Object)) {
  $u = if ($h -match '^https?://') { $h } else { "https://www.naxely.com$h" }
  $code = curl.exe -s -o NUL -w "%{http_code}" -L --max-time 30 $u
  W "$code  $u"
}

# 3. curl timing proxy for /blog + 4 posts
W ''
W '===== curl timing proxy (TTFB / total / bytes) ====='
$timingUrls = @(
  'https://www.naxely.com/blog',
  'https://www.naxely.com/blog/client-reporting-software-guide',
  'https://www.naxely.com/blog/best-client-reporting-software-freelancers',
  'https://www.naxely.com/blog/automating-client-reports',
  'https://www.naxely.com/blog/what-should-client-report-include-checklist'
)
foreach ($u in $timingUrls) {
  $r = (curl.exe -s -o NUL -w "ttfb=%{time_starttransfer}s total=%{time_total}s bytes=%{size_download} http=%{http_code} proto=%{http_version}" --max-time 45 $u)
  W "$u -> $r"
}
# run again to show cached/edge consistency
W '-- second run --'
foreach ($u in $timingUrls) {
  $r = (curl.exe -s -o NUL -w "ttfb=%{time_starttransfer}s total=%{time_total}s bytes=%{size_download}" --max-time 45 $u)
  W "$u -> $r"
}

$out | Set-Content -LiteralPath "$rawDir\links_and_timing.txt" -Encoding UTF8
Write-Output "WROTE $rawDir\links_and_timing.txt"
