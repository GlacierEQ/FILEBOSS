using System;
using System.Threading.Tasks;
using Files.App.Plugins.Interfaces;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace Files.App.Plugins.SamplePlugin
{
    public class SamplePlugin : IUIPlugin
    {
        private IPluginContext _context;
        private Button _button;
        private bool _isInitialized;

        public string Id => "com.files.plugins.sample";
        public string Name => "Sample Plugin";
        public string Description => "A sample plugin demonstrating the plugin system";
        public Version Version => new Version(1, 0, 0);
        public string Author => "Files Team";

        public async Task InitializeAsync(IPluginContext context)
        {
            if (_isInitialized)
                return;

            _context = context ?? throw new ArgumentNullException(nameof(context));
            
            // Initialize UI components
            _button = new Button
            {
                Content = "Click me!",
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 10, 0, 0)
            };

            _button.Click += Button_Click;
            _isInitialized = true;
            
            await Task.CompletedTask;
        }

        public async Task UnloadAsync()
        {
            if (!_isInitialized)
                return;

            _button.Click -= Button_Click;
            _button = null;
            _context = null;
            _isInitialized = false;
            
            await Task.CompletedTask;
        }

        public Control GetControl()
        {
            if (!_isInitialized)
                throw new InvalidOperationException("Plugin not initialized");

            return _button;
        }

        private void Button_Click(object sender, RoutedEventArgs e)
        {
            // Example of using the localization service
            var messageDialog = new ContentDialog
            {
                Title = "Sample Plugin",
                Content = "Hello from the sample plugin!",
                CloseButtonText = "OK",
                XamlRoot = _context.MainWindow.Content.XamlRoot
            };

            _ = messageDialog.ShowAsync();
        }

        public void Dispose()
        {
            if (_isInitialized)
            {
                UnloadAsync().ConfigureAwait(false).GetAwaiter().GetResult();
            }
        }
    }
}
