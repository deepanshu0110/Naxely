# Read-only: extract article body regions from live HTML
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Web
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'
$artDir = "$rawDir\articles"
New-Item -ItemType Directory -Force -Path $artDir | Out-Null

$slugs = @(
  'byok-ai-reporting-tool','csv-to-pdf-report-generator','white-label-client-reporting-agencies',
  'automating-client-reports','client-reporting-software-guide','best-client-reporting-software-freelancers',
  'python-csv-to-pdf-reports','two-weeks-building-naxely','what-should-client-report-include-checklist',
  'anomaly-detection-in-client-reports','google-sheets-client-reports','excel-to-pdf-report-generator'
)

$summary = @()
foreach ($slug in $slugs) {
  $html = (curl.exe -s "https://www.naxely.com/blog/$slug") -join "`n"
  $h1end = $html.IndexOf('</h1>')
  if ($h1end -lt 0) { Write-Output "NO H1 $slug"; continue }
  $rest = $html.Substring($h1end + 5)
  $fidx = $rest.IndexOf('<footer')
  if ($fidx -lt 0) { $fidx = $rest.Length }
  $body = $rest.Substring(0, $fidx)

  # text version
  $txt = $body -replace '(?s)<script.*?</script>', ' '
  $txt = $txt -replace '(?s)<style.*?</style>', ' '
  $txt = $txt -replace '<[^>]+>', ' '
  $txt = [System.Web.HttpUtility]::HtmlDecode($txt)
  $txt = $txt -replace '\s+', ' '
  $txt = $txt.Trim()
  Set-Content -LiteralPath "$artDir\$slug.txt" -Value $txt -Encoding UTF8

  # paragraphs (from raw body, before tag strip)
  $paras = [regex]::Matches($body, '(?s)<p[^>]*>(.*?)</p>')
  $pw = @()
  foreach ($m in $paras) {
    $t = ($m.Groups[1].Value -replace '<[^>]+>', ' ' -replace '\s+', ' ').Trim()
    $t = [System.Web.HttpUtility]::HtmlDecode($t)
    $wc = ($t -split ' ').Count
    if ($wc -gt 0) { $pw += [ordered]@{ words = $wc; text = $t.Substring(0, [Math]::Min(90, $t.Length)) } }
  }
  $over120 = ($pw | Where-Object { $_.words -gt 120 })
  $avgPara = if ($pw.Count -gt 0) { [Math]::Round((($pw | Measure-Object words -Average).Average), 1) } else { 0 }

  # lists and tables
  $ulCount = ([regex]::Matches($body, '<ul')).Count
  $olCount = ([regex]::Matches($body, '<ol')).Count
  $tblCount = ([regex]::Matches($body, '<table')).Count

  # CTAs inside article
  $ctas = @()
  foreach ($m in [regex]::Matches($body, '(?s)<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>')) {
    $href = $m.Groups[1].Value
    $t = ($m.Groups[2].Value -replace '<[^>]+>', ' ' -replace '\s+', ' ').Trim()
    $t = [System.Web.HttpUtility]::HtmlDecode($t)
    if ($href -match '/signup|/pricing|/dashboard|/contact' -or $t -match 'sign up|signup|try it|get started|start free|Try Naxely|create|free tier') {
      $ctas += [ordered]@{ href = $href; text = $t }
    }
  }

  # outbound + internal link hrefs in article
  $hrefs = @()
  foreach ($m in [regex]::Matches($body, '<a\b[^>]*href="([^"]+)"')) { $hrefs += $m.Groups[1].Value }
  $internal = $hrefs | Where-Object { $_ -like '/blog/*' -or $_ -like '/compare/*' -or $_ -match '^/(pricing|faq|changelog|about|contact)$' }
  $external = $hrefs | Where-Object { $_ -match '^https?://' -and $_ -notmatch 'naxely\.com' }

  $summary += [ordered]@{
    slug = $slug
    article_words = ($txt -split ' ').Count
    paragraphs = $pw.Count
    avg_para_words = $avgPara
    paras_over_120 = $over120.Count
    over120_detail = $over120
    ul = $ulCount; ol = $olCount; tables = $tblCount
    h2 = @([regex]::Matches($body, '(?s)<h2[^>]*>(.*?)</h2>') | ForEach-Object { [System.Web.HttpUtility]::HtmlDecode((($_.Groups[1].Value -replace '<[^>]+>','' -replace '\s+',' ').Trim())) })
    h3 = @([regex]::Matches($body, '(?s)<h3[^>]*>(.*?)</h3>') | ForEach-Object { [System.Web.HttpUtility]::HtmlDecode((($_.Groups[1].Value -replace '<[^>]+>','' -replace '\s+',' ').Trim())) })
    cta_count = $ctas.Count
    ctas = $ctas
    internal_links = @($internal)
    external_links = @($external)
  }
  Write-Output "done $slug"
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$rawDir\article_summary.json" -Encoding UTF8
Write-Output "WROTE $rawDir\article_summary.json"
