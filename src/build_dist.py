import codecs
import shutil
import os

currentdir = os.curdir
import sys
import subprocess
from packaging.version import Version, parse

import grf_farm
from iron_horse_legacy_paths import iron_horse_legacy_paths

# add dir to path so we can do relative import of the Polar Fox python content for integrity checks
sys.path.insert(0, currentdir)

dist_container_path = grf_farm.dist_container_path

chameleon_cache_path = os.path.join(currentdir, grf_farm.chameleon_cache_dir)
if not os.path.exists(chameleon_cache_path):
    os.mkdir(chameleon_cache_path)
os.environ["CHAMELEON_CACHE"] = chameleon_cache_path

from chameleon import PageTemplateLoader

docs_templates = PageTemplateLoader(
    os.path.join(currentdir, "src", "templates"), format="text"
)

def render_grf_index_pages(grf_name, dist_dir_path):
    distributed_docs_versions = [
        dir_name
        for dir_name in os.listdir(dist_dir_path)
        if os.path.isdir(os.path.join(dist_dir_path, dir_name))
    ]

    if grf_name == "iron-horse":
        distributed_docs_versions.extend(iron_horse_legacy_paths)

    # note use of parse from python packaging library, this provides sorting on version numbers which don't sort desirably as strings, and can't be treated as int due to e.g. '-alpha-' versions
    distributed_docs_versions = sorted(
        distributed_docs_versions, key=lambda x: parse(x)
    )
    distributed_docs_versions.reverse()

    print("latest", distributed_docs_versions[0])

    for output_filename, template_filename in [('index.html', 'grf_index_page.pt'), ('latest.html', 'grf_latest_version_redirect.pt')]:
        print("Adding", output_filename, "for", grf_name)
        template = docs_templates[template_filename]
        grf_page_html = template(
            grf_farm=grf_farm,
            grf_name=grf_name,
            distributed_docs_versions=distributed_docs_versions,
        )
        grf_page_file = codecs.open(
            os.path.join(dist_dir_path, output_filename), "w", "utf8"
        )
        grf_page_file.write(grf_page_html)
        grf_page_file.close()


def main():
    print("Preparing files for distribution")
    if not os.path.exists(dist_container_path):
        print("Creating", dist_container_path)
        os.mkdir(dist_container_path)

    for grf_name in grf_farm.registered_grfs:
        dist_dir_path = os.path.join(dist_container_path, grf_name)
        src_dir_path = os.path.join(currentdir, "src", grf_name)
        print("Syncing dirs for", grf_name)
        # rsync is used as it's substantially faster than python copytree, both in the case of copying everything, and even faster if only a partial copy is needed
        subprocess.call(["rsync", "-a", "--delete", src_dir_path, dist_container_path])
        render_grf_index_pages(grf_name, dist_dir_path)

    """
    # copied from Polar Fox, not needed here?
    for filename in ['LICENSE.txt', 'README.txt']:
        shutil.copy(os.path.join(currentdir, filename), os.path.join(dist_package_path, filename))
    """
    print("[DONE]")


if __name__ == "__main__":
    main()
