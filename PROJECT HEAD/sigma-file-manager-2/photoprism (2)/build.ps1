# PhotoPrism Build Script for Windows
# Usage: .\build.ps1 [develop|race|static|debug|prod] [filename]

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("develop", "race", "static", "debug", "prod")]
    [string]$BuildType,
    
    [Parameter(Mandatory = $false)]
    [string]$FileName = "photoprism"
)

$BuildOS = "Windows"
$BuildArch = if ([Environment]::Is64BitOperatingSystem) { "AMD64" } else { "386" }
$BuildDate = Get-Date -UFormat "%y%m%d"
$BuildVersion = (git describe --always)
$BuildTag = "$BuildDate-$BuildVersion"
$BuildID = "$BuildTag-$BuildOS-$BuildArch"
$BuildBin = $FileName

Write-Host "Building PhotoPrism $BuildID ($BuildType)..."

# Check if Go is installed
try {
    $GoVer = (go version)
}
catch {
    Write-Host "Error: Go is not installed or not in the PATH." -ForegroundColor Red
    exit 1
}

# Build command based on type
if ($BuildType -eq "develop") {
    $BuildCmd = "go build -tags=`"debug,develop,brains`" -ldflags `"-X main.version=${BuildID}-DEVELOP`" -o `"${BuildBin}.exe`" cmd/photoprism/photoprism.go"
}
elseif ($BuildType -eq "race") {
    $BuildCmd = "go build -tags=`"debug,brains`" -race -ldflags `"-X main.version=${BuildID}-RACE`" -o `"${BuildBin}.exe`" cmd/photoprism/photoprism.go"
}
elseif ($BuildType -eq "static") {
    $BuildCmd = "go build -a -v -tags=`"static,brains`" -ldflags `"-s -w -X main.version=${BuildID}-STATIC`" -o `"${BuildBin}.exe`" cmd/photoprism/photoprism.go"
}
elseif ($BuildType -eq "debug") {
    $BuildCmd = "go build -tags=`"debug,brains`" -ldflags `"-s -w -X main.version=${BuildID}`" -o `"${BuildBin}-DEBUG.exe`" cmd/photoprism/photoprism.go"
}
else {
    $BuildCmd = "go build -tags=`"brains`" -ldflags `"-s -w -X main.version=${BuildID}`" -o `"${BuildBin}.exe`" cmd/photoprism/photoprism.go"
}

# Build app binary
Write-Host "=> compiling `"$BuildBin`" with `"$GoVer`""
Write-Host "=> $BuildCmd"
Invoke-Expression $BuildCmd

# Display binary size
Get-Item $BuildBin.exe | ForEach-Object { "$($_.length / 1MB) MB" }

Write-Host "Done."
