"""Custom nodes mappings."""

from .nodes.tags import (
    TagsExtractor,
    TagsGenerator,
    TagsConflictFilter,
    ClassifyTags,
    GroupTags,
)


NODE_CLASS_MAPPINGS = {
    # GeneratorPack/Tags #############################################################
    "TagsExtractor": TagsExtractor,
    "TagsGenerator": TagsGenerator,
    "TagsConflictFilter": TagsConflictFilter,
    "ClassifyTags": ClassifyTags,
    "GroupTags": GroupTags,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    # GeneratorPack/Tags #############################################################
    "TagsExtractor": "Tags Extractor",
    "TagsGenerator": "Tags Generator",
    "TagsConflictFilter": "Tags Conflict Filter",
    "ClassifyTags": "Classify Tags",
    "GroupTags": "Group Tags",
}


# TagsGenerator draws each category toggle and its share on one row; see
# web/js/tags_generator_categories.js
WEB_DIRECTORY = "./web/js"
