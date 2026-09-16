"""Fetch the pack's data files on first use.

The statistics tables are tens of megabytes and are rebuilt on their own
schedule, so committing them would grow the repository by their full
size on every rebuild. They ship as GitHub release assets instead and
land in resources/ the first time a node needs one.

Each artifact is pinned by sha256: bump the release tag and the digest
together, never one alone, or an old cached copy will be accepted as the
new one.
"""
import os

try:
    from .utils import RESOURCES_DIR, get_logger
except ImportError:  # flat import (playground scripts put nodes/lib on sys.path)
    from utils import RESOURCES_DIR, get_logger

RELEASE = ("https://github.com/alchemine/comfyui-tags-generator"
           "/releases/download/%s/%s")


logger = get_logger()


def url_for(tag, filename):
    return RELEASE % (tag, filename)


def resource(*parts):
    """Path inside the pack's single resources/ directory."""
    return os.path.join(RESOURCES_DIR, *parts)


# Everything that is not a statistics table -- the label tables, the tag
# dump, the two editable lists -- travels as one archive rather than a
# file each: one digest to bump, one fetch, and the repository carries no
# data at all. The big tables stay separate, so a workflow that only
# groups tags never pulls the 100MB the sampler needs.
BUNDLE = "resources-v1.tar.gz"
BUNDLE_TAG = "data-v1.0.0"
BUNDLE_SHA256 = ("403a4513c7f22556fb41b300110fd171"
                 "f141dcc356bd88bcab6298723c75772d")


def bundled(*parts):
    """Path to a file from the resource archive, unpacking it if missing.

    Any one missing member pulls the whole archive, which is what makes
    a hand-edited solo_conflict.txt safe: the file is already there, so
    nothing is fetched and nothing overwrites it.
    """
    path = resource(*parts)
    if os.path.exists(path):
        return path

    import tarfile

    archive = ensure(resource(BUNDLE), url_for(BUNDLE_TAG, BUNDLE),
                     BUNDLE_SHA256, "resources", "2MB")
    try:
        with tarfile.open(archive) as tar:
            tar.extractall(RESOURCES_DIR, filter="data")
    finally:
        os.remove(archive)
    return path


def lazy(build):
    """Run `build` once, caching the result; False if it raises.

    Every table here is optional: the node degrades to passing the
    prompt through rather than failing the workflow, so callers test the
    result for truth instead of catching.
    """
    cached = []

    def get(*args):
        if not cached:
            try:
                cached.append(build(*args))
            except Exception as e:
                logger.warning("[%s] unavailable: %s", build.__name__, e)
                cached.append(False)
        return cached[0]

    get.__name__ = build.__name__
    get.__doc__ = build.__doc__
    return get


def ensure(path, url, sha256, label, note=""):
    """Return `path`, downloading and verifying it if it is missing.

    Downloads land on a .part file and are renamed only after the digest
    matches, so an interrupted fetch can never masquerade as the real
    artifact.
    """
    if os.path.exists(path):
        return path

    import hashlib
    import urllib.request

    logger.info("[%s] downloading %s%s from %s"
                % (label, os.path.basename(path), note and " (%s)" % note, url))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    try:
        urllib.request.urlretrieve(url, tmp)
        digest = hashlib.sha256()
        with open(tmp, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != sha256:
            raise RuntimeError(
                "%s checksum mismatch (corrupt or stale download)"
                % os.path.basename(path))
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    logger.info("[%s] %s ready" % (label, os.path.basename(path)))
    return path
