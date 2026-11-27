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
# Weld only coincident vertices across material boundaries; tolerance 0.02mm.
verts_before_weld=len(bm.verts)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00002)
welded_count=verts_before_weld-len(bm.verts)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
# Close only tiny boundary loops at the toe tips (z < 30mm); preserve ankle/waist openings.
boundary_edge_map={}
for e in bm.edges:
    if len(e.link_faces)==1:
        for v in e.verts: boundary_edge_map.setdefault(v,[]).append(e)
seen_boundary=set(); toe_cap_edges=[]
for start in list(boundary_edge_map):
    if start in seen_boundary: continue
    stack=[start]; seen_boundary.add(start); group_verts=set(); group_edges=set()
    while stack:
        v=stack.pop(); group_verts.add(v)
        for e in boundary_edge_map.get(v,[]):
            group_edges.add(e)
            other=e.other_vert(v)
            if other not in seen_boundary:
                seen_boundary.add(other); stack.append(other)
    if len(group_verts)<=20 and max(v.co.z for v in group_verts)<0.03:
        toe_cap_edges.extend(list(group_edges))
toe_cap_edges=list(set(toe_cap_edges))
toe_cap_faces=0
if toe_cap_edges:
    result=bmesh.ops.holes_fill(bm,edges=toe_cap_edges,sides=0)
    toe_cap_faces=len(result.get("faces",[]))
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
# Topology audit: boundary edges are expected only at garment openings; internal seams are not.
edge_face_counts = [0] * len(mesh.edges)
for loop in mesh.loops:
    edge_face_counts[loop.edge_index] += 1
boundary_edges = sum(1 for n in edge_face_counts if n == 1)
nonmanifold_edges = sum(1 for n in edge_face_counts if n != 2)
adj = [[] for _ in mesh.vertices]
for e in mesh.edges:
    a,b = e.vertices
    adj[a].append(b); adj[b].append(a)
seen=set(); components=[]; component_id=[-1]*len(adj)
for start in range(len(adj)):
    if start in seen or not adj[start]: continue
    stack=[start]; seen.add(start); count=0; members=[]; cid=len(components)
    while stack:
        v=stack.pop(); count+=1; members.append(v); component_id[v]=cid
        for n in adj[v]:
            if n not in seen: seen.add(n); stack.append(n)
    components.append(members)
component_reports=[]
for cid,members in enumerate(components):
    coords=[mesh.vertices[i].co for i in members]
    mins=[min(v[k] for v in coords) for k in range(3)]
    maxs=[max(v[k] for v in coords) for k in range(3)]
    component_reports.append((cid,len(members),mins,maxs))
boundary_mids=[]; overfull=[]
for ei,e in enumerate(mesh.edges):
    n=edge_face_counts[ei]
    a,b=(mesh.vertices[i].co for i in e.vertices)
    if n==1: boundary_mids.append((a+b)*0.5)
    elif n>2: overfull.append((ei,n,tuple(a),tuple(b)))
