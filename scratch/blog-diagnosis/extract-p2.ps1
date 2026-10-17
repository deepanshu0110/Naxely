$dir = 'scratch/blog-diagnosis/raw/articles'
Add-Type -AssemblyName System.Web

# ---- checklist £ context ----
$t = (Get-Content "$dir\what-should-client-report-include-checklist.txt" -Raw) -replace '\s+', ' '
Write-Output '===== checklist GBP context ====='
foreach ($m in [regex]::Matches($t, '.{0,100}£.{0,100}')) { Write-Output "  $($m.Value)" }

# ---- last 2 paragraphs of the 5 CTA-less posts (from live HTML) ----
Write-Output ''
Write-Output '===== last 2 paragraphs of CTA-less posts ====='
foreach ($slug in @('python-csv-to-pdf-reports','two-weeks-building-naxely','anomaly-detection-in-client-reports','google-sheets-client-reports','excel-to-pdf-report-generator')) {
  $html = (curl.exe -s "https://www.naxely.com/blog/$slug") -join "`n"
  $h1end = $html.IndexOf('</h1>')
  $rest = $html.Substring($h1end + 5)
  $fidx = $rest.IndexOf('<footer')
  if ($fidx -lt 0) { $fidx = $rest.Length }
  $body = $rest.Substring(0, $fidx)
  $paras = @()
  foreach ($m in [regex]::Matches($body, '(?s)<p[^>]*>(.*?)</p>')) {
    $p = [System.Web.HttpUtility]::HtmlDecode((($m.Groups[1].Value -replace '<[^>]+>',' ') -replace '\s+',' ').Trim())
    if ($p.Length -gt 20) { $paras += $p }
  }
  $last2 = @($paras)[-2..-1]
  Write-Output "########## $slug"
  foreach ($p in $last2) { Write-Output "  $p" }
}

# ---- CTA wording on posts that HAVE one =====
Write-Output ''
Write-Output '===== CTA component + wording (posts that have one) ====='
$ctaPosts = @('byok-ai-reporting-tool','csv-to-pdf-report-generator','white-label-client-reporting-agencies','automating-client-reports','client-reporting-software-guide','best-client-reporting-software-freelancers','what-should-client-report-include-checklist')
foreach ($slug in $ctaPosts) {
  $t = (Get-Content "$dir\$slug.txt" -Raw) -replace '\s+', ' '
  $hits = @()
  foreach ($m in [regex]::Matches($t, '(?i)(start free|generate your first report|try it free|try naxely free)[^.<]*')) { $hits += $m.Value.Trim() }
  Write-Output "$slug : <Link to=\"/signup\"> $($hits -join ' | ')"
}

# ---- 2d candidates: Excel mentions (link to excel-to-pdf) ----
Write-Output ''
Write-Output '===== Excel mentions (candidate link sentences -> /blog/excel-to-pdf-report-generator) ====='
foreach ($f in Get-ChildItem $dir -Filter *.txt | Sort-Object Name) {
  $slug = $f.BaseName
  if (@('automating-client-reports','client-reporting-software-guide') -contains $slug) { continue }
  $t = (Get-Content $f.FullName -Raw) -replace '\s+', ' '
  foreach ($m in [regex]::Matches($t, '[^.?!]*[Ee]xcel[^.?!]*[.?!]')) {
    $s = $m.Value.Trim()
    if ($s.Length -gt 0) { Write-Output "[$slug] $s" }
  }
}

# ---- 2d candidates: launch/build mentions (link to two-weeks) ----
Write-Output ''
Write-Output '===== launch/build mentions (candidate link sentences -> /blog/two-weeks-building-naxely) ====='
foreach ($f in Get-ChildItem $dir -Filter *.txt | Sort-Object Name) {
  $slug = $f.BaseName
  if (@('automating-client-reports','client-reporting-software-guide','two-weeks-building-naxely') -contains $slug) { continue }
  $t = (Get-Content $f.FullName -Raw) -replace '\s+', ' '
  foreach ($m in [regex]::Matches($t, '(?i)[^.?!]*(two.?weeks|launch|building naxely|bugs? that shipped|we launched)[^.?!]*[.?!]')) {
    $s = $m.Value.Trim()
    if ($s.Length -gt 0) { Write-Output "[$slug] $s" }
  }
}
