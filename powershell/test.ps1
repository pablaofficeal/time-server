$usedPIDs = netstat -aon | Select-String 1356 | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Sort-Object -Unique

$usedPIDs | ForEach-Object {
    tasklist /FI "PID eq $_"
}
$usedPIDs | ForEach-Object {
    taskkill /F /PID $_
}
$Params = @{
    Parameter = Value
}
$Params.GetEnumerator() | ForEach-Object {
    taskkill /F /PID $_.Value
}