import bpy, os, math, json
from mathutils import Vector
os.makedirs("candidate_mask_extract",exist_ok=True)
# Import the supplied full Genesis 2 Female OBJ; do not delete any body regions.
bpy.ops.wm.obj_import(filepath=os.path.abspath("femalecustom.obj"))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and len(o.data.vertices)]
body=meshes[0]
for o in meshes[1:]:
    bpy.context.view_layer.objects.active=body
    o.select_set(True); body.select_set(True); bpy.ops.object.join()
body=bpy.context.object
body.name="G2F_FullBody_Reference"
# Remove only exact duplicate polygons created by OBJ material-boundary overlap.
# Keep every unique body polygon and every anatomical region intact.
import bmesh
def remove_exact_duplicate_faces(obj):
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    seen={}
    duplicates=[]
    for f in bm.faces:
        key=tuple(sorted(v.index for v in f.verts))
        if key in seen:
            duplicates.append(f)
        else:
            seen[key]=f
    if duplicates:
        bmesh.ops.delete(bm,geom=duplicates,context='FACES')
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(duplicates)
duplicate_faces_removed=remove_exact_duplicate_faces(body)
# Preserve source mesh and create a separate dense working copy.
work=body.copy(); work.data=body.data.copy(); bpy.context.collection.objects.link(work)
work.name="Pantyhose_MaskExtract_Work"
bpy.ops.object.select_all(action="DESELECT"); work.select_set(True); bpy.context.view_layer.objects.active=work
# Weld coincident OBJ vertices across material seams before subdivision.
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=0.0001)
# Subdivide once for a more continuous extracted boundary while keeping this test tractable.
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.subdivide(number_cuts=1,smoothness=0.0)
bpy.ops.object.mode_set(mode="OBJECT")
# Build mask from the original anatomical material regions plus a lower-torso waist band.
# This only paints a mask; it never removes body polygons or material groups.
orig_names=[m.name.lower() if m else "" for m in body.data.materials]
# Nearest original face material lookup for subdivided vertices.
from mathutils.bvhtree import BVHTree
deps=bpy.context.evaluated_depsgraph_get()
orig_eval=body.evaluated_get(deps)
bvhtree=BVHTree.FromObject(body,deps)
orig_mesh=body.data
orig_centers=[]
for p in orig_mesh.polygons:
    c=sum((orig_mesh.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    mn=orig_names[p.material_index] if p.material_index<len(orig_names) else ""
    orig_centers.append((c,mn))
# Build material mask by nearest original polygon center; nearest surface point gives face index.
mask=work.data.attributes.get(".sculpt_mask")
if mask is None: mask=work.data.attributes.new(name=".sculpt_mask",type="FLOAT",domain="POINT")
for v in work.data.vertices:
    hit=bvhtree.find_nearest(v.co)
    if hit is None:
        mask.data[v.index].value=0.0; continue
    loc,normal,face_index,distance=hit
    matname=orig_names[orig_mesh.polygons[face_index].material_index] if face_index<len(orig_mesh.polygons) else ""
    z=v.co.z
    # Waist rise: hips and the lower torso are deliberately continuous.
    include=any(k in matname for k in ("hips","legs","feet")) or ("torso" in matname and z<=1.18)
    mask.data[v.index].value=1.0 if include else 0.0
# Extract independent garment surface, preserving the original full body reference.
bpy.ops.object.select_all(action="DESELECT"); work.select_set(True); bpy.context.view_layer.objects.active=work
bpy.ops.object.mode_set(mode="SCULPT")
result=bpy.ops.sculpt.paint_mask_extract(mask_threshold=0.5,add_boundary_loop=True,smooth_iterations=0,apply_shrinkwrap=True,add_solidify=False)
bpy.ops.object.mode_set(mode="OBJECT")
extracted=[o for o in bpy.context.scene.objects if o.type=="MESH" and o!=work and o!=body]
if not extracted: raise RuntimeError("Mask Extract did not create an independent mesh")
garment=extracted[-1]
garment.name="Pantyhose_MaskExtract_Prototype"
# Report topology without applying thickness or deleting any original body geometry.
mesh=garment.data
edge_faces=[0]*len(mesh.edges)
for loop in mesh.loops: edge_faces[loop.edge_index]+=1
boundary=sum(n==1 for n in edge_faces); nonmanifold=sum(n!=2 for n in edge_faces)
adj=[[] for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices; adj[a].append(b); adj[b].append(a)
seen=set(); comps=[]
for i in range(len(adj)):
    if i in seen or not adj[i]: continue
    stack=[i]; seen.add(i); count=0
    while stack:
        v=stack.pop(); count+=1
        for n in adj[v]:
            if n not in seen: seen.add(n); stack.append(n)
    comps.append(count)
# Material preview.
mat=bpy.data.materials.new("Plain sheer nylon neutral preview")
mat.diffuse_color=(0.35,0.42,0.58,1)
garment.data.materials.clear(); garment.data.materials.append(mat)
for p in mesh.polygons: p.use_smooth=True
# Save extracted mesh and native blend for inspection.
bpy.ops.object.select_all(action="DESELECT"); garment.select_set(True); bpy.context.view_layer.objects.active=garment
bpy.ops.wm.obj_export(filepath=os.path.abspath("candidate_mask_extract/Pantyhose_MaskExtract_Prototype.obj"),export_selected_objects=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath("candidate_mask_extract/Pantyhose_MaskExtract_Prototype.blend"))
report={
 "blender":bpy.app.version_string,
 "source_vertices":len(body.data.vertices),"source_faces":len(body.data.polygons),
 "work_vertices_after_subdivide":len(work.data.vertices),
 "extracted_vertices":len(mesh.vertices),"extracted_faces":len(mesh.polygons),
 "boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
 "connected_components":len(comps),"component_vertex_counts":sorted(comps,reverse=True),
 "mask_extract_result":list(result),
 "notes":"Prototype only. Full body source retained. Not a VaM clothing item."
}
open("candidate_mask_extract/report.json","w").write(json.dumps(report,indent=2))
print("MASK_EXTRACT_REPORT",json.dumps(report))
