const themeFlyoutDisplay = "hidden";
const themeVersionSelector = true;
const themeLanguageSelector = true;

if (themeFlyoutDisplay === "attached") {
  function renderLanguages(config) {
    if (!config.projects.translations.length) {
      return "";
    }

    // Insert the current language to the options on the selector
    let languages = config.projects.translations.concat(config.projects.current);
    languages = languages.sort((a, b) => a.language.name.localeCompare(b.language.name));

    const languagesHTML = `
      <dl>
        <dt>Languages</dt>
        ${languages
          .map(
            (translation) => `
        <dd ${translation.slug == config.projects.current.slug ? 'class="rtd-current-item"' : ""}>
          <a href="${translation.urls.documentation}">${translation.language.code}</a>
        </dd>
        `,
          )
          .join("\n")}
      </dl>
    `;
    return languagesHTML;
  }

  function renderVersions(config) {
    if (!config.versions.active.length) {
      return "";
    }
    const versionsHTML = `
      <dl>
        <dt>Versions</dt>
        ${config.versions.active
          .map(
            (version) => `
        <dd ${version.slug === config.versions.current.slug ? 'class="rtd-current-item"' : ""}>
          <a href="${version.urls.documentation}">${version.slug}</a>
        </dd>
        `,
          )
          .join("\n")}
      </dl>
    `;
    return versionsHTML;
  }

  function renderDownloads(config) {
    if (!Object.keys(config.versions.current.downloads).length) {
      return "";
    }
    const downloadsNameDisplay = {
      pdf: "PDF",
      epub: "Epub",
      htmlzip: "HTML",
    };

    const downloadsHTML = `
      <dl>
        <dt>Downloads</dt>
        ${Object.entries(config.versions.current.downloads)
          .map(
            ([name, url]) => `
          <dd>
            <a href="${url}">${downloadsNameDisplay[name]}</a>
          </dd>
        `,
          )
          .join("\n")}
      </dl>
    `;
    return downloadsHTML;
  }

  document.addEventListener("readthedocs-addons-data-ready", function (event) {
    const config = event.detail.data();

    const flyout = `
      <div class="rst-versions" data-toggle="rst-versions" role="note">
        <span class="rst-current-version" data-toggle="rst-current-version">
          <span class="fa fa-book"> Read the Docs</span>
          v: ${config.versions.current.slug}
          <span class="fa fa-caret-down"></span>
        </span>
        <div class="rst-other-versions">
          <div class="injected">
            ${renderLanguages(config)}
            ${renderVersions(config)}
            ${renderDownloads(config)}
            <dl>
              <dt>On Read the Docs</dt>
              <dd>
                <a href="${config.projects.current.urls.home}">Project Home</a>
              </dd>
              <dd>
                <a href="${config.projects.current.urls.builds}">Builds</a>
              </dd>
              <dd>
                <a href="${config.projects.current.urls.downloads}">Downloads</a>
              </dd>
            </dl>
            <dl>
              <dt>Search</dt>
              <dd>
                <form id="flyout-search-form">
                  <input
                    class="wy-form"
                    type="text"
                    name="q"
                    aria-label="Search docs"
                    placeholder="Search docs"
                    />
                </form>
              </dd>
            </dl>
            <hr />
            <small>
              <span>Hosted by <a href="https://about.readthedocs.org/?utm_source=&utm_content=flyout">Read the Docs</a></span>
            </small>
          </div>
        </div>
    `;

    // Inject the generated flyout into the body HTML element.
    document.body.insertAdjacentHTML("beforeend", flyout);

    // Trigger the Read the Docs Addons Search modal when clicking on the "Search docs" input from inside the flyout.
    document
      .querySelector("#flyout-search-form")
      .addEventListener("focusin", () => {
        const event = new CustomEvent("readthedocs-search-show");
        document.dispatchEvent(event);
      });
  })
}

if (themeLanguageSelector || themeVersionSelector) {
  function onSelectorSwitch(event) {
    const option = event.target.selectedIndex;
    const item = event.target.options[option];
    window.location.href = item.dataset.url;
  }

  document.addEventListener("readthedocs-addons-data-ready", function (event) {
    const config = event.detail.data();

    const versionSwitch = document.querySelector(
      "div.switch-menus > div.version-switch",
    );
    if (themeVersionSelector) {
      let versions = config.versions.active;
      if (config.versions.current.hidden || config.versions.current.type === "external") {
        versions.unshift(config.versions.current);
      }
      const versionSelect = `
    <select>
      ${versions
        .map(
          (version) => `
        <option
  value="${version.slug}"
  ${config.versions.current.slug === version.slug ? 'selected="selected"' : ""}
              data-url="${version.urls.documentation}">
              ${version.slug}
          </option>`,
        )
        .join("\n")}
    </select>
  `;

      versionSwitch.innerHTML = versionSelect;
      versionSwitch.firstElementChild.addEventListener("change", onSelectorSwitch);
    }

    const languageSwitch = document.querySelector(
      "div.switch-menus > div.language-switch",
    );

    if (themeLanguageSelector) {
      if (config.projects.translations.length) {
        // Add the current language to the options on the selector
        let languages = config.projects.translations.concat(
          config.projects.current,
        );
        languages = languages.sort((a, b) =>
          a.language.name.localeCompare(b.language.name),
        );

        const languageSelect = `
      <select>
        ${languages
          .map(
            (language) => `
              <option
                  value="${language.language.code}"
                  ${config.projects.current.slug === language.slug ? 'selected="selected"' : ""}
                  data-url="${language.urls.documentation}">
                  ${language.language.name}
              </option>`,
          )
          .join("\n")}
       </select>
    `;

        languageSwitch.innerHTML = languageSelect;
        languageSwitch.firstElementChild.addEventListener("change", onSelectorSwitch);
      }
      else {
        languageSwitch.remove();
      }
    }
  });
}

document.addEventListener("readthedocs-addons-data-ready", function (event) {
  // Trigger the Read the Docs Addons Search modal when clicking on "Search docs" input from the topnav.
  document
    .querySelector("[role='search'] input")
    .addEventListener("focusin", () => {
      const event = new CustomEvent("readthedocs-search-show");
      document.dispatchEvent(event);
    });
});