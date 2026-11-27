import bpy
op=bpy.ops.sculpt.paint_mask_extract
props=op.get_rna_type().properties
print("MASK_EXTRACT_OPERATOR", [(p.identifier, getattr(p,"default",None)) for p in props])
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16)
ob=bpy.context.object
ob.name="MaskExtract_API_Test"
attr=ob.data.attributes.get(".sculpt_mask")
if attr is None:
    attr=ob.data.attributes.new(name=".sculpt_mask",type="FLOAT",domain="POINT")
for i,d in enumerate(attr.data):
    co=ob.data.vertices[i].co
    d.value=1.0 if co.z>0.0 else 0.0
bpy.context.view_layer.objects.active=ob
ob.select_set(True)
try:
    bpy.ops.object.mode_set(mode="SCULPT")
    print("OP_POLL",op.poll())
    result=op(mask_threshold=0.5,add_boundary_loop=False,smooth_iterations=0,apply_shrinkwrap=True,add_solidify=False)
    print("OP_RESULT",result)
    print("OBJECTS_AFTER",[(o.name,o.type,len(o.data.vertices) if o.type=="MESH" else 0) for o in bpy.context.scene.objects])
except Exception as e:
    print("OP_ERROR",type(e).__name__,str(e))
    print("OP_POLL_AFTER_ERROR",op.poll())
print("BLENDER_VERSION",bpy.app.version_string)
