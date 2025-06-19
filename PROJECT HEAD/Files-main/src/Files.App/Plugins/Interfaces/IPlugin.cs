using System;
using System.Threading.Tasks;
using Microsoft.UI.Xaml.Controls;

namespace Files.App.Plugins.Interfaces
{
    /// <summary>
    /// Base interface for all plugins
    /// </summary>
    public interface IPlugin : IDisposable
    {
        /// <summary>
        /// Unique identifier for the plugin
        /// </summary>
        string Id { get; }
        
        /// <summary>
        /// Display name of the plugin
        /// </summary>
        string Name { get; }
        
        /// <summary>
        /// Description of what the plugin does
        /// </summary>
        string Description { get; }
        
        /// <summary>
        /// Version of the plugin
        /// </summary>
        Version Version { get; }
        
        /// <summary>
        /// Author of the plugin
        /// </summary>
        string Author { get; }
        
        /// <summary>
        /// Initialize the plugin with the provided plugin context
        /// </summary>
        /// <param name="context">Plugin context providing access to application services</param>
        /// <returns>Task representing the initialization process</returns>
        Task InitializeAsync(IPluginContext context);
        
        /// <summary>
        /// Called when the plugin is being unloaded
        /// </summary>
        /// <returns>Task representing the unload process</returns>
        Task UnloadAsync();
    }
    
    /// <summary>
    /// Interface for plugins that provide UI elements
    /// </summary>
    public interface IUIPlugin : IPlugin
    {
        /// <summary>
        /// Gets the main control for the plugin UI
        /// </summary>
        /// <returns>Control representing the plugin's UI</returns>
        Control GetControl();
    }
    
    /// <summary>
    /// Context provided to plugins during initialization
    /// </summary>
    public interface IPluginContext
    {
        /// <summary>
        /// Gets a service of the specified type
        /// </summary>
        /// <typeparam name="T">Type of service to retrieve</typeparam>
        /// <returns>The service instance, or null if not found</returns>
        T GetService<T>() where T : class;
        
        /// <summary>
        /// Gets the application's main window
        /// </summary>
        object MainWindow { get; }
        
        /// <summary>
        /// Gets the application's dispatcher queue
        /// </summary>
        object DispatcherQueue { get; }
    }
}
