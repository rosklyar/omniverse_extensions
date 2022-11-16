import omni.ext
import carb.events
import omni.kit.app
import omni.ui as ui
import omni.kit.window.filepicker as fp
from pxr import Usd, UsdGeom, Gf
import omni.usd
import os
from os.path import exists
import asyncio
import json
import time

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.

    def on_startup(self, ext_id):
        
        async def export_data():
            stage = omni.usd.get_context().get_stage()
            manager = omni.audio2face.player.get_ext().player_manager()
            instance = manager.get_instance("/World/LazyGraph/Player")
            l_eye = stage.GetPrimAtPath(self.eyesRootPath + "l_eye_grp_hi")
            r_eye = stage.GetPrimAtPath(self.eyesRootPath + "r_eye_grp_hi")
            bs = stage.GetPrimAtPath(self.bsRootPath)
            while True:
                actual_requests = get_actual_requests(self.scanFolder)
                if len(actual_requests) > 0:
                    for request in actual_requests:
                        print("Processing request: " + request)
                        await asyncio.ensure_future(infer_request(request, instance, l_eye, r_eye, bs))
                else:
                    print(f'No new requests... Sleeping {self.sleepTimeInSeconds} seconds...')
                    await asyncio.sleep(self.sleepTimeInSeconds)

        def on_change(event):
            if(event.type == 8):
                asyncio.ensure_future(export_data())
            pass

        async def infer_request(request, instance, l_eye, r_eye, bs):
            request_path = self.scanFolder + "/" + request
            instance.set_track_root_path(request_path)
            fileLengthInSeconds = instance.get_range_end()
            print("fileLengthInSeconds: " + str(fileLengthInSeconds))
            t = 0.0
            result_eyedarts = []
            result_bs = []
            while(t < fileLengthInSeconds):
                e = await omni.kit.app.get_app().next_update_async()
                t += 1.0 / self.fps
                instance.set_time(t)
                pose_l = omni.usd.utils.get_world_transform_matrix(l_eye)
                pose_r = omni.usd.utils.get_world_transform_matrix(r_eye)
                l_rx, l_ry, l_rz = pose_l.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
                r_rx, r_ry, r_rz = pose_r.ExtractRotation().Decompose(Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis())
                bs_frame = [x for x in bs.GetAttribute(self.bsParamsAttrName).Get()]
                frame = [l_rx, l_ry, l_rz, r_rx, r_ry, r_rz]
                result_eyedarts.append(frame)
                result_bs.append(bs_frame)

            result_eyedarts_json = {
                "numPoses": 6,
                "numFrames": len(result_eyedarts),
                "facsNames" : ["l_rx", "l_ry", "l_rz", "r_rx", "r_ry", "r_rz"],
                "weightMat": result_eyedarts
            }

            result_bs_json = {
                "numPoses": 51,
                "numFrames": len(result_bs),
                "facsNames" : BS_NAMES,
                "weightMat": result_bs
            }

            with open(request_path + "/eye_darts.json", 'w') as outfile:
                json.dump(result_eyedarts_json, outfile)
            with open(request_path + "/lipsync.json", 'w') as outfile:
                json.dump(result_bs_json, outfile)

            with open(request_path + "/request.json") as jsonFile:
                state = json.load(jsonFile)
            state["status"] = "inferred"
            print("State:" + str(state))
            with open(request_path + "/request.json", 'w') as jsonFile:
                json.dump(state, jsonFile)

            print("Processed: " + str(request))
            return result_eyedarts

        print("[playtika.eyedarts.export] ExportEyeDarts Techathon startup")
        self.fps = 60
        self.sleepTimeInSeconds = 10
        self.scanFolder = "C:/Users/rskliar/animations/requests"
        self.eyesRootPath = "/World/male_fullface/char_male_model_hi/"
        self.bsRootPath = "/World/ARKit_bs_skel/ARKit_bs/joint1/bs_anim"
        self.bsParamsAttrName = "blendShapeWeights"
        print("Stream=" + str(omni.kit.app.get_app().get_message_bus_event_stream()))
        print("Update Stream=" + str(omni.kit.app.get_app().get_update_event_stream()))
        self._subscription = omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(on_change)

    def on_shutdown(self):
        print("[playtika.eyedarts.export] ExportEyeDarts Techathon shutdown")

def get_actual_requests(scan_folder):
    requests = []
    if scan_folder and not exists(scan_folder):
        raise Exception("Please, select existed folder with animation requests!")
    # list of requests
    for request in os.listdir(scan_folder):
        if os.path.isdir(scan_folder + "/" + request):
            request_file = os.path.join(os.path.join(scan_folder, request), "request.json")
            with open(request_file) as json_file:
                status = json.load(json_file)['status']
                if not status or status == "created":
                    requests.append(request)
    return requests

BS_NAMES = ["browDownLeftShape",
        "browDownRightShape",
        "browInnerUpShape",
        "browOuterUpLeftShape",
        "browOuterUpRightShape",
        "cheekPuffShape",
        "cheekSquintLeftShape",
        "cheekSquintRightShape",
        "eyeBlinkLeftShape",
        "eyeBlinkRightShape",
        "eyeLookDownLeftShape",
        "eyeLookDownRightShape",
        "eyeLookInLeftShape",
        "eyeLookInRightShape",
        "eyeLookOutLeftShape",
        "eyeLookOutRightShape",
        "eyeLookUpLeftShape",
        "eyeLookUpRightShape",
        "eyeSquintLeftShape",
        "eyeSquintRightShape",
        "eyeWideLeftShape",
        "eyeWideRightShape",
        "jawForwardShape",
        "jawLeftShape",
        "jawOpenShape",
        "jawRightShape",
        "mouthCloseShape",
        "mouthDimpleLeftShape",
        "mouthDimpleRightShape",
        "mouthFrownLeftShape",
        "mouthFrownRightShape",
        "mouthFunnelShape",
        "mouthLeftShape",
        "mouthLowerDownLeftShape",
        "mouthLowerDownRightShape",
        "mouthPressLeftShape",
        "mouthPressRightShape",
        "mouthPuckerShape",
        "mouthRightShape",
        "mouthRollLowerShape",
        "mouthRollUpperShape",
        "mouthShrugLowerShape",
        "mouthShrugUpperShape",
        "mouthSmileLeftShape",
        "mouthSmileRightShape",
        "mouthStretchLeftShape",
        "mouthStretchRightShape",
        "mouthUpperUpLeftShape",
        "mouthUpperUpRightShape",
        "noseSneerLeftShape",
        "noseSneerRightShape"]
