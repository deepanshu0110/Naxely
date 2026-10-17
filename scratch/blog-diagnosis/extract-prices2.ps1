$dir = 'scratch/blog-diagnosis/raw/articles'

# 1) Byte-level scan for standalone EUR/GBP signs (UTF-8: E2 82 AC / C2 A3)
Write-Output '===== standalone EUR/GBP scan ====='
foreach ($f in Get-ChildItem $dir -Filter *.txt | Sort-Object Name) {
  $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
  $euro = 0; $gbp = 0
  for ($i = 0; $i -le $bytes.Length - 3; $i++) {
    if ($bytes[$i] -eq 0xE2 -and $bytes[$i+1] -eq 0x82 -and $bytes[$i+2] -eq 0xAC) { $euro++ }
  }
  for ($i = 0; $i -le $bytes.Length - 2; $i++) {
    if ($bytes[$i] -eq 0xC2 -and $bytes[$i+1] -eq 0xA3) { $gbp++ }
  }
  if ($euro -gt 0 -or $gbp -gt 0) { Write-Output "$($f.BaseName): euro=$euro gbp=$gbp" }
}

# 2) Full sentences containing vendor names or $ amounts
$vendors = @('Whatagraph','AgencyAnalytics','DashThis','Databox','Swydo','Klipfolio','Looker','Reportz','Supermetrics')
$results = @()
foreach ($f in Get-ChildItem $dir -Filter *.txt | Sort-Object Name) {
  $slug = $f.BaseName
  $t = (Get-Content $f.FullName -Raw) -replace '\s+', ' '
  $seen = @{}
  $terms = @($vendors) + @('$')
  foreach ($term in $terms) {
    $pattern = '(?i)[^.?!]*(' + [regex]::Escape($term) + ')[^.?!]*[.?!]'
    foreach ($m in [regex]::Matches($t, $pattern)) {
      $s = $m.Value.Trim()
      if ($s.Length -eq 0) { continue }
      $key = $s.Substring(0, [Math]::Min(80, $s.Length))
      if ($seen.ContainsKey($key)) { continue }
      $seen[$key] = $true
      $results += [ordered]@{ post = $slug; term = $term; sentence = $s }
    }
  }
}
Write-Output ''
Write-Output '===== full sentences =====' 
foreach ($r in $results) {
  Write-Output "[$($r.post)] term=$($r.term)"
  Write-Output "  $($r.sentence)"
}
