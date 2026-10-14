"""Keep imported annotation collections under the visible USER_NOTES root."""
import bpy

def restore_user_notes(path,parent):
    if not path.exists():return []
    with bpy.data.libraries.load(str(path),link=False) as (source,target):
        target.collections=[name for name in source.collections if name=='USER_NOTES']
    loaded=[]
    for collection in target.collections:
        if collection:
            # Blender may rename the imported collection USER_NOTES.001. Nest it so
            # view-layer visibility does not accidentally exclude that new name.
            parent.children.link(collection);loaded.append(collection)
    return loaded
