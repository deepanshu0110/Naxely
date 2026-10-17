# Read-only blog diagnosis collector — writes JSON to scratch/blog-diagnosis/raw/
$ErrorActionPreference = 'Continue'
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$slugs = @(
  'byok-ai-reporting-tool',
  'csv-to-pdf-report-generator',
  'white-label-client-reporting-agencies',
  'automating-client-reports',
  'client-reporting-software-guide',
  'best-client-reporting-software-freelancers',
  'python-csv-to-pdf-reports',
  'two-weeks-building-naxely',
  'what-should-client-report-include-checklist',
  'anomaly-detection-in-client-reports',
  'google-sheets-client-reports',
  'excel-to-pdf-report-generator'
)

function Get-Meta($html, $key) {
  $m = [regex]::Match($html, "<meta[^>]*(?:name|property)=`"$([regex]::Escape($key))`"[^>]*>")
  if ($m.Success) {
    $c = [regex]::Match($m.Value, 'content="([^"]*)"')
    if ($c.Success) { return $c.Groups[1].Value }
  }
  return $null
}

function Get-WordCount($html) {
  $t = $html -replace '(?s)<script.*?</script>', ' '
  $t = $t -replace '(?s)<style.*?</style>', ' '
  $t = $t -replace '(?s)<noscript.*?</noscript>', ' '
  $t = $t -replace '<[^>]+>', ' '
  $t = [System.Web.HttpUtility]::HtmlDecode($t)
  $t = $t -replace '\s+', ' '
  return ($t.Trim() -split ' ').Count
}

$results = @()

foreach ($slug in $slugs) {
  $url = "https://www.naxely.com/blog/$slug"
  $html = curl.exe -s $url
  $status = curl.exe -s -o NUL -w '%{http_code}' $url

  $o = [ordered]@{}
  $o.slug = $slug
  $o.url = $url
  $o.status = [int]$status

  # ---- variants ----
  $variants = [ordered]@{}
  $vset = @{
    'nonwww_https' = "https://naxely.com/blog/$slug"
    'nonwww_http'  = "http://naxely.com/blog/$slug"
    'www_http'     = "http://www.naxely.com/blog/$slug"
    'trailing'     = "https://www.naxely.com/blog/$slug/"
    'uppercase'    = "https://www.naxely.com/Blog/$slug"
  }
  foreach ($k in $vset.Keys) {
    $u = $vset[$k]
    $first = curl.exe -s -o NUL -D - -w 'FIRST:%{http_code}' $u 2>$null
    $fcode = ([regex]::Match(($first -join "`n"), 'FIRST:(\d+)')).Groups[1].Value
    $loc = ([regex]::Match(($first -join "`n"), '(?im)^location:\s*(.+)$')).Groups[1].Value.Trim()
    $fin = curl.exe -s -o NUL -L -w '%{http_code}' $u
    $variants[$k] = @{ first = $fcode; location = $loc; final = $fin }
  }
  $o.variants = $variants

  # ---- head ----
  $tm = [regex]::Match($html, '(?s)<title[^>]*>(.*?)</title>')
  $title = if ($tm.Success) { [System.Web.HttpUtility]::HtmlDecode($tm.Groups[1].Value) } else { $null }
  $o.title = $title
  $o.title_len = if ($title) { $title.Length } else { 0 }
  $o.description = Get-Meta $html 'description'
  $o.desc_len = if ($o.description) { $o.description.Length } else { 0 }
  $can = [regex]::Match($html, '<link[^>]*rel="canonical"[^>]*href="([^"]+)"')
  $o.canonical = if ($can.Success) { $can.Groups[1].Value } else { $null }
  $o.robots_meta_count = ([regex]::Matches($html, 'name="robots"')).Count
  $o.og_title = Get-Meta $html 'og:title'
  $o.og_desc = Get-Meta $html 'og:description'
  $o.og_image = Get-Meta $html 'og:image'
  $o.tw_title = Get-Meta $html 'twitter:title'
  $o.tw_desc = Get-Meta $html 'twitter:description'
  $o.tw_image = Get-Meta $html 'twitter:image'
  $o.tw_card = Get-Meta $html 'twitter:card'

  # ---- headings ----
  $heads = [regex]::Matches($html, '(?s)<(h[1-6])[^>]*>(.*?)</\1>')
  $horder = @()
  foreach ($m in $heads) {
    $txt = ($m.Groups[2].Value -replace '<[^>]+>', '' -replace '\s+', ' ').Trim()
    $txt = [System.Web.HttpUtility]::HtmlDecode($txt)
    if ($txt.Length -gt 0) { $horder += "$($m.Groups[1].Value):$txt" }
  }
  $o.headings = $horder
  $o.h1_count = ($heads | Where-Object { $_.Groups[1].Value -eq 'h1' }).Count
  $h1m = [regex]::Match($html, '(?s)<h1[^>]*>(.*?)</h1>')
  $o.h1 = if ($h1m.Success) { ([System.Web.HttpUtility]::HtmlDecode(($h1m.Groups[1].Value -replace '<[^>]+>', '' -replace '\s+', ' '))).Trim() } else { $null }

  # heading level skips
  $levels = $heads | ForEach-Object { [int]$_.Groups[1].Value.Substring(1) }
  $skips = @()
  for ($i = 1; $i -lt $levels.Count; $i++) { if ($levels[$i] - $levels[$i-1] -gt 1) { $skips += "$($levels[$i-1])->$($levels[$i])" } }
  $o.heading_skips = $skips

  # ---- words ----
  $o.words_raw = Get-WordCount $html

  # ---- json-ld ----
  $lds = [regex]::Matches($html, '(?s)<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>')
  $ldinfo = @()
  foreach ($m in $lds) {
    $txt = $m.Groups[1].Value.Trim()
    $valid = $false; $typ = $null; $dpub = $null; $dmod = $null; $auth = $null; $img = $null
    try {
      $obj = $txt | ConvertFrom-Json
      $valid = $true
      $typ = $obj.'@type'
      $dpub = $obj.datePublished; $dmod = $obj.dateModified
      if ($obj.author) { $auth = $obj.author.name + '|' + $obj.author.url }
      $img = $obj.image
    } catch { $valid = $false }
    $ldinfo += [ordered]@{ type = $typ; valid = $valid; datePublished = $dpub; dateModified = $dmod; author = $auth; image = $img; raw_len = $txt.Length }
  }
  $o.jsonld = $ldinfo

  # ---- images ----
  $imgs = [regex]::Matches($html, '(?s)<img\b[^>]*>')
  $imginfo = @()
  foreach ($m in $imgs) {
    $tag = $m.Value
    $src = ([regex]::Match($tag, 'src="([^"]*)"')).Groups[1].Value
    $alt = ([regex]::Match($tag, 'alt="([^"]*)"')).Groups[1].Value
    $w = ([regex]::Match($tag, 'width="([^"]*)"')).Groups[1].Value
    $hh = ([regex]::Match($tag, 'height="([^"]*)"')).Groups[1].Value
    $load = ([regex]::Match($tag, 'loading="([^"]*)"')).Groups[1].Value
    $imginfo += [ordered]@{ src = $src; alt = $alt; width = $w; height = $hh; loading = $load }
  }
  $o.images = $imginfo
  $o.img_count = $imginfo.Count
  $o.img_missing_alt = ($imginfo | Where-Object { [string]::IsNullOrWhiteSpace($_.alt) }).Count
  $o.img_missing_dims = ($imginfo | Where-Object { [string]::IsNullOrWhiteSpace($_.width) -or [string]::IsNullOrWhiteSpace($_.height) }).Count

  # ---- links ----
  $links = [regex]::Matches($html, '(?s)<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>')
  $li = @()
  foreach ($m in $links) {
    $href = $m.Groups[1].Value
    $txt = ($m.Groups[2].Value -replace '<[^>]+>', '' -replace '\s+', ' ').Trim()
    $li += [ordered]@{ href = $href; text = $txt }
  }
  $o.links = $li
  $o.link_count = $li.Count
  $o.internal_links = ($li | Where-Object { $_.href -like '/blog/*' -or $_.href -like '/compare/*' -or $_.href -eq '/pricing' -or $_.href -like 'https://www.naxely.com/*' }).Count

  # ---- mixed content ----
  $o.mixed_http_assets = @([regex]::Matches($html, '(?:src|href)="http://[^"]+"') | ForEach-Object { $_.Value }) -join ' | '

  $results += $o
  Write-Output "done $slug"
}

$results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$rawDir\live_posts.json" -Encoding UTF8
Write-Output "WROTE $rawDir\live_posts.json"
