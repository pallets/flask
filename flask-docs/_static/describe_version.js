/**
 * Match a PEP 440 version string. The full regex given in PEP 440 is not used.
 * This subset covers what we expect to encounter in our projects.
 */
const versionRe = new RegExp([
  "^",
  "(?:(?<epoch>[1-9][0-9]*)!)?",
  "(?<version>(?:0|[1-9][0-9]*)(?:\\.(?:0|[1-9][0-9]*))*)",
  "(?:(?<preL>a|b|rc)(?<preN>0|[1-9][0-9]*))?",
  "(?:\\.post(?<postN>0|[1-9][0-9]*))?",
  "(?:\\.dev(?<devN>0|[1-9][0-9]*))?",
  "$",
].join(""))

/**
 * Parse a PEP 440 version string into an object.
 *
 * @param {string} value
 * @returns {Object} parsed version information
 */
function parseVersion(value) {
  let {groups: {epoch, version, preL, preN, postN, devN}} = versionRe.exec(value)
  return {
    value: value,
    parts:  [
      parseInt(epoch) || 0, ...version.split(".").map(p => parseInt(p))
    ],
    isPre: Boolean(preL),
    preL: preL || "",
    preN: parseInt(preN) || 0,
    isPost: Boolean(postN),
    postN: parseInt(postN) || 0,
    isDev: Boolean(devN),
    devN: parseInt(devN) || 0,
  }
}

/**
 * Compare two version objects.
 *
 * @param {Object} a left side of comparison
 * @param {Object} b right side of comparison
 * @returns {number} -1 less than, 0 equal to, 1 greater than
 */
function compareVersions(a, b) {
  for (let [i, an] of a.parts.entries()) {
    let bn = i < b.parts.length ? b.parts[i] : 0

    if (an < bn) {
      return -1
    } else if (an > bn) {
      return 1
    }
  }

  if (a.parts.length < b.parts.length) {
    return -1
  }

  return 0
}

/**
 * Get the list of released versions for the project from PyPI. Prerelease and
 * development versions are discarded. The list is sorted in descending order,
 * highest version first.
 *
 * This will be called on every page load. To avoid making excessive requests to
 * PyPI, the result is cached for 1 day. PyPI also sends cache headers, so a
 * subsequent request may still be more efficient, but it only specifies caching
 * the full response for 5 minutes.
 *
 * @param {string} name The normalized PyPI project name to query.
 * @returns {Promise<Object[]>} A sorted list of version objects.
 */
async function getReleasedVersions(name) {
  // The response from PyPI is only cached for 5 minutes. Extend that to 1 day.
  let cacheTime = localStorage.getItem("describeVersion-time")
  let cacheResult = localStorage.getItem("describeVersion-result")

  // if there is a cached value
  if (cacheTime && cacheResult) {
    // if the cache is younger than 1 day
    if (Number(cacheTime) >= Date.now() - 86400000) {
      // Use the cached value instead of making another request.
      return JSON.parse(cacheResult)
    }
  }

  let response = await fetch(
    `https://pypi.org/simple/${name}/`,
    {"headers": {"Accept": "application/vnd.pypi.simple.v1+json"}}
  )
  let data = await response.json()
  let result = data["versions"]
    .map(parseVersion)
    .filter(v => !(v.isPre || v.isDev))
    .sort(compareVersions)
    .reverse()
  localStorage.setItem("describeVersion-time", Date.now().toString())
  localStorage.setItem("describeVersion-result", JSON.stringify(result))
  return result
}

/**
 * Get the highest released version of the project from PyPI, and compare the
 * version being documented. Returns a list of two values, the comparison
 * result and the highest version.
 *
 * @param name The normalized PyPI project name.
 * @param value The version being documented.
 * @returns {Promise<[number, Object|null]>}
 */
async function describeVersion(name, value) {
  if (value.endsWith(".x")) {
    value = value.slice(0, -2)
  }

  let currentVersion = parseVersion(value)
  let releasedVersions = await getReleasedVersions(name)

  if (releasedVersions.length === 0) {
    return [1, null]
  }

  let highestVersion = releasedVersions[0]
  let compared = compareVersions(currentVersion, highestVersion)

  if (compared === 1) {
    return [1, highestVersion]
  }

  // If the current version including trailing zeros is a prefix of the highest
  // version, then these are the stable docs. For example, 2.0.x becomes 2.0,
  // which is a prefix of 2.0.3. If we were just looking at the compare result,
  // it would incorrectly be marked as an old version.
  if (currentVersion.parts.every((n, i) => n === highestVersion.parts[i])) {
    return [0, highestVersion]
  }

  return [-1, highestVersion]
}

/**
 * Compare the version being documented to the highest released version, and
 * display a warning banner if it is not the highest version.
 *
 * @param project The normalized PyPI project name.
 * @param version The version being documented.
 * @returns {Promise<void>}
 */
async function createBanner(project, version) {
  let [compared, stable] = await describeVersion(project, version)

  // No banner if this is the highest version or there are no other versions.
  if (compared === 0 || stable === null) {
    return
  }

  let banner = document.createElement("p")
  banner.className = "version-warning"

  if (compared === 1) {
    banner.textContent = "This is the development version. The stable version is "
  } else if (compared === -1) {
    banner.textContent = "This is an old version. The current version is "
  }

  let canonical = document.querySelector('link[rel="canonical"]')

  if (canonical !== null) {
    // If a canonical URL is available, the version is a link to it.
    let link = document.createElement("a")
    link.href = canonical.href
    link.textContent = stable.value
    banner.append(link, ".")
  } else {
    // Otherwise, the version is text only.
    banner.append(stable.value, ".")
  }

  document.getElementsByClassName("document")[0].prepend(banner)
  // Set scroll-padding-top to prevent the banner from overlapping anchors.
  // It's also set in CSS assuming the banner text is only 1 line.
  let bannerStyle = window.getComputedStyle(banner)
  let bannerMarginTop = parseFloat(bannerStyle["margin-top"])
  let bannerMarginBottom = parseFloat(bannerStyle["margin-bottom"])
  let height = banner.offsetHeight + bannerMarginTop + bannerMarginBottom
  document.documentElement.style["scroll-padding-top"] = `${height}px`
}

(() => {
  // currentScript is only available during init, not during callbacks.
  let {project, version} = document.currentScript.dataset
  document.addEventListener("DOMContentLoaded", async () => {
    await createBanner(project, version)
  })
})()
