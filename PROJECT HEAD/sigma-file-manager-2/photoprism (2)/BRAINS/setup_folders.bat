@echo off
::
:: Batch file to set up the necessary folders for Sorting Hat
::

echo Setting up folders for Sorting Hat...

:: Create main folders
if not exist "C:\Users\casey\OrganizeFolder" (
    echo Creating main organize folder
    mkdir "C:\Users\casey\OrganizeFolder"
) else (
    echo Main organize folder already exists
)

:: Create category folders
if not exist "C:\Users\casey\OrganizeFolder\Legal" mkdir "C:\Users\casey\OrganizeFolder\Legal"
if not exist "C:\Users\casey\OrganizeFolder\Financial" mkdir "C:\Users\casey\OrganizeFolder\Financial"
if not exist "C:\Users\casey\OrganizeFolder\Real Estate" mkdir "C:\Users\casey\OrganizeFolder\Real Estate"
if not exist "C:\Users\casey\OrganizeFolder\Family" mkdir "C:\Users\casey\OrganizeFolder\Family"
if not exist "C:\Users\casey\OrganizeFolder\Business" mkdir "C:\Users\casey\OrganizeFolder\Business"
if not exist "C:\Users\casey\OrganizeFolder\Education" mkdir "C:\Users\casey\OrganizeFolder\Education"
if not exist "C:\Users\casey\OrganizeFolder\Creativity" mkdir "C:\Users\casey\OrganizeFolder\Creativity"
if not exist "C:\Users\casey\OrganizeFolder\Technology" mkdir "C:\Users\casey\OrganizeFolder\Technology"
if not exist "C:\Users\casey\OrganizeFolder\Miscellaneous" mkdir "C:\Users\casey\OrganizeFolder\Miscellaneous"

echo.
echo All required folders have been verified or created.
echo Sorting Hat is ready to organize files.
