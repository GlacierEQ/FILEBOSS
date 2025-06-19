# Files App Plugin System

This document provides information about developing plugins for the Files application.

## Overview

The Files application supports a plugin system that allows developers to extend its functionality. Plugins can add new features, modify existing behavior, or integrate with external services.

## Creating a Plugin

### Prerequisites

- .NET 6.0 or later
- Visual Studio 2022 or later (with .NET desktop development workload)
- Basic knowledge of C# and XAML

### Plugin Structure

A basic plugin has the following structure:

```
MyPlugin/
├── MyPlugin.csproj
├── MyPlugin.cs
└── Properties/
    └── AssemblyInfo.cs
```

### Plugin Project File

Your plugin project file should target `net6.0-windows` and include references to the necessary Files.App assemblies:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0-windows10.0.19041.0</TargetFramework>
    <TargetPlatformMinVersion>10.0.17763.0</TargetPlatformMinVersion>
    <RootNamespace>MyPlugin</RootNamespace>
    <AssemblyName>MyPlugin</AssemblyName>
    <OutputType>Library</OutputType>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.WindowsAppSDK" Version="1.4.0" />
    <PackageReference Include="Microsoft.Windows.SDK.BuildTools" Version="10.0.22621.756" />
  </ItemGroup>
</Project>
```

### Implementing a Basic Plugin

Create a class that implements `IPlugin` or `IUIPlugin`:

```csharp
using Files.App.Plugins.Interfaces;
using Microsoft.UI.Xaml.Controls;

namespace MyPlugin
{
    public class MyPlugin : IUIPlugin
    {
        public string Id => "com.example.myplugin";
        public string Name => "My Plugin";
        public string Description => "A sample plugin for Files";
        public string Author => "Your Name";
        public Version Version => new Version(1, 0, 0);

        private IPluginContext _context;
        private Button _button;

        public async Task InitializeAsync(IPluginContext context)
        {
            _context = context;
            _button = new Button { Content = "Click me!" };
            _button.Click += (s, e) => ShowMessage();
        }

        public Control GetControl() => _button;

        public async Task UnloadAsync()
        {
            // Clean up resources
            _button = null;
            _context = null;
        }

        public void Dispose()
        {
            UnloadAsync().ConfigureAwait(false).GetAwaiter().GetResult();
        }

        private void ShowMessage()
        {
            // Show a message using the application's UI
            var dialog = new ContentDialog
            {
                Title = "My Plugin",
                Content = "Hello from My Plugin!",
                CloseButtonText = "OK"
            };
            
            // Use the main window's XAML root
            if (_context?.MainWindow is Microsoft.UI.Xaml.Window window)
            {
                dialog.XamlRoot = window.Content.XamlRoot;
                _ = dialog.ShowAsync();
            }
        }
    }
}
```

## Localization

Plugins can use the application's localization system:

```csharp
// In your plugin code
var localizedString = Files.App.App.LocalizationService.GetLocalizedString("MyStringKey");
```

To add localized strings, create a `Resources.resw` file in your plugin project and add string resources with appropriate keys.

## Plugin Lifecycle

1. **Loading**: The plugin is loaded when the application starts
2. **Initialization**: `InitializeAsync` is called with a plugin context
3. **Execution**: The plugin performs its functions
4. **Unloading**: `UnloadAsync` is called when the plugin is being unloaded
5. **Disposal**: The plugin is disposed of when the application shuts down

## Best Practices

1. **Error Handling**: Always implement proper error handling in your plugin
2. **Resource Management**: Clean up resources in `UnloadAsync` and `Dispose`
3. **Thread Safety**: Ensure thread safety when accessing UI elements
4. **Performance**: Keep plugin initialization fast and efficient
5. **Compatibility**: Test your plugin with different versions of Files

## Debugging

To debug your plugin:

1. Set your plugin project as the startup project
2. In project properties, set the following debug settings:
   - Start action: Start external program
   - Command: `path\to\Files.App.exe`
   - Working directory: `path\to\Files.App`

## Distribution

Package your plugin as a .dll file and place it in the `Plugins` directory in the application's data folder:

```
%LOCALAPPDATA%\Files\Plugins\
```

## Example Plugins

See the `SamplePlugin` in the `Plugins` directory for a complete example.

## License

Your plugin should include a license file. The Files application is licensed under the MIT License.
