using System;
using System.Globalization;
using Windows.ApplicationModel.Resources;
using Windows.ApplicationModel.Resources.Core;
using Windows.Globalization;

namespace Files.App.Services
{
    public interface ILocalizationService
    {
        string GetLocalizedString(string resourceKey);
        void SetLanguage(string languageCode);
        CultureInfo CurrentCulture { get; }
    }

    public class LocalizationService : ILocalizationService
    {
        private static LocalizationService _instance;
        public static LocalizationService Instance => _instance ??= new LocalizationService();

        private ResourceContext _resourceContext;
        private ResourceMap _resourceMap;

        public CultureInfo CurrentCulture => CultureInfo.CurrentCulture;

        private LocalizationService()
        {
            _resourceContext = ResourceContext.GetForViewIndependentUse();
            _resourceMap = ResourceManager.Current.MainResourceMap.GetSubtree("Files/Resources");
        }

        public string GetLocalizedString(string resourceKey)
        {
            try
            {
                var resourceCandidate = _resourceMap?.GetValue(resourceKey, _resourceContext);
                return resourceCandidate?.ValueAsString ?? $"!{resourceKey}!";
            }
            catch
            {
                return $"!{resourceKey}!";
            }
        }

        public void SetLanguage(string languageCode)
        {
            if (string.IsNullOrEmpty(languageCode))
                return;

            try
            {
                var culture = new CultureInfo(languageCode);
                CultureInfo.DefaultThreadCurrentCulture = culture;
                CultureInfo.DefaultThreadCurrentUICulture = culture;
                ApplicationLanguages.PrimaryLanguageOverride = languageCode;
                _resourceContext.Reset();
            }
            catch (CultureNotFoundException)
            {
                // Log error or handle unsupported culture
            }
        }
    }

    public static class LocalizationExtensions
    {
        public static string GetLocalized(this string resourceKey)
        {
            return LocalizationService.Instance.GetLocalizedString(resourceKey);
        }
    }
}
