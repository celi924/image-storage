import bpy, os, math
from mathutils import Vector

os.makedirs("inspection", exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

bpy.ops.wm.obj_import(filepath=os.path.abspath("femalecustom.obj"))
mesh_objects=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if not mesh_objects:
    raise RuntimeError("OBJ import produced no mesh objects")

# Preserve imported geometry/material assignments; join only for a stable full-body render.
bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objects: o.select_set(True)
bpy.context.view_layer.objects.active=mesh_objects[0]
bpy.ops.object.join()
body=bpy.context.object
body.name="Genesis2_Custom_Body_Inspection"

# Center and frame the model from actual bounds.
corners=[body.matrix_world @ Vector(c) for c in body.bound_box]
mins=Vector((min(v.x for v in corners),min(v.y for v in corners),min(v.z for v in corners)))
maxs=Vector((max(v.x for v in corners),max(v.y for v in corners),max(v.z for v in corners)))
center=(mins+maxs)*0.5
height=maxs.y-mins.y
# OBJ Y is vertical. Front/back are +/- Z.
def aim(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.render.resolution_x=1100
scene.render.resolution_y=1500
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.color=(0.055,0.055,0.055)
# Neutral studio material override is intentionally avoided so imported material regions remain visible.
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=height*2.4

def render_view(label, direction):
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active=body
    cam_data=bpy.data.cameras.new("InspectionCamera")
    cam=bpy.data.objects.new("InspectionCamera",cam_data)
    scene.collection.objects.link(cam)
    cam.location=center+Vector(direction)*height*2.5
    aim(cam,center)
    cam_data.type='ORTHO'
    cam_data.ortho_scale=height*(scene.render.resolution_x/scene.render.resolution_y)*1.12
    scene.camera=cam
    scene.render.filepath=os.path.abspath("inspection/"+label+".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)

render_view("front",(0,0,1))
render_view("back",(0,0,-1))
render_view("side",(1,0,0))
print("BODY_BOUNDS",tuple(mins),tuple(maxs),"HEIGHT",height,"MESH_OBJECTS",len(mesh_objects))
