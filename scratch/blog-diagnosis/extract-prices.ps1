$dir = 'scratch/blog-diagnosis/raw/articles'
$vendors = @('Whatagraph','AgencyAnalytics','DashThis','Databox','Swydo','Klipfolio','Looker','Reportz','Supermetrics')
$results = @()
foreach ($f in Get-ChildItem $dir -Filter *.txt | Sort-Object Name) {
  $slug = $f.BaseName
  $t = (Get-Content $f.FullName -Raw) -replace '\s+', ' '
  $seen = @{}
  $capture = @($vendors) + @('€','$','£')
  foreach ($term in $capture) {
    $pattern = '(?i)[^.]{0,150}' + [regex]::Escape($term) + '[^.]{0,150}\.'
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
foreach ($r in $results) {
  Write-Output "[$($r.post)] term=$($r.term)"
  Write-Output "  $($r.sentence)"
}
if ($results.Count -eq 0) { Write-Output '(no matches anywhere)' }
