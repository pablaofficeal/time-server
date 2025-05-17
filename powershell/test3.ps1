if (Test-Connection -ComputerName google.com -Count 1 -Quiet) {
    Write-Output "There is internet :)"
} else {
    Write-Output "There is no internet :("
}
