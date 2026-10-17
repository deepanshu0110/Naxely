# Read-only: entity consistency + llms.txt + robots.txt + sameAs checks
$ErrorActionPreference = 'Continue'
Add-Type -AssemblyName System.Web
$rawDir = 'C:\Users\Deepanshu\OneDrive\Desktop\Apps\scratch\blog-diagnosis\raw'
$out = @()

function W($s) { $script:out += $s; Write-Output $s }

$homeHtml = (curl.exe -s 'https://www.naxely.com/') -join "`n"
$about = (curl.exe -s 'https://www.naxely.com/about') -join "`n"
$llms = (curl.exe -s 'https://www.naxely.com/llms.txt') -join "`n"
$robots = (curl.exe -s 'https://www.naxely.com/robots.txt') -join "`n"

W '===== HOMEPAGE TITLE / META ====='
foreach ($m in [regex]::Matches($homeHtml, '(?s)<title>(.*?)</title>')) { W ("title: " + [System.Web.HttpUtility]::HtmlDecode($m.Groups[1].Value)) }
foreach ($m in [regex]::Matches($homeHtml, '<meta name="description" content="([^"]*)"')) { W ("meta desc: " + [System.Web.HttpUtility]::HtmlDecode($m.Groups[1].Value)) }
W ''
W '===== ORGANIZATION JSON-LD (homepage) ====='
foreach ($m in [regex]::Matches($homeHtml, '(?s)<script type="application/ld\+json">(.*?)</script>')) {
  $j = $m.Groups[1].Value
  if ($j -match '"Organization"') { W $j }
}
W ''
W '===== /about H1 + first paragraphs ====='
$h1m = [regex]::Match($about, '(?s)<h1[^>]*>(.*?)</h1>')
if ($h1m.Success) { W ("about H1: " + [System.Web.HttpUtility]::HtmlDecode((($h1m.Groups[1].Value -replace '<[^>]+>','' -replace '\s+',' ').Trim()))) }
$c = 0
foreach ($m in [regex]::Matches($about, '(?s)<p[^>]*>(.*?)</p>')) {
  $t = [System.Web.HttpUtility]::HtmlDecode((($m.Groups[1].Value -replace '<[^>]+>','' -replace '\s+',' ').Trim()))
  if (($t -split ' ').Count -ge 12) { W ("about p: " + $t.Substring(0, [Math]::Min(300, $t.Length))); $c++; if ($c -ge 2) { break } }
}
W ''
W '===== FOOTER one-liner ====='
$fx = $homeHtml.LastIndexOf('<footer')
$footer = $homeHtml.Substring($fx, [Math]::Min(3000, $homeHtml.Length - $fx))
$ft = [System.Web.HttpUtility]::HtmlDecode(($footer -replace '(?s)<script.*?</script>',' ' -replace '<[^>]+>',' ' -replace '\s+',' ').Trim())
W $ft.Substring(0, [Math]::Min(400, $ft.Length))
W ''
W '===== llms.txt (full) ====='
W $llms
W ''
W '===== robots.txt (full) ====='
W $robots
W ''
W '===== sameAs status checks ====='
foreach ($m in [regex]::Matches($homeHtml, '"sameAs":\s*\[(.*?)\]')) {
  $urls = [regex]::Matches($m.Groups[1].Value, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
  foreach ($u in $urls) {
    $code = curl.exe -s -o NUL -w "%{http_code}" -L --max-time 25 $u
    W "$code  $u"
  }
}
$out | Set-Content -LiteralPath "$rawDir\entity_check.txt" -Encoding UTF8
Write-Output "WROTE $rawDir\entity_check.txt"