boundary_bins={}
for p in boundary_mids:
    band=round(float(p.z)//0.05*0.05,2)
    boundary_bins[band]=boundary_bins.get(band,0)+1
from mathutils.kdtree import KDTree
cross_component_nearest=[]
for ca in range(len(components)):
    for cb in range(ca+1,len(components)):
        tree=KDTree(len(components[cb]))
        for idx,vi in enumerate(components[cb]): tree.insert(mesh.vertices[vi].co,idx)
        tree.balance()
        best=(1e9,None,None); within={0.0005:0,0.001:0,0.002:0,0.005:0,0.01:0}
        for va in components[ca]:
            co=mesh.vertices[va].co
            near,idx,dist=tree.find(co)
            if dist<best[0]: best=(dist,va,components[cb][idx])
            for threshold in within:
                if dist<=threshold: within[threshold]+=1
        cross_component_nearest.append((ca,cb,best[0],best[1],best[2],within))
selected_by_material={}
for p in body.data.polygons:
    if p.index in keep:
        mn=names[p.material_index] if p.material_index<len(names) else "<none>"
        selected_by_material[mn]=selected_by_material.get(mn,0)+1
# Report geometry and material selection for audit.
with open("candidate/build_report.txt","w") as f:
    f.write("Prototype only; not a VaM .var.\n")
    f.write("Selected source material names: "+", ".join(names)+"\n")
    f.write(f"Selected source faces: {len(keep)}\n")
    f.write(f"Welded coincident vertices (0.02mm tolerance): {welded_count}\n")
    f.write(f"Shell vertices: {len(mesh.vertices)}\nShell faces: {len(mesh.polygons)}\n")
    f.write(f"Boundary edges (one adjacent face): {boundary_edges}\n")
    f.write(f"Nonmanifold edges (not exactly two adjacent faces): {nonmanifold_edges}\n")
    f.write(f"Connected components: {len(components)}; component vertex counts: {sorted([len(c) for c in components], reverse=True)}\n")
    for cid,count,mins,maxs in component_reports:
        f.write(f"Component {cid}: vertices={count}; bounds XYZ min={mins} max={maxs}\n")
    f.write(f"Boundary edge vertical bands (0.05m): {sorted(boundary_bins.items())}\n")
    f.write(f"Boundary edge midpoint bounds XYZ: min={[min(p[k] for p in boundary_mids) for k in range(3)] if boundary_mids else None} max={[max(p[k] for p in boundary_mids) for k in range(3)] if boundary_mids else None}\n")
    f.write(f"Edges with more than two adjacent faces: {len(overfull)}; samples={overfull[:10]}\n")
    f.write("Nearest cross-component vertex pairs (distance, vertex IDs, counts within thresholds):\n")
    for item in cross_component_nearest: f.write(str(item)+"\n")
    f.write("Selected faces by material: "+", ".join(f"{k}={v}" for k,v in sorted(selected_by_material.items()))+"\n")
    f.write("Selected regions: Hips, Legs, Feet, and lower Torso faces with centroid Z <= 1.18m.\n")
    f.write("Outward offset: 1.5mm; Solidify preview thickness: 0.35mm.\n")
# Boundary-edge connected groups: identify each opening and any accidental local holes.
boundary_adj={}
boundary_edge_records=[]
for ei,e in enumerate(mesh.edges):
    if edge_face_counts[ei] != 1: continue
    a,b=e.vertices
    boundary_adj.setdefault(a,[]).append(b)
    boundary_adj.setdefault(b,[]).append(a)
    boundary_edge_records.append((a,b))
boundary_seen=set(); boundary_groups=[]
for start in boundary_adj:
    if start in boundary_seen: continue
    stack=[start]; boundary_seen.add(start); verts_group=set(); edge_count=0
    while stack:
        v=stack.pop(); verts_group.add(v)
        for n in boundary_adj[v]:
            edge_key=tuple(sorted((v,n)))
            if v<n: edge_count+=1
            if n not in boundary_seen:
                boundary_seen.add(n); stack.append(n)
    coords=[mesh.vertices[v].co for v in verts_group]
    mins=[min(float(v[k]) for v in coords) for k in range(3)]
    maxs=[max(float(v[k]) for v in coords) for k in range(3)]
    perimeter=sum((mesh.vertices[a].co-mesh.vertices[b].co).length for a,b in boundary_edge_records if a in verts_group and b in verts_group)
    boundary_groups.append((len(verts_group),edge_count,round(float(perimeter),5),[round(x,5) for x in mins],[round(x,5) for x in maxs]))
boundary_groups.sort(key=lambda x:(x[4][2],x[0]))
# Append boundary loop clusters to the audit report.
with open("candidate/build_report.txt","a") as f:
    f.write("\\nBoundary connected groups (vertices, edges, perimeter m, XYZ min, XYZ max):\\n")
    for group in boundary_groups: f.write(str(group)+"\\n")

# Render multiple orthographic views of the shell; source body remains untouched.
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.show_specular_highlight=True
scene.render.resolution_percentage=100
camd=bpy.data.cameras.new("InspectionCamera")
cam=bpy.data.objects.new("InspectionCamera",camd)
scene.collection.objects.link(cam)
camd.type='ORTHO'
scene.camera=cam
def render_view(name, direction, target_xyz, ortho, width=1100, height=1500):
    target=Vector(target_xyz)
    cam.location=target+Vector(direction).normalized()*4.0
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Z').to_euler()
    camd.ortho_scale=ortho
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.filepath=os.path.abspath("candidate/"+name+".png")
    bpy.ops.render.render(write_still=True)
render_view("front_preview",(0,-1,0),(0,0,0.91),2.7)
render_view("back_preview",(0,1,0),(0,0,0.91),2.7)
render_view("left_side_preview",(-1,0,0),(0,0,0.91),2.7,900,1500)
render_view("right_side_preview",(1,0,0),(0,0,0.91),2.7,900,1500)
render_view("crotch_closeup",(0,-1,0),(0,0,0.79),0.72,1100,900)
render_view("waist_hip_closeup",(0,-1,0),(0,0,1.10),0.72,1100,900)
print("SHELL_BUILD",len(keep),len(mesh.vertices),len(mesh.polygons))
print("TOPOLOGY_AUDIT\\n"+open("candidate/build_report.txt").read())
