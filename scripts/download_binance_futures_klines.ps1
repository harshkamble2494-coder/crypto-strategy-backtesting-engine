param(
    [string]$Symbol = "BTCUSDT",
    [string]$Interval = "1h",
    [double]$Years = 2.0,
    [string]$Output = "data/raw/BTCUSDT_1h.csv"
)

$BaseUrl = "https://fapi.binance.com/fapi/v1/klines"
$IntervalMs = 60 * 60 * 1000
$End = (Get-Date).ToUniversalTime()
$End = Get-Date -Date $End -Minute 0 -Second 0 -Millisecond 0
$Start = $End.AddDays(-365.25 * $Years)
$Epoch = [DateTimeOffset]"1970-01-01T00:00:00Z"
$Cursor = [int64](([DateTimeOffset]$Start).ToUnixTimeMilliseconds())
$EndMs = [int64](([DateTimeOffset]$End).ToUnixTimeMilliseconds())

$Rows = New-Object System.Collections.Generic.List[object]

while ($Cursor -lt $EndMs) {
    $Uri = "{0}?symbol={1}&interval={2}&startTime={3}&endTime={4}&limit=1000" -f $BaseUrl, $Symbol, $Interval, $Cursor, $EndMs
    $Batch = Invoke-RestMethod -Uri $Uri -Method Get -TimeoutSec 30
    if ($null -eq $Batch -or $Batch.Count -eq 0) {
        break
    }

    foreach ($Kline in $Batch) {
        $OpenTime = [int64]$Kline[0]
        if ($OpenTime -gt $EndMs) {
            continue
        }
        $Timestamp = $Epoch.AddMilliseconds($OpenTime).UtcDateTime.ToString("o")
        $Rows.Add([pscustomobject]@{
            timestamp = $Timestamp
            open = [double]$Kline[1]
            high = [double]$Kline[2]
            low = [double]$Kline[3]
            close = [double]$Kline[4]
            volume = [double]$Kline[5]
        })
    }

    $NextCursor = [int64]$Batch[-1][0] + $IntervalMs
    if ($NextCursor -le $Cursor) {
        throw "Download cursor did not advance."
    }
    $Cursor = $NextCursor
    Start-Sleep -Milliseconds 150
}

$OutputPath = Resolve-Path -Path (Split-Path $Output -Parent) -ErrorAction SilentlyContinue
if ($null -eq $OutputPath) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Output -Parent) | Out-Null
}

if ($Rows.Count -lt 8760) {
    throw "Downloaded too few candles for a 2-year backtest: $($Rows.Count)"
}

$TempOutput = "$Output.tmp"
$Rows |
    Sort-Object timestamp -Unique |
    Export-Csv -Path $TempOutput -NoTypeInformation -Encoding UTF8
Move-Item -Path $TempOutput -Destination $Output -Force

Write-Host "Wrote $($Rows.Count) candles to $Output"
