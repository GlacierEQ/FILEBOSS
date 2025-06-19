# Breaking Changes

This document outlines the breaking changes introduced in the latest version of the application, particularly focusing on the new plugin system and localization features.

## Version 2.0.0

### Plugin System Changes

1. **New Plugin Architecture**
   - The entire plugin system has been redesigned for better isolation and security
   - Plugins now run in their own `AssemblyLoadContext`
   - New plugin interfaces have been introduced (`IPlugin`, `IUIPlugin`, `IPluginContext`)

2. **Required Updates for Existing Plugins**
   - Plugins must now implement the new `IPlugin` interface
   - The plugin manifest format has changed (see [Plugin Development Guide](PLUGINS_README.md))
   - Plugins must be recompiled against the new SDK

3. **API Changes**
   - Removed: `LegacyPluginManager` class
   - Removed: `IPluginHost` interface
   - Changed: Plugin initialization now uses `InitializeAsync` instead of `Load`

### Localization System Changes

1. **New Resource Management**
   - Switched from XAML resources to `.resw` files
   - New `LocalizationService` class for string lookups
   - Removed all hardcoded strings from the codebase

2. **Required Updates**
   - All UI strings must now use the localization system
   - XAML bindings must be updated to use the new resource format
   - Custom controls must implement `INotifyPropertyChanged` for dynamic language switching

3. **API Changes**
   - Removed: `LocalizedStrings` class
   - Removed: `StringResources` static class
   - Changed: `GetString` replaced with `GetLocalizedString` in `LocalizationService`

### Migration Guide

#### For Plugin Developers

1. Update your plugin project to target the new SDK
2. Implement the new `IPlugin` interface:
   ```csharp
   public class MyPlugin : IPlugin
   {
       public string Id => "your.plugin.id";
       public string Name => "My Plugin";
       public string Description => "Plugin description";
       public string Author => "Your Name";
       public Version Version => new Version(1, 0, 0);

       public Task InitializeAsync(IPluginContext context)
       {
           // Initialization code
           return Task.CompletedTask;
       }


       public Task UnloadAsync()
       {
           // Cleanup code
           return Task.CompletedTask;
       }

   }
   ```

3. Update your plugin manifest to the new format

#### For Application Developers

1. Update string references to use the new localization system:
   ```csharp
   // Old way
   var text = LocalizedStrings.GetString("MyString");
   
   // New way
   var text = App.LocalizationService.GetLocalizedString("MyString");
   // or using the extension method
   var text = "MyString".GetLocalized();
   ```

2. Update XAML bindings:
   ```xml
   <!-- Old way -->
   <TextBlock Text="{x:Bind LocalizedStrings.MyString}" />
   
   <!-- New way -->
   <TextBlock Text="{x:Bind ('MyString'.GetLocalized()), Mode=OneWay}" />
   ```

### Deprecated Features

The following features are deprecated and will be removed in a future version:

- `LegacyPluginManager` class
- `IPluginHost` interface
- `LocalizedStrings` class
- `StringResources` class
- Hardcoded strings in the codebase

### Known Issues

- Some third-party libraries may not be fully compatible with the new plugin system
- Performance may be impacted when loading many plugins
- Some edge cases in dynamic language switching may cause UI glitches

### Upgrade Instructions

1. Backup your existing project
2. Update all NuGet packages
3. Follow the migration guide above
4. Test thoroughly, especially plugin functionality and localization
5. Update your CI/CD pipelines to handle the new plugin format
