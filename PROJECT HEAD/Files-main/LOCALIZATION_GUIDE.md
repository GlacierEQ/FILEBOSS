# Localization Guide for Files Application

This guide explains how to use and extend the localization system in the Files application.

## Overview

The Files application uses a resource-based localization system that supports multiple languages. The system is built on top of the Windows resource management system and provides an easy-to-use API for accessing localized strings.

## Adding New Strings

1. **Resource Files**:
   - String resources are stored in `.resw` files in the `Resources/Strings/{language-code}` directories.
   - The default language is English (en-US).

2. **Adding a New String**:
   - Open the appropriate `.resw` file for your language
   - Add a new entry with a unique key and the translated text
   - Example key: `SettingsPage_Theme_Description`

## Using Localized Strings in Code

### Basic Usage

```csharp
// Get a localized string
var localizedString = App.LocalizationService.GetLocalizedString("StringKey");

// Using the extension method
var alsoLocalized = "StringKey".GetLocalized();
```

### In XAML

```xml
<TextBlock Text="{x:Bind ('StringKey'.GetLocalized()), Mode=OneWay}" />
```

## Adding Support for a New Language

1. Create a new directory under `Resources/Strings/` with the language code (e.g., `es-ES` for Spanish)
2. Copy the `Resources.resw` file from the `en-US` directory
3. Translate all the strings in the new file
4. Update the `AppDefaultResourceLanguage` in the project file if needed

## Best Practices

1. **String Keys**:
   - Use descriptive, hierarchical names (e.g., `SettingsPage_Theme_Label`)
   - Keep keys consistent across language files

2. **Parameters**:
   - Use `{0}`, `{1}`, etc. for dynamic content
   - Example: `"WelcomeMessage_Text": "Welcome, {0}!"`

3. **Pluralization**:
   - Handle plurals with separate keys or parameters
   - Example: `"ItemCount_Single"` and `"ItemCount_Multiple"`

4. **Accessibility**:
   - Include accessibility information in the resource comments
   - Use complete sentences for screen readers

## Testing Localization

1. Set the application language in Windows Settings
2. Or use the `ApplicationLanguages.PrimaryLanguageOverride` API for testing
3. Test with right-to-left (RTL) languages like Arabic or Hebrew

## Implementation Details

The localization system is implemented in `LocalizationService.cs` and provides:

- Thread-safe string lookups
- Fallback to default language
- Support for runtime language changes
- Extension methods for XAML binding

## Troubleshooting

- **Missing Strings**: Check that the key exists in the resource file
- **Wrong Language**: Verify Windows language settings
- **Format Errors**: Check string format placeholders (e.g., `{0}`, `{1}`)

## Example: Adding a New Localized String

1. Add to `Resources/Strings/en-US/Resources.resw`:
   ```xml
   <data name="MyNewString" xml:space="preserve">
     <value>This is my new string</value>
   </data>
   ```

2. Use in code:
   ```csharp
   var myString = "MyNewString".GetLocalized();
   ```

3. Use in XAML:
   ```xml
   <TextBlock Text="{x:Bind ('MyNewString'.GetLocalized()), Mode=OneWay}" />
   ```
