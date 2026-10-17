# Read-only: separate footer/nav links from in-content links; real first paragraphs
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Web
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'

$slugs = @(
  'byok-ai-reporting-tool','csv-to-pdf-report-generator','white-label-client-reporting-agencies',
  'automating-client-reports','client-reporting-software-guide','best-client-reporting-software-freelancers',
  'python-csv-to-pdf-reports','two-weeks-building-naxely','what-should-client-report-include-checklist',
  'anomaly-detection-in-client-reports','google-sheets-client-reports','excel-to-pdf-report-generator'
)

function Get-Hrefs([string]$html) {
  $r = @()
  foreach ($m in [regex]::Matches($html, 'href="([^"]+)"')) { $r += $m.Groups[1].Value }
  return $r
}

# 1. Extract the shared footer + nav from the homepage
$homeHtml = (curl.exe -s 'https://www.naxely.com/') -join "`n"
$fx = $homeHtml.LastIndexOf('<footer')
$footerHtml = if ($fx -ge 0) { $homeHtml.Substring($fx) } else { '' }
$footerSet = [System.Collections.Generic.HashSet[string]]::new()
foreach ($h in (Get-Hrefs $footerHtml)) { [void]$footerSet.Add($h) }
$nx = $homeHtml.IndexOf('<nav')
$navHtml = if ($nx -ge 0) { $homeHtml.Substring($nx, [Math]::Min(12000, $homeHtml.Length - $nx)) } else { '' }
$navSet = [System.Collections.Generic.HashSet[string]]::new()
foreach ($h in (Get-Hrefs $navHtml)) { [void]$navSet.Add($h) }
Write-Output "footer links: $($footerSet.Count) nav links: $($navSet.Count)"
Write-Output ("FOOTER SET: " + (($footerSet | Sort-Object) -join ', '))
Write-Output ''

$pages = @(
  '/', '/pricing', '/faq', '/about', '/contact', '/changelog', '/blog', '/templates',
  '/research/client-reporting-tool-pricing-2026',
  '/compare/agencyanalytics', '/compare/databox', '/compare/dashthis', '/compare/whatagraph',
  '/compare/klipfolio', '/compare/bonsai', '/compare/plutio', '/compare/powerdrill'
)

$pageOut = [ordered]@{}
foreach ($pg in $pages) {
  $html = if ($pg -eq '/') { $homeHtml } else { (curl.exe -s "https://www.naxely.com$pg") -join "`n" }
  $hrefs = Get-Hrefs $html
  $inContent = @{}
  foreach ($s in $slugs) {
    $own = @($hrefs | Where-Object { $_ -match "(?i)/blog/$s(?:[#?]|$)" })
    $contentOnes = @($own | Where-Object { -not $footerSet.Contains($_) -and -not $navSet.Contains($_) })
    if ($contentOnes.Count -gt 0) { $inContent[$s] = $contentOnes.Count }
  }
  $researchContent = @(Get-Hrefs $html | Where-Object { $_ -match '/research/client-reporting-tool-pricing-2026' -and -not $footerSet.Contains($_) -and -not $navSet.Contains($_) })
  $pageOut[$pg] = [ordered]@{ in_content_blog = $inContent; in_content_research_links = $researchContent.Count; total_blog_anchors = (@($hrefs | Where-Object { $_ -match '(?i)/blog/' })).Count }
  Write-Output "page $pg : in-content blog targets: $(($inContent.Keys | Sort-Object) -join ', ') | in-content research: $($researchContent.Count)"
}

# 2. Real first paragraphs
$firstParas = [ordered]@{}
foreach ($slug in $slugs) {
  $html = (curl.exe -s "https://www.naxely.com/blog/$slug") -join "`n"
  $h1end = $html.IndexOf('</h1>')
  $rest = $html.Substring($h1end + 5)
  $fidx = $rest.IndexOf('<footer')
  if ($fidx -lt 0) { $fidx = $rest.Length }
  $body = $rest.Substring(0, $fidx)
  $first = ''; $fw = 0
  foreach ($m in [regex]::Matches($body, '(?s)<p[^>]*>(.*?)</p>')) {
    $t = [System.Web.HttpUtility]::HtmlDecode((($m.Groups[1].Value -replace '<[^>]+>','' -replace '\s+',' ').Trim()))
    $w = ($t -split ' ').Count
    if ($w -ge 15) { $first = $t; $fw = $w; break }
  }
  $firstParas[$slug] = [ordered]@{ first_para = $first; first_para_words = $fw }
  Write-Output "post $slug : first_para_words=$fw :: $($first.Substring(0,[Math]::Min(100,$first.Length)))"
}

$out = [ordered]@{ footer_set = @($footerSet); pages = $pageOut; posts = $firstParas }
$out | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$rawDir\inbound_content_map.json" -Encoding UTF8
Write-Output "WROTE $rawDir\inbound_content_map.json"

