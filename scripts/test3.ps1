$servers = @('fetch')
foreach ($name in $servers) {
    $config = @{
        command='npx'
        args = @('-y',"@modelcontextprotocol/server-$name")
        env = @{}
    } | ConvertTo-Json -Compress
    Write-Host $config
}
