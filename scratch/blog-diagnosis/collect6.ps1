# Read-only: PageSpeed Insights mobile (free API, no key)
$ErrorActionPreference = 'Continue'
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'
$psiDir = "$rawDir\psi"
New-Item -ItemType Directory -Force -Path $psiDir | Out-Null

$urls = @(
  'https://www.naxely.com/blog',
  'https://www.naxely.com/blog/client-reporting-software-guide',
  'https://www.naxely.com/blog/best-client-reporting-software-freelancers',
  'https://www.naxely.com/blog/automating-client-reports',
  'https://www.naxely.com/blog/what-should-client-report-include-checklist'
)

foreach ($u in $urls) {
  $enc = [uri]::EscapeDataString($u)
  $api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=$enc&strategy=mobile&category=performance"
  $name = ($u -replace 'https://www\.naxely\.com/blog', 'blog') -replace '/', '_'
  if ($name -eq 'blog') { $name = 'blog_index' }
  $json = curl.exe -s --max-time 120 $api
  $text = $json -join "`n"
  if ($text.Length -lt 100 -or $text -match '"error"') {
    Write-Output "PSI FAIL for $u : $($text.Substring(0,[Math]::Min(300,$text.Length)))"
    continue
  }
  Set-Content -LiteralPath "$psiDir\$name.json" -Value $text -Encoding UTF8
  try {
    $o = $text | ConvertFrom-Json
    $score = [Math]::Round($o.lighthouseResult.categories.performance.score * 100)
    $a = $o.lighthouseResult.audits
    Write-Output "$u -> score=$score LCP=$($a.'largest-contentful-paint'.displayValue) CLS=$($a.'cumulative-layout-shift'.displayValue) TBT=$($a.'total-blocking-time'.displayValue) FCP=$($a.'first-contentful-paint'.displayValue) SI=$($a.'speed-index'.displayValue) TTFB=$($a.'server-response-time'.displayValue)"
  } catch { Write-Output "PSI parse fail for $u : $_" }
}
Write-Output 'DONE'
