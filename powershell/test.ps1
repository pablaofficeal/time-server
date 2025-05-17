$usedPIDs = netstat -aon | Select-String 1356 | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Sort-Object -Unique

$usedPIDs | ForEach-Object {
    tasklist /FI "PID eq $_"
}
