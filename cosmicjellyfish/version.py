_MAJOR = "2"
_MINOR = "0"
# On main and in a nightly release the patch should be one ahead of the last
# released build.
_PATCH = "0"
# Pre-releases use PEP 440 suffixes such as "rc1"; nightly builds use
# ".dev$DATE". See https://semver.org/#is-v123-a-semantic-version for the
# semantics. Leave empty for a final release.
_SUFFIX = "rc2"

VERSION_SHORT = "{0}.{1}".format(_MAJOR, _MINOR)
VERSION = "{0}.{1}.{2}{3}".format(_MAJOR, _MINOR, _PATCH, _SUFFIX)
