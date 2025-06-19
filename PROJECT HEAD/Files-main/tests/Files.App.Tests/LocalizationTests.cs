using Files.App.Services;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Globalization;
using Windows.ApplicationModel.Resources.Core;

namespace Files.App.Tests
{
    [TestClass]
    public class LocalizationTests
    {
        private LocalizationService _localizationService;
        private string _originalLanguage;

        [TestInitialize]
        public void Initialize()
        {
            _localizationService = new LocalizationService();
            
            // Save the original language to restore later
            _originalLanguage = Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride;
        }

        [TestCleanup]
        public void Cleanup()
        {
            // Restore the original language
            Windows.Globalization.ApplicationLanguages.PrimaryLanguageOverride = _originalLanguage;
        }

        [TestMethod]
        public void GetLocalizedString_WithExistingKey_ReturnsLocalizedString()
        {
            // Arrange
            const string testKey = "AppDisplayName";
            const string expectedValue = "Files";
            
            // Act
            var result = _localizationService.GetLocalizedString(testKey);
            
            // Assert
            Assert.AreEqual(expectedValue, result, "Localized string did not match expected value");
        }

        [TestMethod]
        public void GetLocalizedString_WithNonExistentKey_ReturnsKeyWithMarkers()
        {
            // Arrange
            const string nonExistentKey = "NonExistentKey123";
            
            // Act
            var result = _localizationService.GetLocalizedString(nonExistentKey);
            
            // Assert
            StringAssert.StartsWith(result, "!");
            StringAssert.EndsWith(result, "!");
            StringAssert.Contains(result, nonExistentKey);
        }

        [TestMethod]
        public void SetLanguage_WithValidLanguage_ChangesCulture()
        {
            // Arrange
            var testCulture = new CultureInfo("es-ES");
            
            // Act
            _localizationService.SetLanguage("es-ES");
            
            // Assert
            Assert.AreEqual(testCulture.Name, CultureInfo.CurrentUICulture.Name, "UI culture was not set correctly");
            Assert.AreEqual(testCulture.Name, CultureInfo.CurrentCulture.Name, "Culture was not set correctly");
        }

        [TestMethod]
        public void SetLanguage_WithInvalidLanguage_DoesNotThrow()
        {
            // Arrange
            var originalCulture = CultureInfo.CurrentUICulture;
            
            // Act & Assert (should not throw)
            try 
            {
                _localizationService.SetLanguage("invalid-language-code");
            }
            finally
            {
                // Cleanup
                CultureInfo.CurrentUICulture = originalCulture;
            }
        }

        [TestMethod]
        public void ExtensionMethod_GetLocalized_ReturnsSameAsService()
        {
            // Arrange
            const string testKey = "AppDisplayName";
            var expected = _localizationService.GetLocalizedString(testKey);
            
            // Act
            var result = testKey.GetLocalized();
            
            // Assert
            Assert.AreEqual(expected, result, "Extension method should return same as service method");
        }
    }
}
