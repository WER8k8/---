Get-ScheduledTask -TaskPath '\YouDing\' | ForEach-Object {
    $info = Get-ScheduledTaskInfo $_
    [PSCustomObject]@{
        Name       = $_.TaskName
        State      = $_.State
        User       = $_.Principal.UserId
        RunLevel   = $_.Principal.RunLevel
        LogonType  = $_.Principal.LogonType
        LastResult = $info.LastTaskResult
        LastRun    = $info.LastRunTime
        NextRun    = $info.NextRunTime
    }
} | Format-Table -AutoSize
