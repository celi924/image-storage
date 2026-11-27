import bpy, os, bmesh
from mathutils import Vector
os.makedirs("candidate",exist_ok=True)
bpy.ops.wm.obj_import(filepath=os.path.abspath("femalecustom.obj"))
objs=[o for o in bpy.context.scene.objects if o.type=="MESH" and len(o.data.vertices)]
body=objs[0]
for o in objs[1:]:
    bpy.context.view_layer.objects.active=body
    o.select_set(True); body.select_set(True)
    bpy.ops.object.join()
body=bpy.context.object
body.name="Genesis2_Body_Source"
# Material-name selection: keep pelvic/leg/foot regions, plus lower torso to form a continuous waist rise.
names=[m.name.lower() if m else "" for m in body.data.materials]
keep=set()
for p in body.data.polygons:
    mat=names[p.material_index] if p.material_index<len(names) else ""
    z=sum(body.data.vertices[i].co.z for i in p.vertices)/len(p.vertices)
    if any(k in mat for k in ("hips","legs","feet")):
        keep.add(p.index)
    elif "torso" in mat and z <= 1.18:
        keep.add(p.index)
if not keep:
    raise RuntimeError("No garment source faces selected; material names: "+repr(names))
# Build a separate surface from the selected body polygons, leaving source mesh untouched.
bm=bmesh.new()
bm.from_mesh(body.data)
faces=list(bm.faces)
for f in faces:
    if f.index not in keep:
        bm.faces.remove(f)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
# Slight outward offset for a first fitting shell; this is a fitting prototype, not a finished garment.
for v in bm.verts:
    if v.normal.length>0:
        v.co += v.normal.normalized()*0.0015
mesh=bpy.data.meshes.new("PlainPantyhoseShell_Mesh")
bm.to_mesh(mesh); bm.free()
shell=bpy.data.objects.new("PlainPantyhoseShell_CANDIDATE",mesh)
bpy.context.collection.objects.link(shell)
# Neutral single-color material for inspection.
mat=bpy.data.materials.new("Plain sheer nylon preview")
mat.diffuse_color=(0.22,0.32,0.52,1.0)
mat.use_nodes=True
bs=mat.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(0.12,0.20,0.38,1)
bs.inputs["Roughness"].default_value=0.38
shell.data.materials.clear(); shell.data.materials.append(mat)
for p in shell.data.polygons: p.material_index=0; p.use_smooth=True
solid=shell.modifiers.new("Thin fabric preview thickness","SOLIDIFY")
solid.thickness=0.00035
solid.offset=0
# Export the independent candidate mesh.
bpy.ops.object.select_all(action='DESELECT')
shell.select_set(True); bpy.context.view_layer.objects.active=shell
bpy.ops.wm.obj_export(filepath=os.path.abspath("candidate/PlainPantyhoseShell_CANDIDATE.obj"),export_selected_objects=True)
# Report geometry and material selection for audit.
with open("candidate/build_report.txt","w") as f:
    f.write("Prototype only; not a VaM .var.\n")
    f.write("Selected source material names: "+", ".join(names)+"\n")
    f.write(f"Selected source faces: {len(keep)}\n")
    f.write(f"Shell vertices: {len(mesh.vertices)}\nShell faces: {len(mesh.polygons)}\n")
    f.write("Selected regions: Hips, Legs, Feet, and lower Torso faces with centroid Z <= 1.18m.\n")
    f.write("Outward offset: 1.5mm; Solidify preview thickness: 0.35mm.\n")
# Render frontal fitting preview, full body frame.
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.render.resolution_x=1100; scene.render.resolution_y=1500; scene.render.resolution_percentage=100
camd=bpy.data.cameras.new("PreviewCamera"); cam=bpy.data.objects.new("PreviewCamera",camd); scene.collection.objects.link(cam)
cam.location=Vector((0,-4,0.91)); target=Vector((0,0,0.91))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Z').to_euler()
camd.type='ORTHO'; camd.ortho_scale=2.7; scene.camera=cam
scene.render.filepath=os.path.abspath("candidate/front_preview.png")
bpy.ops.render.render(write_still=True)
print("SHELL_BUILD",len(keep),len(mesh.vertices),len(mesh.polygons))
