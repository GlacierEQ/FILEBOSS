using Files.App.Plugins;
using Files.App.Plugins.Interfaces;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Moq;
using System;
using System.Threading.Tasks;

namespace Files.App.Tests
{
    [TestClass]
    public class PluginTests
    {
        private PluginManager _pluginManager;
        private Mock<IPluginContext> _mockContext;

        [TestInitialize]
        public void Initialize()
        {
            _pluginManager = new PluginManager();
            _mockContext = new Mock<IPluginContext>();
            _pluginManager.Initialize(_mockContext.Object);
        }

        [TestMethod]
        public async Task LoadPlugins_WithValidPlugin_LoadsSuccessfully()
        {
            // Arrange - The SamplePlugin is in the test assembly
            
            // Act
            await _pluginManager.LoadPluginsAsync();
            
            // Assert
            Assert.IsTrue(_pluginManager.LoadedPlugins.Count > 0, "No plugins were loaded");
            
            var samplePlugin = _pluginManager.GetPlugin<SamplePlugin>();
            Assert.IsNotNull(samplePlugin, "SamplePlugin was not loaded");
            Assert.AreEqual("Sample Plugin", samplePlugin.Name);
        }

        [TestMethod]
        public async Task UnloadPlugins_WhenCalled_UnloadsAllPlugins()
        {
            // Arrange
            await _pluginManager.LoadPluginsAsync();
            Assert.IsTrue(_pluginManager.LoadedPlugins.Count > 0, "No plugins were loaded for test");

            // Act
            await _pluginManager.UnloadPluginsAsync();

            // Assert
            Assert.AreEqual(0, _pluginManager.LoadedPlugins.Count, "Not all plugins were unloaded");
        }

        
        [TestMethod]
        public void GetPlugin_WithNonExistentType_ReturnsNull()
        {
            // Act
            var result = _pluginManager.GetPlugin<INonExistentPlugin>();

            // Assert
            Assert.IsNull(result, "Should return null for non-existent plugin type");
        }
    }

    // Test plugin implementation
    public class SamplePlugin : IPlugin
    {
        public string Id => "test.plugin.sample";
        public string Name => "Sample Plugin";
        public string Description => "A test plugin";
        public Version Version => new(1, 0, 0);
        public string Author => "Test";

        public Task InitializeAsync(IPluginContext context) => Task.CompletedTask;
        public Task UnloadAsync() => Task.CompletedTask;
        public void Dispose() { }
    }

    // Used for testing non-existent plugin type
    public interface INonExistentPlugin : IPlugin { }
}
