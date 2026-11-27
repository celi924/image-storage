import bpy, os, json
from mathutils import Vector

os.makedirs("subdivision_comparison", exist_ok=True)
bpy.ops.wm.obj_import(filepath=os.path.abspath("femalecustom.obj"))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and len(o.data.vertices)]
body=meshes[0]
for o in meshes[1:]:
    bpy.context.view_layer.objects.active=body
    o.select_set(True); body.select_set(True); bpy.ops.object.join()
body=bpy.context.object
body.name="G2F_FullBody_Reference"

def duplicate(name):
    obj=body.copy()
    obj.data=body.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.name=name
    return obj

def weld(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.object.mode_set(mode="OBJECT")

def mesh_stats(obj):
    return {"vertices":len(obj.data.vertices),"edges":len(obj.data.edges),"faces":len(obj.data.polygons)}

# Interpretation A: Subdivision Surface level 3, applied on a duplicate.
a=duplicate("TEST_SubdivisionSurface_Level3")
weld(a)
mod=a.modifiers.new("Tutorial_interpretation_Subdivision_Level_3","SUBSURF")
mod.subdivision_type="CATMULL_CLARK"
mod.levels=3
mod.render_levels=3
bpy.context.view_layer.objects.active=a
bpy.ops.object.modifier_apply(modifier=mod.name)

# Interpretation B: Edit-mode Subdivide with number_cuts=3, on another duplicate.
b=duplicate("TEST_EditMode_Subdivide_NumberCuts3")
weld(b)
bpy.ops.object.select_all(action="DESELECT")
b.select_set(True); bpy.context.view_layer.objects.active=b
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.subdivide(number_cuts=3,smoothness=0.0)
bpy.ops.object.mode_set(mode="OBJECT")

# Keep all variants and the original intact in a comparison blend.
report={
 "blender":bpy.app.version_string,
 "source":mesh_stats(body),
 "interpretation_A_subdivision_surface_level_3":mesh_stats(a),
 "interpretation_B_edit_mode_number_cuts_3":mesh_stats(b),
 "notes":"Diagnostic comparison only. No mask, extraction, smoothing, remesh, shrinkwrap, or source deletion performed."
}
with open("subdivision_comparison/report.json","w") as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath("subdivision_comparison/Subdivision_Method_Comparison.blend"))
print("SUBDIVISION_COMPARISON",json.dumps(report))
