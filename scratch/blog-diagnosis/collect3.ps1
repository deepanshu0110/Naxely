# Read-only: inbound links to each blog post from across the site + first paragraphs
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Web
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'

$slugs = @(
  'byok-ai-reporting-tool','csv-to-pdf-report-generator','white-label-client-reporting-agencies',
  'automating-client-reports','client-reporting-software-guide','best-client-reporting-software-freelancers',
  'python-csv-to-pdf-reports','two-weeks-building-naxely','what-should-client-report-include-checklist',
  'anomaly-detection-in-client-reports','google-sheets-client-reports','excel-to-pdf-report-generator'
)

$pages = @(
  '/', '/pricing', '/faq', '/about', '/contact', '/changelog', '/blog', '/templates',
  '/research/client-reporting-tool-pricing-2026',
  '/compare/agencyanalytics', '/compare/databox', '/compare/dashthis', '/compare/whatagraph',
  '/compare/klipfolio', '/compare/bonsai', '/compare/plutio', '/compare/powerdrill'
)

$pageLinks = [ordered]@{}
foreach ($pg in $pages) {
  $html = (curl.exe -s "https://www.naxely.com$pg") -join "`n"
  $hrefs = @()
  foreach ($m in [regex]::Matches($html, 'href="([^"]+)"')) { $hrefs += $m.Groups[1].Value }
  $blogHits = @{}
  foreach ($s in $slugs) {
    $c = ($hrefs | Where-Object { $_ -match "(?i)/blog/$s(?:[#?]|$)" }).Count
    if ($c -gt 0) { $blogHits[$s] = $c }
  }
  $researchHits = ($hrefs | Where-Object { $_ -match '/research/client-reporting-tool-pricing-2026' }).Count
  $compareHits = ($hrefs | Where-Object { $_ -match '/compare/' }).Count
  $pageLinks[$pg] = [ordered]@{ status_len = $html.Length; blog = $blogHits; research_links = $researchHits; compare_links = $compareHits }
  Write-Output "page $pg : blogHits=$(($blogHits.Keys).Count) research=$researchHits compare=$compareHits"
}

# first paragraphs from live HTML
$firstParas = [ordered]@{}
foreach ($slug in $slugs) {
  $html = (curl.exe -s "https://www.naxely.com/blog/$slug") -join "`n"
  $h1end = $html.IndexOf('</h1>')
  $rest = $html.Substring($h1end + 5)
  $fidx = $rest.IndexOf('<footer')
  if ($fidx -lt 0) { $fidx = $rest.Length }
  $body = $rest.Substring(0, $fidx)
  $m = [regex]::Match($body, '(?s)<p[^>]*>(.*?)</p>')
  $first = ''
  if ($m.Success) { $first = [System.Web.HttpUtility]::HtmlDecode((($m.Groups[1].Value -replace '<[^>]+>','' -replace '\s+',' ').Trim())) }
  $fw = ($first -split ' ').Count
  # date line: first 120 chars of saved text
  $txtFile = "$rawDir\articles\$slug.txt"
  $head = ''
  if (Test-Path $txtFile) { $head = (Get-Content $txtFile -Raw).Substring(0, [Math]::Min(120, (Get-Content $txtFile -Raw).Length)) }
  $firstParas[$slug] = [ordered]@{ first_para = $first; first_para_words = $fw; text_head = $head }
  Write-Output "post $slug : first_para_words=$fw"
}

$out = [ordered]@{ pages = $pageLinks; posts = $firstParas }
$out | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$rawDir\inbound_map.json" -Encoding UTF8
Write-Output "WROTE $rawDir\inbound_map.json"
