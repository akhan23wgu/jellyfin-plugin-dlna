using System;
using System.Collections.Generic;
using Jellyfin.Plugin.Dlna.Configuration;
using MediaBrowser.Common.Configuration;
using MediaBrowser.Common.Plugins;
using MediaBrowser.Model.Plugins;
using MediaBrowser.Model.Serialization;

namespace Jellyfin.Plugin.Dlna;

/// <summary>
/// DLNA plugin for Jellyfin.
/// </summary>
public class DlnaPlugin : BasePlugin<DlnaPluginConfiguration>, IHasWebPages
{
    /// <summary>
    /// Initializes a new instance of the <see cref="DlnaPlugin"/> class.
    /// </summary>
    /// <param name="applicationPaths">Instance of the <see cref="IApplicationPaths"/> interface.</param>
    /// <param name="xmlSerializer">Instance of the <see cref="IXmlSerializer"/> interface.</param>
    public DlnaPlugin(IApplicationPaths applicationPaths, IXmlSerializer xmlSerializer)
        : base(applicationPaths, xmlSerializer)
    {
        Instance = this;
    }

    /// <summary>
    /// Gets the <see cref="DlnaPlugin"/> instance.
    /// </summary>
    public static DlnaPlugin Instance { get; private set; } = null!;

    /// <inheritdoc />
    public override Guid Id => new("a1b27ca4-a2d4-4acd-bda9-d6f6ec42d815");

    /// <inheritdoc />
    public override string Name => "DLNA (Published URL)";

    /// <inheritdoc />
    public override string Description => "Use Jellyfin as a DLNA server.";

    /// <inheritdoc />
    public IEnumerable<PluginPageInfo> GetPages()
    {
        return
        [
            new PluginPageInfo
            {
                Name = "dlna",
                EmbeddedResourcePath = GetType().Namespace + ".Configuration.config.html",
                EnableInMainMenu = true
            },
            new PluginPageInfo
            {
                Name = "dlnajs",
                EmbeddedResourcePath = GetType().Namespace + ".Configuration.config.js"
            },
        ];
    }
}
