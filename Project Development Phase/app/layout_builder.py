def build_comic_layout(image_paths: list[str], story: list[dict],
                       outline: list[dict]) -> list[dict]:
    """Match generated images with their panel outline and story."""
    layout = []

    story_by_panel = {item["panel"]: item for item in story}
    for idx, (image_path, panel) in enumerate(zip(image_paths, outline), start=1):
        story_item = story_by_panel.get(idx, {})
        layout.append({
            "panel": idx,
            "title": panel.get("title", f"Panel {idx}"),
            "image_path": image_path,
            "image_url": "/" + image_path.replace("\\", "/"),
            "scene_description": panel.get("scene_description", ""),
            "image_prompt": panel.get("image_prompt", ""),
            "caption": story_item.get("caption", ""),
            "narration": story_item.get("narration", ""),
            "dialogue": story_item.get("dialogue", []),
        })

    return layout
