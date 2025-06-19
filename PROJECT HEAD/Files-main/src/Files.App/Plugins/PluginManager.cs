using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Loader;
using System.Threading.Tasks;
using Files.App.Plugins.Interfaces;
using Microsoft.UI.Xaml;
using Windows.ApplicationModel;

namespace Files.App.Plugins
{
    public class PluginManager : IDisposable
    {
        private static PluginManager _instance;
        public static PluginManager Instance => _instance ??= new PluginManager();

        private readonly List<IPlugin> _loadedPlugins = new();
        private readonly List<AssemblyLoadContext> _pluginContexts = new();
        private IPluginContext _pluginContext;

        public IReadOnlyList<IPlugin> LoadedPlugins => _loadedPlugins.AsReadOnly();

        private PluginManager()
        {
            // Create the plugin directory if it doesn't exist
            var pluginDir = GetPluginDirectory();
            if (!Directory.Exists(pluginDir))
            {
                Directory.CreateDirectory(pluginDir);
            }
        }

        public void Initialize(IPluginContext context)
        {
            _pluginContext = context ?? throw new ArgumentNullException(nameof(context));
        }

        public async Task LoadPluginsAsync()
        {
            if (_pluginContext == null)
            {
                throw new InvalidOperationException("PluginManager must be initialized before loading plugins");
            }

            var pluginDir = GetPluginDirectory();
            var pluginFiles = Directory.GetFiles(pluginDir, "*.dll", SearchOption.AllDirectories);

            foreach (var pluginFile in pluginFiles)
            {
                try
                {
                    var context = new PluginLoadContext(pluginFile);
                    var assembly = context.LoadFromAssemblyPath(pluginFile);
                    
                    var pluginTypes = assembly.GetTypes()
                        .Where(t => typeof(IPlugin).IsAssignableFrom(t) && !t.IsInterface && !t.IsAbstract);

                    foreach (var type in pluginTypes)
                    {
                        try
                        {
                            if (Activator.CreateInstance(type) is IPlugin plugin)
                            {
                                await plugin.InitializeAsync(_pluginContext);
                                _loadedPlugins.Add(plugin);
                                _pluginContexts.Add(context);
                                context = null; // Don't unload this context as it's in use by the plugin
                                break;
                            }
                        }
                        catch (Exception ex)
                        {
                            // Log error
                            System.Diagnostics.Debug.WriteLine($"Failed to initialize plugin {type.FullName}: {ex.Message}");
                        }
                    }

                    // If we didn't use this context, unload it
                    context?.Unload();
                }
                catch (Exception ex)
                {
                    // Log error
                    System.Diagnostics.Debug.WriteLine($"Failed to load plugin {pluginFile}: {ex.Message}");
                }
            }
        }

        public async Task UnloadPluginsAsync()
        {
            foreach (var plugin in _loadedPlugins)
            {
                try
                {
                    await plugin.UnloadAsync();
                    if (plugin is IDisposable disposable)
                    {
                        disposable.Dispose();
                    }
                }
                catch (Exception ex)
                {
                    // Log error
                    System.Diagnostics.Debug.WriteLine($"Error unloading plugin {plugin.Name}: {ex.Message}");
                }
            }

            _loadedPlugins.Clear();

            // Unload all plugin contexts
            foreach (var context in _pluginContexts)
            {
                context.Unload();
            }
            _pluginContexts.Clear();
        }

        public T GetPlugin<T>() where T : class, IPlugin
        {
            return _loadedPlugins.OfType<T>().FirstOrDefault();
        }

        public IEnumerable<T> GetPlugins<T>() where T : class, IPlugin
        {
            return _loadedPlugins.OfType<T>();
        }

        public static string GetPluginDirectory()
        {
            var appData = ApplicationData.Current.LocalFolder.Path;
            return Path.Combine(appData, "Plugins");
        }

        public void Dispose()
        {
            UnloadPluginsAsync().ConfigureAwait(false).GetAwaiter().GetResult();
        }
    }

    internal class PluginLoadContext : AssemblyLoadContext
    {
        private readonly AssemblyDependencyResolver _resolver;

        public PluginLoadContext(string pluginPath)
        {
            _resolver = new AssemblyDependencyResolver(pluginPath);
        }

        protected override Assembly Load(AssemblyName assemblyName)
        {
            string assemblyPath = _resolver.ResolveAssemblyToPath(assemblyName);
            if (assemblyPath != null)
            {
                return LoadFromAssemblyPath(assemblyPath);
            }

            return null;
        }

        protected override IntPtr LoadUnmanagedDll(string unmanagedDllName)
        {
            string libraryPath = _resolver.ResolveUnmanagedDllToPath(unmanagedDllName);
            if (libraryPath != null)
            {
                return LoadUnmanagedDllFromPath(libraryPath);
            }

            return IntPtr.Zero;
        }
    }
}
