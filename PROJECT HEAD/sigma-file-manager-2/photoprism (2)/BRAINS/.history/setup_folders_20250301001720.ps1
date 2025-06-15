#
# PowerShell script to set up the necessary folders for Sorting Hat
#

# Define the folders to create
$folders = @(
    "C:\Users\casey\OrganizeFolder",
    "C:\Users\casey\OrganizeFolder\Legal",
    "C:\Users\casey\OrganizeFolder\Financial",
    "C:\Users\casey\OrganizeFolder\Real Estate",
    "C:\Users\casey\OrganizeFolder\Family",
    "C:\Users\casey\OrganizeFolder\Business",
    "C:\Users\casey\OrganizeFolder\Education",
    "C:\Users\casey\OrganizeFolder\Creativity",
    "C:\Users\casey\OrganizeFolder\Technology",
    "C:\Users\casey\OrganizeFolder\Miscellaneous"
)

# Create each folder if it doesn't exist
foreach ($folder in $folders) {
    if (-not (Test-Path -Path $folder)) {
        Write-Host "Creating folder: $folder"
        New-Item -ItemType Directory -Path $folder -Force
    } else {
        Write-Host "Folder already exists: $folder"
    }
}

Write-Host "`nAll required folders have been verified or created."
Write-Host "Sorting Hat is ready to organize files."
